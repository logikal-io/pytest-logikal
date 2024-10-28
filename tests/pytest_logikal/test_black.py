from collections.abc import Callable

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.black import BlackItem, BlackPlugin, pytest_configure
from pytest_logikal.plugin import Item, ItemRunError


def test_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(plugin=BlackPlugin, item=BlackItem, file_contents="""
        x = [
            1, 2,
        ]
    """)
    difference = r'x = \[\n.*-\s+1, 2,.*\n.*\+\s+1,.*\n.*\+\s+2,.*\n\s+\]'
    with raises(ItemRunError, match=difference):
        item.runtest()


def test_parse_error(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(plugin=BlackPlugin, item=BlackItem, file_contents='Syntax error')
    with raises(ItemRunError, match='error: .* Cannot parse'):
        item.runtest()


def test_register(mocker: MockerFixture) -> None:
    config = mocker.Mock()
    config.black = True
    pytest_configure(config)
    assert config.pluginmanager.register.called
