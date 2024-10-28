from collections.abc import Callable

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.plugin import Item, ItemRunError
from pytest_logikal.spell import SpellItem, SpellPlugin


def test_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(
        plugin=SpellPlugin,
        item=SpellItem,
        file_contents="univrsal = 'value'",  # codespell:ignore univrsal
    )
    error = r'\x1b\[33m1\x1b\[0m: \x1b\[31munivrsal\x1b\[0m ==> \x1b\[32muniversal\x1b\[0m'
    with raises(ItemRunError, match=error):
        item.runtest()


def test_error(mocker: MockerFixture, plugin_item: Callable[..., Item]) -> None:
    run = mocker.patch('pytest_logikal.spell.subprocess.run')
    run.return_value.returncode = 2
    run.return_value.stdout = 'error'
    item = plugin_item(plugin=SpellPlugin, item=SpellItem)
    with raises(ItemRunError, match='Error: error'):
        item.runtest()
