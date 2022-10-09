import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, List

import pytest

from pytest_logikal.core import PYPROJECT, ReportInfoType
from pytest_logikal.plugin import Item, ItemRunError, Plugin

ALLOWED_LICENSES = [
    '3-Clause BSD License',
    'Apache 2.0',
    'Apache Software License',
    'BSD',
    'BSD-3-Clause',
    'BSD 3-Clause',
    'BSD License',
    'GNU Lesser General Public License v2 (LGPLv2)',
    'ISC License (ISCL)',
    'MIT',
    'MIT License',
    'Mozilla Public License 2.0 (MPL 2.0)',
    'Public Domain',
    'Python Software Foundation License',
    'The MIT License (MIT)',
]

ALLOWED_PACKAGES = {
    'facebook-business': 'LICENSE.txt',  # only used as a connector
    'pkg-resources': 'UNKNOWN',  # caused by an Ubuntu bug, see [1]
    'Pillow': 'Historical Permission Notice and Disclaimer (HPND)',  # license is BSD-like
    'pylint': 'GNU General Public License v2 (GPLv2)',  # only used as a local tool
    'pylint-django': 'GPLv2',  # only used as a local tool plugin
    'pylint-plugin-utils': 'GPLv2',  # only used as a local tool plugin
    'python-lsp-jsonrpc': 'UNKNOWN',  # license is MIT
}
# [1] https://bugs.launchpad.net/ubuntu/+source/python-pip/+bug/1635463


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('licenses')
    group.addoption('--licenses', action='store_true', default=False, help='run license checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'licenses: checks licenses.')
    if config.option.licenses:
        config.pluginmanager.register(LicensePlugin(config=config))


class LicensePlugin(Plugin):
    name = 'licenses'

    @staticmethod
    def pytest_collect_file(file_path: Path, parent: pytest.Collector) -> Any:
        return LicenseFile.from_parent(parent, path=file_path)


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
            allowed_package_license = allowed_packages.get(name) in licenses
            allowed_license = any(license in allowed_licenses for license in licenses)
            if (not allowed_package_license and not allowed_license):
                url = f' ({url})' if url not in ('UNKNOWN', None) else ''
                warnings.append(f'Warning: {package["License"]}: {name}=={version}{url}')
        if warnings:
            raise ItemRunError('\n'.join(warnings))

    def reportinfo(self) -> ReportInfoType:
        return (self.path, None, f'[{LicensePlugin.name}]')


class LicenseFile(pytest.File):
    def collect(self) -> Iterable[LicenseItem]:
        if not any(isinstance(item, LicenseItem) for item in self.session.items):
            yield LicenseItem.from_parent(parent=self, name=LicensePlugin.name)
