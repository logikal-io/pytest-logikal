from pathlib import Path
from typing import Callable

from pytest import Pytester, raises

from pytest_logikal.docs import DocsItem, DocsPlugin
from pytest_logikal.plugin import ItemRunError

pytest_plugins = ['pytester']

FILES_DIR = Path(__file__).parent / 'files'


def test_invalid_docs(pytester: Pytester, plugin_item: Callable[..., DocsItem]) -> None:
    item = plugin_item(plugin=DocsPlugin, item=DocsItem, file_contents={
        'pyproject.toml': (FILES_DIR / 'valid_pyproject.toml').read_text(encoding='utf-8'),
        'docs/index.rst': (FILES_DIR / 'invalid.rst').read_text(encoding='utf-8'),
    })
    pytester.run('git', 'init', '.')
    with raises(ItemRunError, match='WARNING: Title underline too short'):
        item.runtest()
