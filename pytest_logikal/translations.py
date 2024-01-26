from itertools import permutations
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pytest
from babel.messages import Catalog, Message, mofile, pofile

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('translations')
    group.addoption('--translations', action='store_true', default=False,
                    help='run django translation checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'translations: checks Django translation files.')
    if config.option.translations:
        config.pluginmanager.register(TranslationPlugin(config=config))


def _get_message_context(message: Message) -> Optional[Union[str, bytes]]:
    if isinstance(message.context, bytes):
        return message.context.decode('utf-8')  # type: ignore[unreachable]
    if isinstance(message.context, str):
        return message.context.encode()
    return message.context


def _get_message_string(message: Message) -> Union[str, Tuple[str]]:
    if isinstance(message.string, list):
        return tuple(message.string)
    return message.string  # type: ignore[return-value]


def _message_in_catalog(message: Message, catalog: Catalog) -> bool:
    catalog_message = catalog.get(
        id=message.id,
        context=_get_message_context(message),  # type: ignore[arg-type]
    )
    return (
        catalog_message is not None
        and _get_message_string(message) == _get_message_string(catalog_message)
        and message.flags == catalog_message.flags
    )


def _catalogs_identical(catalog: Catalog, compiled_catalog: Catalog) -> bool:
    if dict(catalog.mime_headers) != dict(compiled_catalog.mime_headers):
        return False
    for catalog_1, catalog_2 in permutations([catalog, compiled_catalog]):
        for message in catalog_1:
            if not message.id:
                continue
            if not _message_in_catalog(message, catalog_2):
                return False
    return True


class TranslationItem(CachedFileCheckItem):
    plugin: 'TranslationPlugin'

    def run(self) -> None:
        errors: List[str] = []

        with open(self.path, encoding='utf-8') as catalog_file:
            catalog = pofile.read_po(catalog_file, abort_invalid=True)

        # Check compiled translation file
        compiled_path = self.path.with_suffix('.mo')
        if compiled_path.exists():
            with open(compiled_path, mode='rb') as compiled_catalog_file:
                compiled_catalog = mofile.read_mo(compiled_catalog_file)
            if not _catalogs_identical(catalog, compiled_catalog):
                errors.append(f'error: Compiled translation file "{compiled_path}" is outdated')
        else:
            errors.append(f'error: Compiled translation file "{compiled_path}" does not exist')

        # Check catalog fuzziness
        if catalog.fuzzy:
            errors.append('error: Fuzzy catalog')

        # Check messages
        for message in catalog:
            # Check fuzziness
            if message.fuzzy and message.lineno:  # we skip the catalog fuzzy marker
                errors.append(f'{message.lineno}: error: Fuzzy message')

            # Check missing translation
            messages = message.string if isinstance(message.string, tuple) else [message.string]
            if any(not string for string in messages):
                errors.append(f'{message.lineno}: error: Missing translation')

        # Report errors
        if errors:
            raise ItemRunError('\n'.join(errors))


class TranslationPlugin(CachedFileCheckPlugin):
    name = 'translations'
    item = TranslationItem

    def check_file(self, file_path: Path) -> bool:
        return file_path.suffix == '.po'
