import json
import re
import subprocess
from typing import List

import pytest
from logikal_utils.project import PYPROJECT

from pytest_logikal.core import ReportInfoType
from pytest_logikal.plugin import Item, ItemRunError, Plugin

ALLOWED_LICENSES = [
    r'^3-Clause BSD License$',
    r'^Apache 2\.0$',
    r'^Apache License 2\.0$',
    r'^Apache License Version 2\.0$',
    r'^Apache License, Version 2\.0$',
    r'^Apache Software License$',
    r'^BSD 3-Clause$',
    r'^BSD License$',
    r'^BSD$',
    r'^BSD-3-Clause$',
    r'^CC0 1.0 Universal \(CC0 1\.0\) Public Domain Dedication$',
    r'^GNU Lesser General Public License v2 \(LGPLv2\)$',
    r'^GNU Lesser General Public License v2 or later \(LGPLv2\+\)$',
    r'^GNU Lesser General Public License v3 \(LGPLv3\)$',
    r'^GNU Library or Lesser General Public License \(LGPL\)$',
    r'^ISC License \(ISCL\)$',
    r'^ISC$',
    r'^MIT License$',
    r'^MIT No Attribution License \(MIT-0\)$',
    r'^MIT$',
    r'^Mozilla Public License 2\.0 \(MPL 2\.0\)$',
    r'^Public Domain$',
    r'^Python Software Foundation License$',
    r'^The MIT License \(MIT\)$',
    r'^The Unlicense \(Unlicense\)$',
]

ALLOWED_PACKAGES = {
    'django-migration-linter': r'^UNKNOWN$',  # license is Apache License 2.0, see [1]
    'djlint': r'^GNU General Public License v3 or later \(GPLv3\+\)$',  # only used as a local tool
    'facebook-business': r'^LICENSE\.txt$',  # only used as a connector
    'facebook_business': r'^LICENSE\.txt$',  # only used as a connector
    'html-tag-names': r'^GNU General Public License v3 or later \(GPLv3\+\)$',  # local tool
    'html-void-elements': r'^GNU General Public License v3 or later \(GPLv3\+\)$',  # local tool
    'pillow': r'^Historical Permission Notice and Disclaimer \(HPND\)$',  # license is BSD-like
    'pkg-resources': r'^UNKNOWN$',  # caused by an Ubuntu bug, see [2]
    'pkg_resources': r'^UNKNOWN$',  # caused by an Ubuntu bug, see [2]
    'pylint': r'^GNU General Public License v2 \(GPLv2\)$',  # only used as a local tool
    'pylint-django': r'^GNU General Public License v2 or later \(GPLv2\+\)$',  # local plugin
    'pylint-plugin-utils': r'^GNU General Public License v2 or later \(GPLv2\+\)$',  # local plugin
}
# [1] https://github.com/3YOURMIND/django-migration-linter/issues/290
# [2] https://bugs.launchpad.net/ubuntu/+source/python-pip/+bug/1635463


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('licenses')
    group.addoption('--licenses', action='store_true', default=False, help='run license checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'licenses: checks licenses.')
    if config.option.licenses:
        config.pluginmanager.register(LicensePlugin(config=config))


class LicenseItem(Item):
    def runtest(self) -> None:
        command = ['pip-licenses', '--format=json', '--with-system', '--with-urls']

        # This subprocess call is secure as it is not using untrusted input
        process = subprocess.run(command, capture_output=True, text=True, check=True)  # nosec
        packages = json.loads(process.stdout)

        pyproject_licenses = PYPROJECT.get('tool', {}).get('licenses', {})
        allowed_licenses = pyproject_licenses.get('allowed_licenses', ALLOWED_LICENSES)
        allowed_packages = pyproject_licenses.get('allowed_packages', ALLOWED_PACKAGES)
        allowed_licenses.extend(pyproject_licenses.get('extend_allowed_licenses', []))
        allowed_packages.update(pyproject_licenses.get('extend_allowed_packages', {}))

        warnings: List[str] = []
        for package in sorted(packages, key=lambda item: (item['License'], item['Name'].lower())):
            name, version, url = package['Name'], package.get('Version'), package.get('URL')
            licenses = [license.strip() for license in package['License'].split(';')]

            allowed_package_license = any(
                re.match(allowed_packages[name], license)
                for license in licenses
            ) if name in allowed_packages else False
            allowed_license = any(
                re.match(allowed_license, license)
                for license in licenses
                for allowed_license in allowed_licenses
            )

            if (not allowed_package_license and not allowed_license):
                url = f' ({url})' if url not in ('UNKNOWN', None) else ''
                warnings.append(f'Warning: {package["License"]}: {name}=={version}{url}')
        if warnings:
            raise ItemRunError('\n'.join(warnings))

    def reportinfo(self) -> ReportInfoType:
        return (self.path, None, f'[{LicensePlugin.name}]')


class LicensePlugin(Plugin):
    name = 'licenses'
    item = LicenseItem
