import json
import subprocess
from pathlib import Path

import pytest

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError
from pytest_logikal.utils import get_ini_option, render_template
from pytest_logikal.validator import Validator


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('css')
    group.addoption('--css', action='store_true', default=False, help='run css checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'css: checks CSS files.')
    if config.option.css:
        config.pluginmanager.register(CSSPlugin(config=config))


class CSSItem(CachedFileCheckItem):
    plugin: 'CSSPlugin'

    def run(self) -> None:
        # Validate
        content = self.path.read_text(encoding='utf-8')
        errors = self.plugin.validator.errors(content, content_type='text/css')
        messages = [
            f'{error.first_line}: validation {error.severity}: {error.message}'
            for error in errors
        ]

        # Lint
        # Note: we cannot specify max_line_length via CLI arguments currently
        # (see https://github.com/stylelint/stylelint/issues/6805)
        context = {'max_line_length': get_ini_option('max_line_length')}
        with render_template(Path(__file__).parent / 'css_config.yml', context) as config_path:
            command = [
                'npx', '--no',
                'stylelint', str(self.path), '--formatter', 'json',
                '--config', str(config_path),
            ]
            process = subprocess.run(  # nosec
                command, capture_output=True, text=True, check=False, cwd=Path(__file__).parent,
            )
        try:
            report = json.loads(process.stdout)[0]
            if report['errored']:
                messages.extend(
                    f'{error["line"]}:{error["column"]}: {error["severity"]}: {error["text"]}'
                    for error in report['warnings']
                )
        except json.decoder.JSONDecodeError:
            messages.append(process.stdout or process.stderr)

        # Report errors
        if messages:
            raise ItemRunError('\n'.join(messages))


class CSSPlugin(CachedFileCheckPlugin):
    name = 'css'
    item = CSSItem

    def __init__(self, config: pytest.Config):
        super().__init__(config=config)
        self.validator = Validator()

    def check_file(self, file_path: Path) -> bool:
        return file_path.suffix == '.css'
