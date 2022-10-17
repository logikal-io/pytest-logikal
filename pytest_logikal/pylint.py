import json
import subprocess

import pytest

from pytest_logikal.core import PYPROJECT
from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('pylint')
    group.addoption('--pylint', action='store_true', default=False, help='run pylint')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'pylint: tests linting source code.')
    if config.option.pylint:
        config.pluginmanager.register(PylintPlugin(config=config))


class PylintItem(CachedFileCheckItem):
    def run(self) -> None:
        command = [
            'pylint', str(self.path),
            '--init-hook=import sys; sys.path.append(".")',
            f'--max-line-length={self.config.getini("max_line_length")}',
            '--include-naming-hint=y',
            '--output-format=json',
        ]
        enable = ['useless-suppression', 'use-symbolic-message-instead']
        disable = [
            # checks covered by pycodestyle
            'line-too-long', 'trailing-newlines', 'trailing-whitespace', 'missing-final-newline',
            # other checks
            'duplicate-code',  # not working with distributed exeuction
            'logging-fstring-interpolation',  # we are mostly using f-strings in logging
            'missing-docstring',  # we are less strict about class and function docstrings
        ]
        if 'DJANGO_SETTINGS_MODULE' in self.config.inicfg:
            disable += [
                'too-few-public-methods',  # common error with some Django classes
                'unsubscriptable-object',  # common error with generic types in django-stubs
            ]
            command += [
                '--load-plugins=pylint_django,pylint_django.checkers.migrations',
                f'--django-settings-module={self.config.inicfg["DJANGO_SETTINGS_MODULE"]}',
                r'--module-rgx=[^\WA-Z]*$',  # allow (migration) modules to start with digits
            ]

        pyproject_pylint = PYPROJECT.get('tool', {}).get('pylint', {}).get('messages_control', {})
        enable = pyproject_pylint.get('enable', enable)
        disable = pyproject_pylint.get('disable', disable)
        command += [f'--enable={",".join(enable)}', f'--disable={",".join(disable)}']

        # Note that we are running Pylint in a subprocess and process its output instead of
        # importing it due to its license (GPLv2). The subprocess call is secure as it is not using
        # untrusted input.
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        try:
            if messages := json.loads(process.stdout):
                formatter = '{line}:{column}: {type}: {message} ({symbol})'
                raise ItemRunError('\n'.join(formatter.format(**message) for message in messages))
        except json.decoder.JSONDecodeError as error:
            raise ItemRunError(f'Error: {process.stdout or process.stderr}') from error


class PylintPlugin(CachedFileCheckPlugin):
    name = 'pylint'
    item = PylintItem
