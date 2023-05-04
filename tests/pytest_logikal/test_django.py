import sys
from importlib import import_module
from typing import Callable, Type

from django.apps import AppConfig, apps
from django.conf import Settings
from faker.proxy import Faker
from pytest import mark, raises
from pytest_factoryboy import register
from pytest_mock import MockerFixture

from pytest_logikal import django
from pytest_logikal.plugin import Item, ItemRunError
from tests.pytest_logikal import factories
from tests.pytest_logikal.conftest import FILES_DIR
from tests.website.models import Project, User

register(factories.UserFactory)
register(factories.ProjectFactory)


@mark.parametrize('run', range(10))  # we test multiple runs just to be sure
def test_faker_seed(faker: Faker, run: int) -> None:  # pylint: disable=unused-argument
    assert faker.name() == 'Allison Hill'
    assert faker.name() == 'Noah Rhodes'


@mark.parametrize('run', range(10))
def test_faker_seed_again(faker: Faker, run: int) -> None:  # pylint: disable=unused-argument
    assert faker.name() == 'Allison Hill'
    assert faker.name() == 'Noah Rhodes'


@mark.parametrize('run', range(10))  # we test multiple runs just to be sure
@mark.django_db
def test_factories(  # pylint: disable=unused-argument
    user_factory: Type[User], project_factory: Type[Project], run: int,
) -> None:
    assert user_factory().first_name == 'Jeffrey'
    assert user_factory().first_name == 'Robert'
    assert project_factory().name == 'Architect Bleeding-Edge Mindshare'
    assert project_factory().name == 'Expedite Proactive Schemas'


@mark.parametrize('run', range(10))  # we test multiple runs just to be sure
@mark.django_db
def test_factories_again(  # pylint: disable=unused-argument
    user_factory: Type[User], project_factory: Type[Project], run: int,
) -> None:
    assert user_factory().first_name == 'Jeffrey'
    assert user_factory().first_name == 'Robert'
    assert project_factory().name == 'Architect Bleeding-Edge Mindshare'
    assert project_factory().name == 'Expedite Proactive Schemas'


def test_migration_item_run(
    mocker: MockerFixture,
    plugin_item: Callable[..., Item],
    settings: Settings,
) -> None:
    # Create migration file
    invalid_migration = (FILES_DIR / 'invalid_migration.py').read_text()
    item = plugin_item(plugin=django.MigrationPlugin, item=django.MigrationItem, file_contents={
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
