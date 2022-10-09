import py
import pycodestyle
import pydocstyle
import pytest

from pytest_logikal.core import PYPROJECT
from pytest_logikal.file_checker import CheckItem, FileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('style')
    group.addoption('--style', action='store_true', default=False,
                    help='run pycodestyle and pydocstyle')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'style: tests checking code and docstring style.')
    if config.option.style:
        config.pluginmanager.register(StylePlugin(config=config))


class StyleItem(CheckItem):
    def run(self) -> None:
        call = py.io.StdCapture.call  # pylint: disable=no-member

        # Run pycodestyle
        ignore = ['E133', 'W503']  # mutually exclusive checks with E123 and W504
        max_line_length = int(self.config.getini('max_line_length'))
        checker = pycodestyle.Checker(
            filename=self.path,
            max_line_length=max_line_length,
            max_doc_length=max_line_length,
            format='%(row)s:%(col)s: error: %(text)s (%(code)s)',
            ignore=PYPROJECT.get('tool', {}).get('pycodestyle', {}).get('ignore', ignore),
        )
        code_errors, code_stdout, _code_stderr = call(checker.check_all)

        # Run pydocstyle
        select = pydocstyle.violations.all_errors - {
            'D100', 'D101', 'D102', 'D103', 'D104', 'D105', 'D106', 'D107',
            'D200', 'D203', 'D204', 'D212', 'D407', 'D408', 'D409',
        }
        select = PYPROJECT.get('tool', {}).get('pydocstyle', {}).get('select', select)
        doc_errors = list(pydocstyle.check(filenames=[str(self.path)], select=select))

        # Report errors
        messages = []
        if code_errors:
            messages.append(code_stdout.rstrip())
        if doc_errors:
            messages.extend(f'{e.line}: error: {e.short_desc} ({e.code})' for e in doc_errors)
        if messages:
            raise ItemRunError('\n'.join(messages))


class StylePlugin(FileCheckPlugin):
    name = 'style'
    item = StyleItem
