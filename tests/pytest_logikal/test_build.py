from pathlib import Path
from typing import Callable

from pytest import raises

from pytest_logikal.build import BuildItem, BuildPlugin
from pytest_logikal.plugin import ItemRunError

FILES_DIR = Path(__file__).parent / 'files'


def test_invalid_pyproject_toml(plugin_item: Callable[..., BuildItem]) -> None:
    item = plugin_item(plugin=BuildPlugin, item=BuildItem, file_contents={
        'pyproject.toml': (FILES_DIR / 'invalid_pyproject.toml').read_text(encoding='utf-8'),
    })
    with raises(ItemRunError, match='Failed to validate `build-system`'):
        item.runtest()


def test_invalid_distribution(plugin_item: Callable[..., BuildItem]) -> None:
    item = plugin_item(plugin=BuildPlugin, item=BuildItem, file_contents={
        'pyproject.toml': (FILES_DIR / 'valid_pyproject.toml').read_text(encoding='utf-8'),
        'README.rst': (FILES_DIR / 'invalid.rst').read_text(encoding='utf-8'),
    })
    with raises(ItemRunError, match='syntax errors in markup'):
        item.runtest()
