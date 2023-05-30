from shutil import copy
from typing import Callable

from pytest import Pytester, raises

from pytest_logikal.plugin import Item, ItemRunError
from pytest_logikal.translations import TranslationItem, TranslationPlugin
from tests.pytest_logikal.conftest import FILES_DIR


def test_incomplete(plugin_item: Callable[..., Item]) -> None:
    contents = {'incomplete.po': (FILES_DIR / 'incomplete.po').read_text()}
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match('error: Compiled translation file ".*/incomplete.mo" does not exist')
    error.match('error: Fuzzy catalog')
    error.match('19: error: Fuzzy message')
    error.match('22: error: Missing translation')
    error.match('26: error: Fuzzy message')
    error.match('26: error: Missing translation')
    error.match('31: error: Missing translation')
    error.match('36: error: Missing translation')
    error.match('41: error: Missing translation')


def test_outdated(plugin_item: Callable[..., Item], pytester: Pytester) -> None:
    contents = {'outdated.po': (FILES_DIR / 'outdated.po').read_text()}
    copy(FILES_DIR / 'outdated.mo', pytester.path / 'outdated.mo')
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match('error: Compiled translation file ".*/outdated.mo" is outdated')
