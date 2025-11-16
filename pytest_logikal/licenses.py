import importlib
import string

import pytest
from license_expression import Licensing, Renderable, get_spdx_licensing
from logikal_utils.project import tool_config

from pytest_logikal.core import ReportInfoType
from pytest_logikal.plugin import Item, ItemRunError, Plugin

UNKNOWN_LICENSE = 'UNKNOWN'

# See https://spdx.org/licenses/
ALLOWED_LICENSES = [
    'Apache-2.0',
    'BSD-2-Clause',
    'BSD-3-Clause',
    'CC0-1.0',
    'ISC',
    'LGPL-2.0',
    'LGPL-2.0+',
    'LGPL-2.1-or-later',
    'LGPL-3.0',
    'LGPL-3.0+',
    'MIT',
    'MIT-0',
    'MIT-CMU',
    'MPL-2.0',
    'PSF-2.0',
    'Unlicense',
]
ALLOWED_PACKAGES = {
    'pylint': 'GPL-2.0-or-later',  # only used as a local tool
}

ALLOWED_LEGACY_LICENSES = [
    '3-Clause BSD License',
    'Apache 2.0',
    'Apache License 2.0',
    'Apache License Version 2.0',
    'Apache License, Version 2.0',
    'Apache Software License',
    'Apache-2.0 OR BSD-3-Clause',
    'Apache-2.0',
    'BSD 3-Clause',
    'BSD License',
    'BSD',
    'BSD-2-Clause',
    'BSD-3-Clause',
    'BSD 3-Clause OR Apache-2.0',
    'CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
    'CMU License (MIT-CMU)',
    'GNU Lesser General Public License v2 (LGPLv2)',
    'GNU Lesser General Public License v2 or later (LGPLv2+)',
    'GNU Lesser General Public License v3 (LGPLv3)',
    'GNU Library or Lesser General Public License (LGPL)',
    'ISC License (ISCL)',
    'ISC',
    'MIT License',
    'MIT No Attribution License (MIT-0)',
    'MIT',
    'Mozilla Public License 2.0 (MPL 2.0)',
    'Public Domain',
    'Python Software Foundation License',
    'The MIT License (MIT)',
    'The Unlicense (Unlicense)',
    'Unlicense',
]

