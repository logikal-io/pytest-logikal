from collections.abc import Callable
from shutil import copy

from pytest import Pytester, mark, raises

from pytest_logikal.plugin import Item, ItemRunError
from pytest_logikal.translations import TranslationItem, TranslationPlugin
from tests.pytest_logikal.conftest import FILES_DIR

COMPILED_SUBPATH = 'locale/en_GB/LC_MESSAGES/django.mo'


def test_incomplete(plugin_item: Callable[..., Item]) -> None:
    contents = {'translations/incomplete.po': (FILES_DIR / 'incomplete.po').read_text()}
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match(f'error: Compiled translation file ".*/{COMPILED_SUBPATH}" does not exist')
    error.match('error: Fuzzy catalog')
    error.match('19: error: Fuzzy message')
    error.match('22: error: Missing translation')
    error.match('26: error: Fuzzy message')
    error.match('26: error: Missing translation')
    error.match('31: error: Missing translation')
    error.match('36: error: Missing translation')
    error.match('41: error: Missing translation')


def test_missing_language(plugin_item: Callable[..., Item]) -> None:
    file_name = 'missing_language.po'
    contents = {f'translations/{file_name}': (FILES_DIR / file_name).read_text()}
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    with raises(ItemRunError, match='error: Missing "Language" header'):
        item.runtest()


def test_complete(plugin_item: Callable[..., Item], pytester: Pytester) -> None:
    contents = {'translations/complete.po': (FILES_DIR / 'complete.po').read_text()}
    compiled_path = pytester.path / COMPILED_SUBPATH
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    copy(FILES_DIR / 'complete.mo', compiled_path)
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    item.runtest()  # does not raise an error


@mark.parametrize('changed', ['header', 'message'])
def test_outdated(changed: str, plugin_item: Callable[..., Item], pytester: Pytester) -> None:
    contents = {'translations/outdated.po': (FILES_DIR / 'outdated.po').read_text()}
    compiled_path = pytester.path / COMPILED_SUBPATH
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    copy(FILES_DIR / f'outdated_{changed}.mo', compiled_path)
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    with raises(ItemRunError) as error:
        item.runtest()
    error.match(f'error: Compiled translation file ".*/{COMPILED_SUBPATH}" is outdated')


def test_skipped(plugin_item: Callable[..., Item]) -> None:
    contents = {'translations/skipped.po': (FILES_DIR / 'skipped.po').read_text()}
    item = plugin_item(plugin=TranslationPlugin, item=TranslationItem, file_contents=contents)
    item.runtest()  # does not raise an error
