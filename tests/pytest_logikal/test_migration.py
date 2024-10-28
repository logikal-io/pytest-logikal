import sys
from collections.abc import Callable
from importlib import import_module

from django.apps import AppConfig, apps
from django.conf import Settings
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.migration import MigrationItem, MigrationPlugin
from pytest_logikal.plugin import Item, ItemRunError
from tests.pytest_logikal.conftest import FILES_DIR


def test_migration_item_run(
    mocker: MockerFixture,
    plugin_item: Callable[..., Item],
    settings: Settings,
) -> None:
    # Create migration file
    invalid_migration = (FILES_DIR / 'invalid_migration.py').read_text()
    item = plugin_item(plugin=MigrationPlugin, item=MigrationItem, file_contents={
        'app/__init__.py': '',
        'app/migrations/__init__.py': '',
        'app/migrations/0001_invalid.py': invalid_migration,
        'app/migrations/0002_ignored.py': invalid_migration,
    })

    # Patch installed apps
    settings.MIGRATION_LINTER_OPTIONS = {  # type: ignore[attr-defined]
        'ignore_name': ['0002_ignored'],
    }
    mocker.patch.object(sys, 'path', ['.'] + sys.path)
    app_config = AppConfig(app_name='app', app_module=import_module('app'))
    mocker.patch.dict(apps.app_configs, {'app': app_config})

    # Run plugin
    with raises(ItemRunError) as error:
        item.runtest()
    error.match(r'\(app, 0001_invalid\)... ERR')
    error.match(r"'update':[^\n]*not reversible")
    error.match(r"'update':[^\n]*RunPython names the two arguments")
    error.match(r'\(app, 0002_ignored\)... IGNORE')
