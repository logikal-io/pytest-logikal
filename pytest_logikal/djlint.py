import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Optional

import pytest
from django.conf import settings
from django_migration_linter import MigrationLinter
from django_migration_linter.management.commands import lintmigrations
from pytest_django.plugin import _blocking_manager  # pylint: disable=import-private-name
from termcolor import colored

from pytest_logikal.core import PYPROJECT, ReportInfoType
from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import Item, ItemRunError, Plugin
from pytest_logikal.utils import get_ini_option


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'htmlj: checks Django HTML Jinja templates.')
    config.addinivalue_line('markers', 'migrations: checks Django migrations.')
    if config.option.djlint:
        config.pluginmanager.register(HTMLJTemplatePlugin(config=config))
        config.pluginmanager.register(MigrationPlugin(config=config))


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('djlint')
    group.addoption('--djlint', action='store_true', default=False, help='run djlint')


class HTMLJTemplateItem(CachedFileCheckItem):
    @staticmethod
    def _color_diff(line: str) -> str:
        if line.startswith('@@'):
            return colored(line, 'cyan', force_color=True)
        if line.startswith('+'):
            return colored(line, 'green', force_color=True)
        if line.startswith('-'):
            return colored(line, 'red', force_color=True)
        return line

    def run(self) -> None:
        messages = []
        max_line_length = str(get_ini_option('max_line_length'))
        common_args = [
            str(self.path),
            '--extension', 'html.j',
            '--indent', '2',
            '--profile', 'jinja',
            '--max-line-length', max_line_length,
            '--max-attribute-length', max_line_length,
            '--linter-output-format', '{line}: error: {message} ({code})',
        ]

        # Check formatting
        command = ['djlint', '--check', '--preserve-blank-lines', *common_args]
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode:
            errors = process.stdout.strip().replace('@@\n\n', '@@\n')
            errors = '\n'.join(self._color_diff(line) for line in errors.splitlines()[2:-2])
            messages.append(errors or process.stderr.strip())

        # Lint
        ignore = [
            'J004', 'J018',  # we have our own functions for Jinja environments
            'T002',  # we always use single quotes
        ]
        command = ['djlint', '--lint', '--ignore', ','.join(ignore), *common_args]
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        if process.returncode:
            errors = process.stdout.strip()
            errors = '\n'.join(errors.splitlines()[2:-2])
            messages.append(errors or process.stderr.strip())

        # Report errors
        if messages:
            separator = colored('Errors:', 'red', attrs=['bold'], force_color=True)
            raise ItemRunError(f'\n\n{separator}\n'.join(messages))


class MigrationItem(Item):
    def runtest(self, migrations_file_path: Optional[Path] = None) -> None:
        # We cannot request a fixture here, so we use the blocking manager directly
        # See https://github.com/pytest-dev/pytest/discussions/10915
        with _blocking_manager.unblock():
            linter = MigrationLinter(**{
                'all_warnings_as_errors': True,
                **getattr(settings, 'MIGRATION_LINTER_OPTIONS', {}),
                **PYPROJECT.get('tool', {}).get(lintmigrations.CONFIG_NAME, {}),
            })
            with redirect_stdout(StringIO()) as code_stdout:
                linter.lint_all_migrations(migrations_file_path=migrations_file_path)
            migrations = 'migration' if linter.nb_total == 1 else 'migrations'
            print(f'Checked {linter.nb_total} {migrations} ({linter.nb_ignored} ignored)')
            if linter.nb_warnings or linter.nb_erroneous:
                raise ItemRunError(code_stdout.getvalue().rstrip())

    def reportinfo(self) -> ReportInfoType:
        return (self.path, None, f'[{MigrationPlugin.name}]')


class HTMLJTemplatePlugin(CachedFileCheckPlugin):
    name = 'htmlj'
    item = HTMLJTemplateItem

    def check_file(self, file_path: Path) -> bool:
        return str(file_path).endswith('.html.j')


class MigrationPlugin(Plugin):
    name = 'migrations'
    item = MigrationItem
