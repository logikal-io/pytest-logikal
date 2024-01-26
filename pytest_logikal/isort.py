import re
from io import StringIO
from typing import Any, Dict

import isort
import pytest
from isort.wrap_modes import WrapModes
from logikal_utils.project import PYPROJECT

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def get_config(max_line_length: int, black_compatible: bool = False) -> Dict[str, Any]:
    config = {
        'py_version': 'auto',
        'line_length': max_line_length,
        'multi_line_output': WrapModes.VERTICAL_GRID_GROUPED,  # type: ignore[attr-defined]
        'balanced_wrapping': True,
        'combine_as_imports': True,
        'use_parentheses': True,
        'include_trailing_comma': True,
        'color_output': True,
    }
    if black_compatible:
        config.update({
            # See https://pycqa.github.io/isort/docs/configuration/profiles.html
            # See https://black.readthedocs.io/en/stable/guides/using_black_with_other_tools.html
            'multi_line_output': WrapModes.VERTICAL_HANGING_INDENT,  # type: ignore[attr-defined]
            'ensure_newline_before_comments': True,
            'split_on_trailing_comma': True,
        })
    if 'tool' in PYPROJECT and 'isort' in PYPROJECT['tool']:
        for option in config:
            if option in PYPROJECT['tool']['isort']:
                config[option] = PYPROJECT['tool']['isort'][option]
    return config


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('isort')
    group.addoption('--isort', action='store_true', default=False, help='run isort')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'isort: tests checking import ordering.')
    if config.option.isort:
        config.pluginmanager.register(IsortPlugin(config=config))


class IsortItem(CachedFileCheckItem):
    def run(self) -> None:
        config = get_config(
            max_line_length=int(self.config.getini('max_line_length')),
            black_compatible=getattr(self.config.option, 'black', False),
        )
        stdout = StringIO()
        if not isort.check_file(filename=str(self.path), show_diff=stdout, **config):
            diff = stdout.getvalue()
            message = re.sub('^([+]{3}|[-]{3}|[@]{2}) .*\n', '', diff, flags=re.MULTILINE)
            raise ItemRunError(message.lstrip('\n').rstrip())


class IsortPlugin(CachedFileCheckPlugin):
    name = 'isort'
    item = IsortItem
