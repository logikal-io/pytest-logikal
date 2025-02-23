from factory.declarations import LazyFunction
from factory.django import DjangoModelFactory, Password
from factory.faker import Faker
from faker import Faker as FakerFactory

from tests.website.models import Project, User

faker = FakerFactory()


class UserFactory(DjangoModelFactory[User]):
    username = Faker('name')
    password = Password('local')
    first_name = Faker('first_name')
    last_name = Faker('last_name')

    class Meta:
        model = User


class ProjectFactory(DjangoModelFactory[Project]):
    name = LazyFunction(lambda: faker.bs().title())

    class Meta:
        model = Project
