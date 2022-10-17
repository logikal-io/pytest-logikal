from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.plugin import Item, Plugin


class NamelessPlugin(Plugin):
    item = Item


class ItemlessPlugin(Plugin):
    name = 'itemless'


def test_invalid_arguments(mocker: MockerFixture) -> None:
    with raises(AttributeError):
        NamelessPlugin(config=mocker.Mock())
    with raises(AttributeError):
        ItemlessPlugin(config=mocker.Mock())
