from django.contrib.auth.hashers import make_password
from factory import Faker, LazyFunction
from factory.django import DjangoModelFactory
from faker import Faker as FakerFactory

from tests.website.models import Project, User

faker = FakerFactory()


class UserFactory(DjangoModelFactory):  # type: ignore[misc]
    username = Faker('name')
    password = LazyFunction(lambda: make_password('local'))  # nosec: used for testing
    first_name = Faker('first_name')
    last_name = Faker('last_name')

    class Meta:
        model = User


class ProjectFactory(DjangoModelFactory):  # type: ignore[misc]
    name = LazyFunction(lambda: faker.bs().title())

    class Meta:
        model = Project