ALLOWED_LEGACY_PACKAGES = {
    'codespell': 'GPL-2.0-only',  # only used as a local tool
    'djlint': 'GNU General Public License v3 or later (GPLv3+)',  # only used as a local tool
    'facebook-business': 'LICENSE.txt',  # only used as a connector
    'facebook_business': 'LICENSE.txt',  # only used as a connector
    'html-tag-names': 'GNU General Public License v3 or later (GPLv3+)',  # local tool
    'html-void-elements': 'GNU General Public License v3 or later (GPLv3+)',  # local tool
    'pkg-resources': UNKNOWN_LICENSE,  # caused by an Ubuntu bug, see [1]
    'pkg_resources': UNKNOWN_LICENSE,  # caused by an Ubuntu bug, see [1]
    'pylint-django': 'GNU General Public License v2 or later (GPLv2+)',  # local plugin
    'pylint-plugin-utils': 'GNU General Public License v2 or later (GPLv2+)',  # local plugin
    # Packages with invalid license metadata
    'django-migration-linter': UNKNOWN_LICENSE,  # license is Apache License 2.0, see [2]
    'jupyter-sphinx': 'any',  # license is BSD-3-Clause, see [3]
    'matplotlib-inline': UNKNOWN_LICENSE,  # license is BSD-3-Clause, see [4]
    'wrapt': 'any',  # license is BSD-2-Clause, see [5]
}
# [1] https://bugs.launchpad.net/ubuntu/+source/python-pip/+bug/1635463
# [2] https://github.com/3YOURMIND/django-migration-linter/issues/290
# [3] https://github.com/jupyter/jupyter-sphinx/issues/262
# [4] https://github.com/ipython/matplotlib-inline/issues/53
# [5] https://github.com/GrahamDumpleton/wrapt/issues/298


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('licenses')
    group.addoption('--licenses', action='store_true', default=False, help='run license checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'licenses: checks licenses.')
    if config.option.licenses:
        config.pluginmanager.register(LicensePlugin(config=config))


class LicenseItem(Item):
    @staticmethod
    def _normalize_label(label: str) -> str:
        # See https://packaging.python.org/en/latest/specifications/well-known-project-urls
        removal_map = str.maketrans('', '', string.punctuation + string.whitespace)
        return label.strip().translate(removal_map).lower()

    @staticmethod
    def _package_url(package: importlib.metadata.Distribution) -> str | None:
        # Parse project URLs
        urls: dict[str, str] = {}
        for project_url in package.metadata.get_all('project-url', []):
            label, url = project_url.split(',', 1)
            urls[LicenseItem._normalize_label(label)] = url.strip()

        # Check well-known labels
        # See https://packaging.python.org/en/latest/specifications/well-known-project-urls
        well_known_labels = [
            'homepage',
            'documentation', 'docs',
            'source', 'repository', 'sourcecode', 'github',
            'changelog', 'changes', 'whatsnew', 'history',
            'issues', 'bugs', 'issue', 'tracker', 'issuetracker', 'bugtracker',
        ]
        for label in well_known_labels:
            if url := urls.get(label):
                return url

        # Legacy home page URL, deprecated by PEP 753
        if url := package.metadata.get('home-page'):
            return url

        return None

    @staticmethod
    def _legacy_package_licenses(package: importlib.metadata.Distribution) -> list[str]:
        # Legacy licenses read from classifiers, deprecated by PEP 639
        if licenses := [
            classifier.split(' :: ')[-1]
            for classifier in package.metadata.get_all('classifier', [])
            if classifier.startswith('License ::') and classifier != 'License :: OSI Approved'
        ]:
            return licenses

        # Legacy license expression, deprecated by PEP 639
        if license_expression := package.metadata.get('license'):
            return [license_expression.replace('\n', ' ').replace('  ', ' ')]

        return [UNKNOWN_LICENSE]

    @staticmethod
    def _allowed_license(
        expression: str,
        allowed_expressions: list[Renderable],
        licensing: Licensing,
    ) -> bool:
        return any(
            licensing.contains(expression, allowed_expression)
            for allowed_expression in allowed_expressions
        )

    @staticmethod
    def _allowed_legacy_license(licenses: list[str], allowed_licenses: list[str]) -> bool:
        return any(
            allowed_license in (license, 'any')
            for license in licenses
            for allowed_license in allowed_licenses
        )

    def runtest(self) -> None:  # pylint: disable=too-many-locals
        config = tool_config('licenses')
        licensing = get_spdx_licensing()

        # SPDX licenses
        allowed_licenses = config.get('allowed_licenses', ALLOWED_LICENSES)
        allowed_packages = config.get('allowed_packages', ALLOWED_PACKAGES)
        allowed_licenses.extend(config.get('extend_allowed_licenses', []))
        allowed_packages.update(config.get('extend_allowed_packages', {}))

        allowed_license_expressions = [
            licensing.parse(allowed_license)
            for allowed_license in allowed_licenses
        ]
        allowed_package_license_expressions = {
            package: licensing.parse(allowed_license)
            for package, allowed_license in allowed_packages.items()
        }

        # Legacy licenses
        allowed_legacy_licenses = config.get('allowed_legacy_licenses', ALLOWED_LEGACY_LICENSES)
        allowed_legacy_packages = config.get('allowed_legacy_packages', ALLOWED_LEGACY_PACKAGES)
        allowed_legacy_licenses.extend(config.get('extend_allowed_legacy_licenses', []))
        allowed_legacy_packages.update(config.get('extend_allowed_legacy_packages', {}))

        warnings: list[str] = []
        for package in importlib.metadata.distributions():
            name = package.metadata['name']
            version = package.metadata['version']
            url = self._package_url(package) or f'https://pypi.org/project/{name}/'
            allowed_license = False
            allowed_package_license = False

            if license_expression := package.metadata.get('license-expression'):
                # SPDX license check
                parsed_license_expression = licensing.parse(license_expression)
                allowed_license = self._allowed_license(
                    expression=parsed_license_expression,
                    allowed_expressions=allowed_license_expressions,
                    licensing=licensing,
                )
                if package_license_expression := allowed_package_license_expressions.get(name):
                    allowed_package_license = self._allowed_license(
                        expression=parsed_license_expression,
                        allowed_expressions=[package_license_expression],
                        licensing=licensing,
                    )
            else:
                # Legacy license check
                licenses = self._legacy_package_licenses(package)
                license_expression = f'{'; '.join(licenses)} (legacy license definition)'
                allowed_license = self._allowed_legacy_license(
                    licenses=licenses,
                    allowed_licenses=allowed_legacy_licenses,
                )
                if package_license := allowed_legacy_packages.get(name):
                    allowed_package_license = self._allowed_legacy_license(
                        licenses=licenses,
                        allowed_licenses=[package_license],
                    )

            if (not allowed_license and not allowed_package_license):
                warnings.append(f'Warning: {license_expression}: {name}=={version} ({url})')

        if warnings:
            raise ItemRunError('\n'.join(warnings))

    def reportinfo(self) -> ReportInfoType:
        return (self.path, None, f'[{LicensePlugin.name}]')


class LicensePlugin(Plugin):
    name = 'licenses'
    item = LicenseItem
