from typing import Callable

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.plugin import Item, ItemRunError
from pytest_logikal.pylint import PylintItem, PylintPlugin


def test_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(
        plugin=PylintPlugin, item=PylintItem, file_contents="x = 'invalid'",
        set_django_settings_module=False,
    )
    error = (
        '1:0: convention: Constant name "x" doesn\'t conform to UPPER_CASE naming style'
        r' \(.* pattern\) \(invalid-name\)'
    )
    with raises(ItemRunError, match=error):
        item.runtest()


def test_error(mocker: MockerFixture, plugin_item: Callable[..., Item]) -> None:
    run = mocker.patch('pytest_logikal.pylint.subprocess.run')
    run.return_value.stdout = 'error'
    item = plugin_item(plugin=PylintPlugin, item=PylintItem)
    with raises(ItemRunError, match='Error: error'):
        item.runtest()
