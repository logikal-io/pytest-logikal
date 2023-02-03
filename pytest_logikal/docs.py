import subprocess
from pathlib import Path

import pytest

from pytest_logikal.file_checker import FileCheckItem, FileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('docs')
    group.addoption('--docs', action='store_true', default=False, help='run docs checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'docs: tests package docs.')
    if config.option.docs:
        config.pluginmanager.register(DocsPlugin(config=config))


class DocsItem(FileCheckItem):
    def runtest(self) -> None:
        process = subprocess.run(  # nosec: secure, not using untrusted input
            ['docs', '--build', '--clear'], capture_output=True, text=True, check=False,
        )
        if process.returncode:
            raise ItemRunError(process.stderr or process.stdout)


class DocsPlugin(FileCheckPlugin):
    name = 'docs'
    item = DocsItem

    def check_file(self, file_path: Path) -> bool:
        return file_path.relative_to(self.config.invocation_params.dir) == Path('docs/index.rst')
