from contextlib import redirect_stdout
from io import StringIO

import pycodestyle
import pydocstyle
import pytest
from logikal_utils.project import PYPROJECT

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('style')
    group.addoption('--style', action='store_true', default=False,
                    help='run pycodestyle and pydocstyle')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'style: tests checking code and docstring style.')
    if config.option.style:
        config.pluginmanager.register(StylePlugin(config=config))


class StyleItem(CachedFileCheckItem):
    def run(self) -> None:
        messages = []

        # Run pycodestyle
        if not getattr(self.config.option, 'black', False):
            ignore = ['E133', 'W503']  # mutually exclusive checks with E123 and W504
            max_line_length = int(self.config.getini('max_line_length'))
            with redirect_stdout(StringIO()) as code_stdout:
                code_errors = pycodestyle.Checker(
                    filename=self.path,
                    max_line_length=max_line_length,
                    max_doc_length=max_line_length,
                    format='%(row)s:%(col)s: error: %(text)s (%(code)s)',
                    ignore=PYPROJECT.get('tool', {}).get('pycodestyle', {}).get('ignore', ignore),
                ).check_all()
            if code_errors:
                messages.append(code_stdout.getvalue().rstrip())

        # Run pydocstyle
        select = pydocstyle.violations.all_errors - {
            'D100', 'D101', 'D102', 'D103', 'D104', 'D105', 'D106', 'D107',
            'D200', 'D203', 'D204', 'D212', 'D406', 'D407', 'D408', 'D409',
        }
        select = PYPROJECT.get('tool', {}).get('pydocstyle', {}).get('select', select)
        if doc_errors := list(pydocstyle.check(filenames=[str(self.path)], select=select)):
            messages.extend(
                f'{error.line}: error: {error.short_desc} ({error.code})'
                if isinstance(error, pydocstyle.violations.Error) else f'error: {error}'
                for error in doc_errors
            )

        # Report errors
        if messages:
            raise ItemRunError('\n'.join(messages))


class StylePlugin(CachedFileCheckPlugin):
    name = 'style'
    item = StyleItem
