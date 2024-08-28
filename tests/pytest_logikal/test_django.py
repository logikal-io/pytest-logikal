import re
from typing import Type

from django.utils.timezone import get_current_timezone_name
from django.utils.translation import get_language
from faker.proxy import Faker
from pytest import mark
from pytest_factoryboy import register

from pytest_logikal.django import LiveURL, all_languages, set_language, set_timezone
from tests.pytest_logikal import factories
from tests.website.models import Project, User

register(factories.UserFactory)
register(factories.ProjectFactory)


@mark.parametrize('run', range(10))  # we test multiple runs just to be sure
def test_faker_seed(faker: Faker, run: int) -> None:  # pylint: disable=unused-argument
    assert faker.name() == 'Allison Hill'
    assert faker.name() == 'Noah Rhodes'


@mark.parametrize('run', range(10))  # we test multiple runs just to be sure
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


def test_live_url(live_url: LiveURL) -> None:
    assert re.fullmatch('http://localhost:[0-9]+', live_url())
    assert re.fullmatch('http://localhost:[0-9]+/internal/', live_url('internal'))
    assert re.fullmatch(
        'http://localhost:[0-9]+/internal/test/',
        live_url('internal', kwargs={'parameter': 'test'}),
    )


def test_language_fixture_without_decorator(language: str) -> None:
    assert language == 'en-us'


@set_language('en-us', 'en-gb')
def test_set_language(language: str) -> None:
    assert get_language() == language


@all_languages()
def test_all_languages(language: str) -> None:
    assert get_language() == language


def test_timezone_fixture_without_decorator(timezone: str) -> None:
    assert timezone == 'Europe/Zurich'


@set_timezone('Europe/London', 'America/New_York')
def test_set_timezone(timezone: str) -> None:
    assert get_current_timezone_name() == timezone
