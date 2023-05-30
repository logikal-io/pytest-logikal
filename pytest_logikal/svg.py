from pathlib import Path

import pytest

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError
from pytest_logikal.validator import Validator


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('svg')
    group.addoption('--svg', action='store_true', default=False, help='run svg checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'svg: checks SVG files.')
    if config.option.svg:
        config.pluginmanager.register(SVGPlugin(config=config))


class SVGItem(CachedFileCheckItem):
    plugin: 'SVGPlugin'

    def run(self) -> None:
        content = self.path.read_text(encoding='utf-8')
        errors = self.plugin.validator.errors(content, content_type='image/svg+xml')
        messages = [
            f'{error.first_line}: {error.severity}: {error.message}'
            for error in errors if 'Using the preset for SVG' not in error.message
        ]
        if messages:
            raise ItemRunError('\n'.join(messages))


class SVGPlugin(CachedFileCheckPlugin):
    name = 'svg'
    item = SVGItem

    def __init__(self, config: pytest.Config):
        super().__init__(config=config)
        self.validator = Validator()

    def check_file(self, file_path: Path) -> bool:
        return file_path.suffix == '.svg'
