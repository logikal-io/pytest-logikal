from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.plugin import Item, Plugin


class NamelessPlugin(Plugin):
    item = Item


def test_invalid_arguments(mocker: MockerFixture) -> None:
    with raises(AttributeError):
        NamelessPlugin(config=mocker.Mock())
