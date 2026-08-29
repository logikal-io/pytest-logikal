import dataclasses
import json
from abc import abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from logging import getLogger
from pathlib import Path
from time import time
from typing import Any, final
from uuid import uuid4

import pytest
from xdist import is_xdist_controller, is_xdist_worker
from xdist.workermanage import WorkerController

from pytest_logikal.plugin import Item, Plugin

logger = getLogger(__name__)

_BATCH_OUTPUT_STARTED_KEY = pytest.StashKey[bool]()


class FileCheckItem(Item):
    def __init__(self, *, plugin: 'FileCheckPlugin', **kwargs: Any):
        super().__init__(**kwargs)
        self.plugin = plugin

    @abstractmethod
    def runtest(self) -> None:
        ...


class FileCheckPlugin(Plugin):
    item: type[FileCheckItem]

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
    item: type[CachedFileCheckItem]

    def __init__(self, config: pytest.Config):
        super().__init__(config=config)

        if not config.cache:
            raise RuntimeError('Cannot use a file check plugin without a cache')

        self.cache = config.cache
        self.mtimes_path = f'{self.name}/mtimes'
        self.mtimes = self.cache.get(self.mtimes_path, {})
        self.new_mtimes: dict[str, float] = {}

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


class ExecutionFailed(RuntimeError):
    """
    Exception to represent batch check execution errors.
    """


@dataclass
class BatchFileCheckResult:
    errors: list[str] = field(default_factory=list)
    skipped: bool = False


@dataclass
class BatchFileCheckResults:
    collection_failed: bool = False
    path_check_results: dict[Path, BatchFileCheckResult | None] | None = None

    def as_dict(self) -> dict[str, Any]:
        results = dataclasses.asdict(self)
        if path_check_results := results.get('path_check_results'):
            results['path_check_results'] = {  # serialize paths
                str(path): result for path, result in path_check_results.items()
            }
        return results

    @staticmethod
    def from_dict(results: dict[str, Any]) -> 'BatchFileCheckResults':
        if path_check_results := results.get('path_check_results'):  # deserialize results
            results['path_check_results'] = {
                Path(path): BatchFileCheckResult(**result) if result else None
                for path, result in path_check_results.items()
            }
        return BatchFileCheckResults(**results)


class CachedBatchFileCheckItem(FileCheckItem):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.plugin: 'CachedBatchFileCheckPlugin'

    def runtest(self) -> None:
        try:
            results = self.plugin.results
            if results.collection_failed:
                pytest.skip('check skipped due to test collection failure')
            if not results.path_check_results or self.path not in results.path_check_results:
                pytest.fail(f'Results not found for path "{self.path}"')
            if result := results.path_check_results[self.path]:
                if result.skipped:
                    pytest.skip('file has previously passed check')
                if result.errors:
                    pytest.fail('\n'.join(result.errors), pytrace=False)
        except ExecutionFailed:
            pytest.fail('Failed due to batch check execution error', pytrace=False)


