from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Optional

import pytest
from django.conf import settings
from django_migration_linter import MigrationLinter
from django_migration_linter.management.commands import lintmigrations
from pytest_django.plugin import _blocking_manager  # pylint: disable=import-private-name

from pytest_logikal.core import PYPROJECT, ReportInfoType
from pytest_logikal.plugin import Item, ItemRunError, Plugin


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('migration')
    group.addoption('--migration', action='store_true', default=False,
                    help='run django migration checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'migration: checks Django migrations.')
    if config.option.migration:
        config.pluginmanager.register(MigrationPlugin(config=config))


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


class MigrationPlugin(Plugin):
    name = 'migration'
    item = MigrationItem
