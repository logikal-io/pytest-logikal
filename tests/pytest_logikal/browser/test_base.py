import pytest
from pytest_mock import MockerFixture

from pytest_logikal.browser import base


def test_browser_version_print(mocker: MockerFixture, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch(
        'pytest_logikal.browser.base.BrowserVersion._initial_info',
        new_callable=mocker.PropertyMock,
        return_value=False,
    )

    base.BrowserVersion.print('test')
    assert 'Installing browsers' in capsys.readouterr().out

    base.BrowserVersion.final_info()
    assert capsys.readouterr().out == '\n'
