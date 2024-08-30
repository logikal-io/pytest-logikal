import pytest
from pytest_mock import MockerFixture

from pytest_logikal.browser import base


def test_browser_version_print(mocker: MockerFixture, capfd: pytest.CaptureFixture[str]) -> None:
    mocker.patch(
        'pytest_logikal.browser.base.BrowserVersion._initial_info',
        new_callable=mocker.PropertyMock,
        return_value=False,
    )

    base.BrowserVersion.print('test')
    assert 'Installing browsers' in capfd.readouterr().err

    base.BrowserVersion.final_info()
    assert capfd.readouterr().err == '\n'
