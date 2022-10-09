from typing import Callable

from pytest import raises

from pytest_logikal.plugin import ItemRunError
from pytest_logikal.requirements import RequirementsItem, RequirementsPlugin


def test_outdated_lockfile(plugin_item: Callable[..., RequirementsItem]) -> None:
    item = plugin_item(plugin=RequirementsPlugin, item=RequirementsItem, file_contents={
        'requirements.txt.lock': 'invalid',
        'requirements.txt': '',
    })
    with raises(ItemRunError, match='Requirements lockfile "requirements.txt.lock" is outdated'):
        item.runtest()
