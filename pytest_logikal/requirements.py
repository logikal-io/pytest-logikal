import re
from pathlib import Path
from typing import Any, Iterable

import pytest
from pyorbs.orbs import Orbs

from pytest_logikal.plugin import Item, ItemRunError, Plugin


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('requirements')
    group.addoption('--requirements', action='store_true', default=False,
                    help='run requirements checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'requirements: checks requirements.')
    if config.option.requirements:
        config.pluginmanager.register(RequirementsPlugin(config=config))


class RequirementsPlugin(Plugin):
    name = 'requirements'

    def pytest_collect_file(self, file_path: Path, parent: pytest.Collector) -> Any:
        relative_file_path = file_path.relative_to(self.config.invocation_params.dir)
        if (
            bool(re.match(r'reqirements\.txt$|requirements/.+\.txt$', str(relative_file_path)))
            and file_path.with_suffix(file_path.suffix + '.lock').exists()
        ):
            return RequirementsFile.from_parent(parent, path=file_path)
        return None


class RequirementsItem(Item):
    def runtest(self) -> None:
        if Orbs.test(str(self.path), quiet=True):
            relative_path = self.path.relative_to(self.config.invocation_params.dir)
            raise ItemRunError(f'Requirements lockfile "{relative_path}.lock" is outdated')


class RequirementsFile(pytest.File):
    def collect(self) -> Iterable[RequirementsItem]:
        yield RequirementsItem.from_parent(parent=self, name=RequirementsPlugin.name)
