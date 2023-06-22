from typing import Callable

from logikal_utils.project import PYPROJECT
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.isort import IsortItem, IsortPlugin
from pytest_logikal.plugin import Item, ItemRunError


def test_run(mocker: MockerFixture, plugin_item: Callable[..., Item]) -> None:
    mocker.patch.dict(PYPROJECT, {'tool': {'isort': {'line_length': 10}}})
    item = plugin_item(plugin=IsortPlugin, item=IsortItem, file_contents="""
        from pathlib import Path, PosixPath
        import re
    """)
    with raises(ItemRunError, match='\n\\x1b\\[32m\\+from pathlib import \\(\n.* Path'):
        item.runtest()
