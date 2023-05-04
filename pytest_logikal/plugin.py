from abc import abstractmethod
from pathlib import Path
from typing import Any, Iterable, Type

import pytest

from pytest_logikal.core import ReportInfoType


class ItemRunError(Exception):
    """An item run error."""


class Item(pytest.Item):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.add_marker(self.name)

    def reportinfo(self) -> ReportInfoType:
        info = f'[{self.name}]'
        if self.path:
            relative_path = self.path.relative_to(self.config.invocation_params.dir)
            info += f' {relative_path}'
        return (self.path, None, info)

    def repr_failure(
        self, excinfo: pytest.ExceptionInfo[BaseException], *args: Any, **kwargs: Any,
    ) -> Any:
        if excinfo.errisinstance(ItemRunError):
            return str(excinfo.value)
        return super().repr_failure(excinfo, *args, **kwargs)

    @abstractmethod
    def runtest(self) -> None:
        ...


class Plugin:
    name: str
    item: Type[Item]

    def __init__(self, config: pytest.Config):
        if not hasattr(self, 'name'):
            raise AttributeError('You must provide a plugin name')
        if not hasattr(self, 'item'):
            raise AttributeError('You must provide an item type')

        self.config = config

    def pytest_collect_file(self, parent: pytest.Collector) -> Any:
        plugin = self

        class File(pytest.File):
            def collect(self) -> Iterable[Item]:
                # Ensure that a plugin item is added once and only once per session
                if not any(isinstance(item, plugin.item) for item in self.session.items):
                    yield plugin.item.from_parent(parent=self, name=plugin.name)
        return File.from_parent(parent, path=Path('check'))
