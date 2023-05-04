import subprocess
from pathlib import Path

import pytest
from termcolor import colored

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError
from pytest_logikal.utils import get_ini_option


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'html: checks HTML templates.')
    if config.option.html:
        config.pluginmanager.register(HTMLTemplatePlugin(config=config))


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('html')
    group.addoption('--html', action='store_true', default=False, help='run html template checks')


class HTMLTemplateItem(CachedFileCheckItem):
    @staticmethod
    def _color_diff(line: str) -> str:
        if line.startswith('@@'):
            return colored(line, 'cyan', force_color=True)
        if line.startswith('+'):
            return colored(line, 'green', force_color=True)
        if line.startswith('-'):
            return colored(line, 'red', force_color=True)
        return line

    def run(self) -> None:
        messages = []
        max_line_length = str(get_ini_option('max_line_length'))
        common_args = [
            str(self.path),
            '--extension', 'html.j',
            '--indent', '2',
            '--profile', 'jinja',
            '--max-line-length', max_line_length,
            '--max-attribute-length', max_line_length,
            '--linter-output-format', '{line}: error: {message} ({code})',
        ]

        # Check formatting
        command = ['djlint', '--check', '--preserve-blank-lines', *common_args]
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode:
            errors = process.stdout.strip().replace('@@\n\n', '@@\n')
            errors = '\n'.join(self._color_diff(line) for line in errors.splitlines()[2:-2])
            messages.append(errors or process.stderr.strip())

        # Lint
        ignore = [
            'J004', 'J018',  # we have our own functions for Jinja environments
            'T002',  # we always use single quotes
        ]
        command = ['djlint', '--lint', '--ignore', ','.join(ignore), *common_args]
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode:
            errors = process.stdout.strip()
            errors = '\n'.join(errors.splitlines()[2:-2])
            messages.append(errors or process.stderr.strip())

        # Report errors
        if messages:
            separator = colored('Errors:', 'red', attrs=['bold'], force_color=True)
            raise ItemRunError(f'\n\n{separator}\n'.join(messages))


class HTMLTemplatePlugin(CachedFileCheckPlugin):
    name = 'html'
    item = HTMLTemplateItem

    def check_file(self, file_path: Path) -> bool:
        return str(file_path).endswith('.html.j')
