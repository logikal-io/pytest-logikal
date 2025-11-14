from collections.abc import Callable

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.js import JSItem, JSPlugin
from pytest_logikal.plugin import Item, ItemRunError
from tests.pytest_logikal.conftest import FILES_DIR


def test_run_invalid(plugin_item: Callable[..., Item]) -> None:
    contents = {'invalid.js': (FILES_DIR / 'invalid.js').read_text()}
    item = plugin_item(plugin=JSPlugin, item=JSItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match(r'Missing semicolon.*\(@stylistic/semi\)')
    error.match(r'Expected indentation.*\(@stylistic/indent\)')
    error.match(r'Expected multiple line comments.*\(multiline-comment-style\)')
    error.match(r'This line has a length of.*\(max-len\)')
    error.match(r'Strings must use singlequote.*\(@stylistic/quotes\)')
    error.match(r'Expected no linebreak.*\(@stylistic/nonblock-statement-body-position\)')


def test_run_valid(plugin_item: Callable[..., Item]) -> None:
    contents = {'valid.js': (FILES_DIR / 'valid.js').read_text()}
    item = plugin_item(plugin=JSPlugin, item=JSItem, file_contents=contents)
    item.runtest()  # does not raise an ItemRunError


def test_error(mocker: MockerFixture, plugin_item: Callable[..., Item]) -> None:
    run = mocker.patch('pytest_logikal.js.subprocess.run')
    run.return_value.stdout = 'error'
    item = plugin_item(plugin=JSPlugin, item=JSItem)
    with raises(ItemRunError, match='error'):
        item.runtest()
