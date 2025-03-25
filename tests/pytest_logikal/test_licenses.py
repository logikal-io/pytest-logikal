import re
from collections.abc import Callable
from typing import Any

from logikal_utils.project import PYPROJECT
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.licenses import LicenseItem, LicensePlugin
from pytest_logikal.plugin import ItemRunError


class Metadata:
    def __init__(self, **kwargs: Any):
        self._metadata = kwargs

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._metadata.get(key.replace('-', '_'), default)

    def get_all(self, key: str, default: Any | None = None) -> Any:
        return self.get(key=key, default=default)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)


class Package:
    def __init__(self, **kwargs: Any):
        self.metadata = Metadata(**kwargs)


def test_run(plugin_item: Callable[..., LicenseItem], mocker: MockerFixture) -> None:
    mocker.patch.dict(PYPROJECT, {'tool': {'licenses': {
        'allowed_licenses': ['Apache-2.0', 'MIT'],
        'allowed_packages': {
            'allowed-package': 'Unlicense',
            'blocked-package': 'Unlicense',
        },
        'allowed_legacy_licenses': ['Apache License 2.0', 'MIT License'],
        'allowed_legacy_packages': {
            'allowed-legacy-package': 'Unlicense',
            'blocked-legacy-package': 'Unlicense',
        },
    }}})
    url = 'https://example.com'
    urls = [f'Homepage, {url}']
    packages = mocker.patch('pytest_logikal.licenses.importlib.metadata.distributions')
    packages.return_value = [
        # SPDX license definition
        Package(name='allowed', version='1.0', license_expression='MIT'),
        Package(name='allowed-complex', version='1.0', license_expression='Unlicense OR MIT'),
        Package(name='allowed-package', version='1.0', license_expression='Unlicense'),
        Package(name='blocked', version='1.0', license_expression='Unlicense', project_url=urls),
        Package(name='blocked-package', version='1.0', license_expression='GPL-3.0'),
        Package(name='blocked-complex-package', version='1.0',
                license_expression='GPL-2.0 OR GPL-3.0', project_url=urls),
        # Legacy license definition
        Package(name='allowed-legacy', version='1.0', classifier=[
            'License :: OSI Approved',
            'License :: OSI Approved :: MIT License',
        ]),
        Package(name='allowed-legacy-package', version='1.0', license='Unlicense'),
        Package(name='blocked-legacy', version='1.0', license='Unlicense', project_url=urls),
        Package(name='blocked-legacy-package', version='1.0', home_page=url),
    ]
    item = plugin_item(plugin=LicensePlugin, item=LicenseItem, file_contents='')
    warnings = '\n'.join([
        fr'Warning: Unlicense: blocked==1.0 ({url})',
        r'Warning: GPL-3.0: blocked-package==1.0 (https://pypi.org/project/blocked-package/)',
        fr'Warning: GPL-2.0 OR GPL-3.0: blocked-complex-package==1.0 ({url})',
        fr'Warning: Unlicense (legacy license definition): blocked-legacy==1.0 ({url})',
        fr'Warning: UNKNOWN (legacy license definition): blocked-legacy-package==1.0 ({url})',
    ])
    with raises(ItemRunError, match=re.escape(warnings)):
        item.runtest()