class CachedBatchFileCheckPlugin(FileCheckPlugin):
    item = CachedBatchFileCheckItem
    results_max_age_seconds = 24 * 60 * 60  # 24 hours
    results_file_prefix = 'results'

    def __init__(self, config: pytest.Config):
        super().__init__(config=config)

        if not config.cache:
            raise RuntimeError('Cannot use a batch file check plugin without a cache')

        workerinput = getattr(config, 'workerinput', {})
        self.run_id_key = f'{self.name}_run_id'
        self.run_id = workerinput.get(self.run_id_key, uuid4().hex)

        self.cache = config.cache
        self.path_modification_times_key = f'{self.name}/path_modification_times'
        self.path_modification_times = {
            Path(path): modification_time for path, modification_time in self.cache.get(
                self.path_modification_times_key, {},
            ).items()
        }
        self.batch_started = False
        self._collection_finished_nodes: set[str] = set()

    @abstractmethod
    def runtest(self, paths: list[Path], workers: int | None) -> dict[Path, BatchFileCheckResult]:
        """
        Run a batch check on the given paths and return the check result for each path.
        """

    @staticmethod
    def _path_modification_time(path: Path) -> int:
        return path.lstat().st_mtime_ns

    def _path_modification_times(self, paths: list[Path]) -> dict[Path, int]:
        return {path: self._path_modification_time(path) for path in paths}

    def _skipped_result_or_none(
        self, path: Path, modification_time: int,
    ) -> BatchFileCheckResult | None:
        if modification_time == self.path_modification_times.get(path):
            return BatchFileCheckResult(skipped=True)
        return None

    def _run_batch(self, paths: list[Path], workers: int | None = None) -> None:
        # Prepare batch
        if self.batch_started:
            return
        self.batch_started = True

        initial_path_modification_times = self._path_modification_times(paths=paths)
        results = {
            path: self._skipped_result_or_none(path=path, modification_time=modification_time)
            for path, modification_time in initial_path_modification_times.items()
        }

        # Run batch when there are files to check
        if batch_paths := [path for path, result in results.items() if result is None]:
            self._print_info(paths=batch_paths, workers=workers, all_files=len(results))
            results.update(self.runtest(paths=batch_paths, workers=workers))

        self._save_results(BatchFileCheckResults(path_check_results=results))

        # Update path modification times for successful checks
        if batch_paths:
            self.path_modification_times.update({
                path: initial_path_modification_times[path] for path, result in results.items()
                if not result or not result.errors
            })
            self.cache.set(self.path_modification_times_key, {
                str(path): modification_time
                for path, modification_time in self.path_modification_times.items()
            })

        # Emit trailing newline
        self._print_trailing_newline(workers=workers)

    def _print_info(self, paths: list[Path], workers: int | None, all_files: int) -> None:
        if terminal := self.config.pluginmanager.get_plugin('terminalreporter'):
            if _BATCH_OUTPUT_STARTED_KEY not in self.config.stash:
                if workers is not None:  # pragma: no cover
                    terminal.write('\n')  # post-collection newline to clear xdist messages
                terminal.write_line('\nRunning checks', blue=True, bold=True)
                self.config.stash[_BATCH_OUTPUT_STARTED_KEY] = True
            files = len(paths)
            terminal.write_line(
                f'Running {self.name} checks on {files} file{'s' if files != 1 else ''}'
                f' ({all_files - files} skipped)...'
            )
            if self.config.getoption('verbose'):
                terminal.write_line(f'  paths: {paths}')
                terminal.write_line(f'  workers: {workers}')

    def _print_trailing_newline(self, workers: int | None) -> None:
        if (terminal := self.config.pluginmanager.get_plugin('terminalreporter')) and workers:
            batch_plugins = (
                plugin for plugin in self.config.pluginmanager.get_plugins()
                if isinstance(plugin, CachedBatchFileCheckPlugin)
            )
            all_plugins_started = all(plugin.batch_started for plugin in batch_plugins)

            if _BATCH_OUTPUT_STARTED_KEY in self.config.stash and all_plugins_started:
                terminal.write_line('')  # pragma: no cover

    @cached_property
    def results_path(self) -> Path:
        return self.cache.mkdir(self.name) / f'{self.results_file_prefix}_run_{self.run_id}.json'

    def _save_results(self, results: BatchFileCheckResults) -> None:
        logger.debug(f'Writing results to file "{self.results_path}"')
        self.results_path.write_text(json.dumps(results.as_dict()))

    @cached_property
    def results(self) -> BatchFileCheckResults:
        """
        Return the results of each check.
        """
        logger.debug(f'Loading results from file "{self.results_path}"')
        if not self.results_path.exists():
            raise ExecutionFailed()
        results = json.loads(self.results_path.read_text(encoding='utf-8'))
        return BatchFileCheckResults.from_dict(results)

    def pytest_configure_node(self, node: WorkerController) -> None:
        node.workerinput[self.run_id_key] = self.run_id

    def pytest_xdist_node_collection_finished(
        self, node: WorkerController, ids: Sequence[str],
    ) -> None:
        # Wait until all nodes finish collection
        self._collection_finished_nodes.add(node.gateway.id)
        if len(self._collection_finished_nodes) < node.workerinput['workercount']:
            return

        # Skip running checks if collection failed
        session = self.config.pluginmanager.get_plugin('session')
        if session and session.testsfailed:
            self._save_results(BatchFileCheckResults(collection_failed=True))
            return

        # Run batch
        node_id_suffix = f'::{self.name}'
        paths = [
            (self.config.rootpath / node_id.removesuffix(node_id_suffix)).resolve()
            for node_id in ids if node_id.endswith(node_id_suffix)
        ]
        self._run_batch(paths=paths, workers=node.workerinput.get('workercount'))

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        # Skip running in-process checks if collection failed or if we are running with xdist
        if session.testsfailed:
            self._save_results(BatchFileCheckResults(collection_failed=True))
            return
        if is_xdist_controller(session) or is_xdist_worker(session):
            return

        # Run batch
        self._run_batch(paths=[
            item.path.resolve()
            for item in session.items if getattr(item, 'plugin', None) == self
        ])

    def pytest_sessionfinish(self, session: pytest.Session, *args: Any, **kwargs: Any) -> None:
        # Execute cleanup on controller
        if is_xdist_worker(session):
            return
        self.results_path.unlink(missing_ok=True)

        # Remove stale temporary results files
        oldest_allowed_time = time() - self.results_max_age_seconds
        for path in self.results_path.parent.glob(f'{self.results_file_prefix}*.json'):
            if path.stat().st_mtime < oldest_allowed_time:
                path.unlink(missing_ok=True)
