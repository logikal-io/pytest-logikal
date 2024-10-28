from collections.abc import Callable

from pytest import Pytester, raises

from pytest_logikal.docs import DocsItem, DocsPlugin
from pytest_logikal.plugin import ItemRunError
from tests.pytest_logikal.conftest import FILES_DIR

pytest_plugins = ['pytester']


def test_invalid_docs(pytester: Pytester, plugin_item: Callable[..., DocsItem]) -> None:
    item = plugin_item(plugin=DocsPlugin, item=DocsItem, file_contents={
        'pyproject.toml': (FILES_DIR / 'valid_pyproject.toml').read_text(),
        'docs/index.rst': (FILES_DIR / 'invalid.rst').read_text(),
    })
    pytester.run('git', 'init', '.')
    with raises(ItemRunError, match='WARNING: Title underline too short'):
        item.runtest()
