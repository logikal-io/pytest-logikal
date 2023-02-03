from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable, Type, final

import pytest
from xdist import is_xdist_worker
from xdist.workermanage import WorkerController

from pytest_logikal.plugin import Item, Plugin


class FileCheckItem(Item):
    def __init__(self, *, plugin: 'FileCheckPlugin', **kwargs: Any):
        super().__init__(**kwargs)
        self.plugin = plugin

    @abstractmethod
    def runtest(self) -> None:
        ...


class FileCheckPlugin(Plugin):
    item: Type[FileCheckItem]

    def check_file(self, file_path: Path) -> bool:  # pylint: disable=no-self-use
        return file_path.suffix == '.py'

    # Note: the arguments change but that is fine because pytest dynamically prunes them
    def pytest_collect_file(  # type: ignore[override] # pylint: disable=arguments-differ
        self, file_path: Path, parent: pytest.Collector,
    ) -> Any:
        plugin = self
        if self.check_file(file_path):
            class File(pytest.File):
                def collect(self) -> Iterable[FileCheckItem]:
                    yield plugin.item.from_parent(parent=self, name=plugin.name, plugin=plugin)
            return File.from_parent(parent, path=file_path)
        return None


class CachedFileCheckItem(FileCheckItem):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.plugin: 'CachedFileCheckPlugin'
        self._current_mtime: float

    def setup(self) -> None:
        previous_mtime = self.plugin.mtimes.get(str(self.path))
        self._current_mtime = self.path.lstat().st_mtime
        if previous_mtime is not None and previous_mtime == self._current_mtime:
            pytest.skip('file has previously passed check')

    @abstractmethod
    def run(self) -> None:
        ...

    @final
    def runtest(self) -> None:
        # Run the test in the child object
        self.run()

        # Store the file modification time if the test was successful
        self.plugin.new_mtimes[str(self.path)] = self._current_mtime


class CachedFileCheckPlugin(FileCheckPlugin):
    item: Type[CachedFileCheckItem]

    def __init__(self, config: pytest.Config):
        super().__init__(config=config)

        if not config.cache:
            raise RuntimeError('Cannot use a file check plugin without a cache')

        self.cache = config.cache
        self.mtimes_path = f'{self.name}/mtimes'
        self.mtimes = self.cache.get(self.mtimes_path, {})
        self.new_mtimes: Dict[str, float] = {}

    def pytest_testnodedown(self, node: WorkerController, *_args: Any, **_kwargs: Any) -> None:
        # Update the controller's file modification times with the values on the worker nodes
        self.new_mtimes.update(node.workeroutput[self.mtimes_path])

    def pytest_sessionfinish(self, session: pytest.Session, *_args: Any, **_kwargs: Any) -> None:
        if is_xdist_worker(session):
            # Transfer the new file modification times from the worker nodes to the controller node
            mtimes_path = self.mtimes_path
            self.config.workeroutput[mtimes_path] = self.new_mtimes  # type: ignore[attr-defined]
        else:
            # Update the cache with the new file modification times
            self.cache.set(self.mtimes_path, {**self.mtimes, **self.new_mtimes})
