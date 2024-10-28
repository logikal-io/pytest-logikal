import json
from collections.abc import Callable
from subprocess import CompletedProcess

from logikal_utils.project import PYPROJECT
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.licenses import LicenseItem, LicensePlugin
from pytest_logikal.plugin import ItemRunError


def test_run(plugin_item: Callable[..., LicenseItem], mocker: MockerFixture) -> None:
    mocker.patch.dict(PYPROJECT, {'tool': {'licenses': {
        'allowed_licenses': [r'^MIT License$', r'^Partial License v[0-9]+$'],
        'allowed_packages': {'pylint': r'^GNU General Public License v2 \(GPLv2\)$'},
    }}})
    packages = [
        {'License': 'Other', 'Name': 'other', 'Version': '1.0.0', 'URL': 'https://example.com'},
        {'License': 'GNU General Public License v2 (GPLv2)', 'Name': 'blocked', 'URL': 'UNKNOWN'},
        {'License': 'GNU General Public License v2 (GPLv2)', 'Name': 'pylint'},
        {'License': 'GPLv2', 'Name': 'pylint-django'},
        {'License': 'MIT License', 'Name': 'allowed'},
        {'License': 'Partial License v1', 'Name': 'partial'},
    ]
    result = CompletedProcess(args=[], returncode=0, stdout=json.dumps(packages))
    mocker.patch('pytest_logikal.licenses.subprocess.run', return_value=result)
    item = plugin_item(plugin=LicensePlugin, item=LicenseItem, file_contents='')
    warnings = '\n'.join([
        r'Warning: GNU General Public License v2 \(GPLv2\): blocked==None',
        r'Warning: GPLv2: pylint-django==None',
        r'Warning: Other: other==1.0.0 \(https://example.com\)',
    ])
    with raises(ItemRunError, match=warnings):
        item.runtest()
