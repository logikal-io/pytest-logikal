import re
from pathlib import Path

import pytest
from pyorbs.orbs import Orbs

from pytest_logikal.file_checker import FileCheckItem, FileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('requirements')
    group.addoption('--requirements', action='store_true', default=False,
                    help='run requirements checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'requirements: checks requirements.')
    if config.option.requirements:
        config.pluginmanager.register(RequirementsPlugin(config=config))


class RequirementsItem(FileCheckItem):
    def runtest(self) -> None:
        if Orbs.test(str(self.path), quiet=True):
            relative_path = self.path.relative_to(self.config.invocation_params.dir)
            raise ItemRunError(f'Requirements lockfile "{relative_path}.lock" is outdated')


class RequirementsPlugin(FileCheckPlugin):
    name = 'requirements'
    item = RequirementsItem

    def check_file(self, file_path: Path) -> bool:
        relative_file_path = file_path.relative_to(self.config.invocation_params.dir)
        return (
            bool(re.match(r'reqirements\.txt$|requirements/.+\.txt$', str(relative_file_path)))
            and file_path.with_suffix(file_path.suffix + '.lock').exists()
        )
