from typing import Type

from faker.proxy import Faker
from pytest import mark
from pytest_factoryboy import register

from tests.pytest_logikal import factories
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
