from collections.abc import Callable

from pytest import raises

from pytest_logikal.plugin import Item, ItemRunError
from pytest_logikal.svg import SVGItem, SVGPlugin
from tests.pytest_logikal.conftest import FILES_DIR


def test_run_invalid(plugin_item: Callable[..., Item]) -> None:
    contents = {'invalid.svg': (FILES_DIR / 'invalid.svg').read_text()}
    item = plugin_item(plugin=SVGPlugin, item=SVGItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match('end of file')


def test_run_valid(plugin_item: Callable[..., Item]) -> None:
    contents = {'logikal_logo.svg': (FILES_DIR / 'logikal_logo.svg').read_text()}
    item = plugin_item(plugin=SVGPlugin, item=SVGItem, file_contents=contents)
    item.runtest()  # does not raise an ItemRunError
