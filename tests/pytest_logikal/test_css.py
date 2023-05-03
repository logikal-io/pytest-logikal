from typing import Callable

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.css import CSSItem, CSSPlugin
from pytest_logikal.plugin import Item, ItemRunError
from tests.pytest_logikal.conftest import FILES_DIR


def test_run(plugin_item: Callable[..., Item]) -> None:
    contents = {'invalid.css': (FILES_DIR / 'invalid.css').read_text()}
    item = plugin_item(plugin=CSSPlugin, item=CSSItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match('validation error: “unknown-property”')
    error.match('unknown type selector "unknown"')
    error.match('unknown property "unknown-property"')
    error.match('Expected indentation')
    error.match('Expected a trailing semicolon')


def test_error(mocker: MockerFixture, plugin_item: Callable[..., Item]) -> None:
    run = mocker.patch('pytest_logikal.css.subprocess.run')
    run.return_value.stdout = 'error'
    item = plugin_item(plugin=CSSPlugin, item=CSSItem)
    with raises(ItemRunError, match='error'):
        item.runtest()
