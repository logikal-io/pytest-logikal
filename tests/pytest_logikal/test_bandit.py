from typing import Callable

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.bandit import BanditItem, BanditPlugin
from pytest_logikal.plugin import Item, ItemRunError


def test_run(plugin_item: Callable[..., Item]) -> None:
    item = plugin_item(plugin=BanditPlugin, item=BanditItem, file_contents='import pickle')
    error = (
        '1:0: warning: Consider possible security implications associated with pickle module. '
        r'\(B403: blacklist, confidence: high\)\n'
        'More info: https://bandit.readthedocs.io/.*'
        r'/blacklists/blacklist_imports.html\#b403-import-pickle'
    )
    with raises(ItemRunError, match=error):
        item.runtest()


def test_error(mocker: MockerFixture, plugin_item: Callable[..., Item]) -> None:
    run = mocker.patch('pytest_logikal.bandit.subprocess.run')
    run.return_value.stdout = 'error'
    item = plugin_item(plugin=BanditPlugin, item=BanditItem)
    with raises(ItemRunError, match='Error: error'):
        item.runtest()
