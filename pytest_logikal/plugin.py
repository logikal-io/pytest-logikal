from abc import ABC, abstractmethod
from typing import Any

import pytest

from pytest_logikal.core import ReportInfoType


class Plugin:
    name: str

    def __init__(self, config: pytest.Config):
        if not hasattr(self, 'name'):
            raise AttributeError('You must provide a plugin name')

        self.config = config


class ItemRunError(Exception):
    """An item run error."""


class AbstractItemMeta(type(ABC), type(pytest.Item)):  # type: ignore[misc]
    """Abstract metaclass of the Item class."""


class Item(pytest.Item, metaclass=AbstractItemMeta):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.add_marker(self.name)

    def reportinfo(self) -> ReportInfoType:
        relative_path = self.path.relative_to(self.config.invocation_params.dir)
        return (self.path, None, f'[{self.name}] {relative_path}')

    def repr_failure(
        self, excinfo: pytest.ExceptionInfo[BaseException], *args: Any, **kwargs: Any,
    ) -> Any:
        if excinfo.errisinstance(ItemRunError):
            return str(excinfo.value)
        return super().repr_failure(excinfo, *args, **kwargs)

    @abstractmethod
    def runtest(self) -> None:
        ...
