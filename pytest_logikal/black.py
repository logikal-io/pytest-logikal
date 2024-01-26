import re
import subprocess

import black
import pytest
from logikal_utils.project import PYPROJECT

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def get_mode(max_line_length: int) -> black.Mode:
    config = PYPROJECT.get('tool', {}).get('black', {})
    return black.Mode(
        line_length=config.get('line-length', max_line_length),
        string_normalization=not config.get('skip-string-normalization', True),
        preview=config.get('preview', True),
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('black')
    group.addoption('--black', action='store_true', default=False, help='run black')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'black: tests checking code formatting.')
    if config.option.black:
        config.pluginmanager.register(BlackPlugin(config=config))


class BlackItem(CachedFileCheckItem):
    def run(self) -> None:
        mode = get_mode(max_line_length=int(self.config.getini('max_line_length')))
        command = [
            'black', '--check', '--diff', '--color', '--quiet', str(self.path),
            '--line-length', str(mode.line_length),
        ]
        if not mode.string_normalization:
            command += ['--skip-string-normalization']
        if mode.preview:
            command += ['--preview']

        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode:
            message = re.sub(r'^.*\n.*\n([^@]*)@@', r'\1@@', process.stdout) or process.stderr
            raise ItemRunError(message.lstrip('\n').rstrip())


class BlackPlugin(CachedFileCheckPlugin):
    name = 'black'
    item = BlackItem
