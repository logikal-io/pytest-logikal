import json
import subprocess

import pytest
from logikal_utils.project import PYPROJECT

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
        plugins = [
            'pylint.extensions.code_style',
            'pylint.extensions.comparison_placement',
            'pylint.extensions.confusing_elif',
            'pylint.extensions.for_any_all',
            'pylint.extensions.consider_refactoring_into_while_condition',
            'pylint.extensions.consider_ternary_expression',
            'pylint.extensions.bad_builtin',
            'pylint.extensions.mccabe',
            'pylint.extensions.dict_init_mutate',
            'pylint.extensions.dunder',
            'pylint.extensions.check_elif',
            'pylint.extensions.empty_comment',
            'pylint.extensions.eq_without_hash',
            'pylint.extensions.private_import',
            'pylint.extensions.no_self_use',
            'pylint.extensions.overlapping_exceptions',
            'pylint.extensions.redefined_loop_name',
            'pylint.extensions.set_membership',
            'pylint.extensions.typing',
            'pylint.extensions.while_used',
        ]
        command = [
            'pylint', str(self.path),
            '--init-hook=import sys; sys.path.append(".")',
            f'--max-line-length={self.config.getini("max_line_length")}',
            '--include-naming-hint=y',
            '--output-format=json2',
            f'--max-complexity={self.config.getini("max_complexity")}',
        ]
        enable = [
            'useless-suppression',
            'use-symbolic-message-instead',
            'use-implicit-booleaness-not-comparison-to-zero',
            'use-implicit-booleaness-not-comparison-to-string',
            'prefer-typing-namedtuple',
        ]
        disable = [
            # Checks covered by pycodestyle
            'line-too-long', 'trailing-newlines', 'trailing-whitespace', 'missing-final-newline',
            # Checks covered by isort
            'wrong-import-order',
            # Other checks
            'duplicate-code',  # not working with distributed exeuction
            'logging-fstring-interpolation',  # we are mostly using f-strings in logging
            'missing-docstring',  # we are less strict about class and function docstrings
            'consider-using-tuple',  # lists are often easier to read
            'use-dict-literal',  # the dict class constructor approach is sometimes useful
            'consider-using-namedtuple-or-dataclass',  # unnamed tuples can be sometimes useful
        ]
        if 'DJANGO_SETTINGS_MODULE' in self.config.inicfg:
            disable += [
                'too-few-public-methods',  # common error with some Django classes
                'unsubscriptable-object',  # common error with generic types in django-stubs
            ]
            plugins += ['pylint_django']
            command += [
                f'--django-settings-module={self.config.inicfg["DJANGO_SETTINGS_MODULE"]}',
                r'--module-rgx=[^\WA-Z]*$',  # allow (migration) modules to start with digits
            ]

        pyproject_pylint = PYPROJECT.get('tool', {}).get('pylint', {}).get('messages_control', {})
        enable = pyproject_pylint.get('enable', enable)
        disable = pyproject_pylint.get('disable', disable)
        command += [
            f'--enable={",".join(enable)}', f'--disable={",".join(disable)}',
            f'--load-plugins={",".join(plugins)}',
        ]

        # Note that we are running Pylint in a subprocess and process its output instead of
        # importing it due to its license (GPLv2). The subprocess call is secure as it is not using
        # untrusted input.
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        try:
            if messages := json.loads(process.stdout).get('messages'):
                formatter = '{line}:{column}: {type}: {message} ({symbol})'
                raise ItemRunError('\n'.join(formatter.format(**message) for message in messages))
        except json.decoder.JSONDecodeError as error:
            raise ItemRunError(f'Error: {process.stdout or process.stderr}') from error


class PylintPlugin(CachedFileCheckPlugin):
    name = 'pylint'
    item = PylintItem
