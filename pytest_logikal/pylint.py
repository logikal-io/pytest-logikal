import json
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest
from logikal_utils.project import tool_config

from pytest_logikal.file_checker import (
    BatchFileCheckResult, CachedBatchFileCheckItem, CachedBatchFileCheckPlugin,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('pylint')
    group.addoption('--pylint', action='store_true', default=False, help='run pylint')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'pylint: tests linting source code.')
    if config.option.pylint:
        config.pluginmanager.register(PylintPlugin(config=config))


class PylintPlugin(CachedBatchFileCheckPlugin):
    name = 'pylint'
    item = CachedBatchFileCheckItem

    def runtest(self, paths: list[Path], workers: int | None) -> dict[Path, BatchFileCheckResult]:
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
            'pylint', *(str(path) for path in paths),
            '--init-hook=import sys; sys.path.append(".")',
            f'--max-line-length={self.config.getini('max_line_length')}',
            '--include-naming-hint=y',
            '--output-format=json2',
            f'--max-complexity={self.config.getini('max_complexity')}',
            f'--jobs={workers or 0}',  # auto-detects number of CPUs if not provided explicitly
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
            'ungrouped-imports',
            # Other checks
            'duplicate-code',  # not working with distributed execution
            'logging-fstring-interpolation',  # we are mostly using f-strings in logging
            'missing-docstring',  # we are less strict about class and function docstrings
            'consider-using-tuple',  # lists are often easier to read
            'use-dict-literal',  # the dict class constructor approach is sometimes useful
            'consider-using-namedtuple-or-dataclass',  # unnamed tuples can be sometimes useful
        ]

        try:
            django_settings_module = self.config.getini('DJANGO_SETTINGS_MODULE')
        except ValueError:  # pragma: no cover, tested in subprocess
            django_settings_module = None

        if django_settings_module:
            disable += [
                'too-few-public-methods',  # common error with some Django classes
                'unsubscriptable-object',  # common error with generic types in django-stubs
            ]
            plugins += ['pylint_django']
            command += [
                f'--django-settings-module={django_settings_module}',
                r'--module-rgx=[^\WA-Z]*$',  # allow (migration) modules to start with digits
            ]

        messages_control = tool_config('pylint').get('messages_control', {})
        enable = messages_control.get('enable', enable)
        disable = messages_control.get('disable', disable)
        command += [
            f'--enable={','.join(enable)}', f'--disable={','.join(disable)}',
            f'--load-plugins={','.join(plugins)}',
        ]

        # Note that we are running Pylint in a subprocess and process its output instead of
        # importing it due to its license (GPLv2). The subprocess call is secure as it is not using
        # untrusted input.
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode < 0:
            raise RuntimeError(
                f'Pylint was terminated by signal {-process.returncode}: '
                f'{process.stderr.strip() or process.stdout.strip() or '(no output)'}'
            )
        if process.returncode & 32:
            raise RuntimeError(
                f'Pylint failed with a usage error (exit code {process.returncode}): '
                f'{process.stderr.strip() or process.stdout.strip() or '(no output)'}'
            )

        results: dict[Path, BatchFileCheckResult] = defaultdict(BatchFileCheckResult)
        formatter = '{line}:{column}: {type}: {message} ({symbol})'
        path_set = set(paths)  # speed up path checking on large projects
        for message in json.loads(process.stdout).get('messages', []):
            if (path := Path(message['absolutePath'])) not in path_set:
                raise RuntimeError(f'Invalid path: {path}')
            results[path].errors.append(formatter.format(**message))
        return results
