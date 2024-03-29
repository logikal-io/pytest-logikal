from typing import Callable

from pytest import raises

from pytest_logikal import html
from pytest_logikal.plugin import Item, ItemRunError
from tests.pytest_logikal.conftest import FILES_DIR


def test_htmlj_template_item_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(
        plugin=html.HTMLTemplatePlugin,
        item=html.HTMLTemplateItem,
        file_contents={'invalid.html.j': (FILES_DIR / 'invalid.html.j').read_text()},
    )
    with raises(ItemRunError) as error:
        item.runtest()
    # Note: format checking is disabled
    # error.match('\n\\x1b\\[32m\\+  </html>')  # formatting error
    error.match('10:0: error: Tag seems to be an orphan\\. \\(H025\\)')  # linting error
