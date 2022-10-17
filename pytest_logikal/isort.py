import re
from io import StringIO

import isort
import pytest
from isort.wrap_modes import WrapModes

from pytest_logikal.core import PYPROJECT
from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('isort')
    group.addoption('--isort', action='store_true', default=False, help='run isort')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'isort: tests checking import ordering.')
    if config.option.isort:
        config.pluginmanager.register(IsortPlugin(config=config))


class IsortItem(CachedFileCheckItem):
    def run(self) -> None:
        config = {
            'py_version': 'auto',
            'line_length': int(self.config.getini('max_line_length')),
            'multi_line_output': WrapModes.VERTICAL_GRID_GROUPED,  # type: ignore[attr-defined]
            'balanced_wrapping': True,
            'combine_as_imports': True,
            'use_parentheses': True,
            'include_trailing_comma': True,
            'color_output': True,
        }
        if 'tool' in PYPROJECT and 'isort' in PYPROJECT['tool']:
            for option in config:
                if option in PYPROJECT['tool']['isort']:
                    config[option] = PYPROJECT['tool']['isort'][option]

        stdout = StringIO()
        if not isort.check_file(filename=str(self.path), show_diff=stdout, **config):
            diff = stdout.getvalue()
            message = re.sub('^([+]{3}|[-]{3}|[@]{2}) .*\n', '', diff, flags=re.MULTILINE)
            raise ItemRunError(message.lstrip('\n').rstrip())


class IsortPlugin(CachedFileCheckPlugin):
    name = 'isort'
    item = IsortItem
