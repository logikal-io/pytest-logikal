from typing import Callable

from pytest import raises

from pytest_logikal.plugin import Item, ItemRunError
from pytest_logikal.style import StyleItem, StylePlugin


def test_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(plugin=StylePlugin, item=StyleItem, file_contents="""
        '''Invalid docstring.'''

        def single_blank_line() -> None:
            pass
    """)
    error = (
        r'3:1: error: expected 2 blank lines, found 1 \(E302\)\n'
        r'1: error: Use """triple double quotes""" \(D300\)'
    )
    with raises(ItemRunError, match=error):
        item.runtest()
