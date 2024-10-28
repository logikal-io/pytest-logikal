import re
import subprocess

import pytest

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('spell')
    group.addoption('--spell', action='store_true', default=False, help='run codespell')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'spell: tests checking spelling.')
    if config.option.spell:
        config.pluginmanager.register(SpellPlugin(config=config))


class SpellItem(CachedFileCheckItem):
    def run(self) -> None:
        command = [
            'codespell', str(self.path),
            '--enable-colors',
            '--builtin', 'clear,rare,informal,en-GB_to_en-US',
            '--check-filenames',
        ]

        # Note that we are running codespell in a subprocess and process its output instead of
        # importing it due to its license (GPLv2). The subprocess call is secure as it is not using
        # untrusted input.
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode == 2:
            raise ItemRunError(f'Error: {(process.stdout or process.stderr).strip()}')
        if process.returncode:
            filename_regex = re.compile(r'^[^:]+:', re.MULTILINE)
            raise ItemRunError('\n'.join(
                filename_regex.sub('', line) for line in process.stdout.splitlines()
            ))


class SpellPlugin(CachedFileCheckPlugin):
    name = 'spell'
    item = SpellItem
