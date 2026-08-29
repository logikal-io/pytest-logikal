import os
from pathlib import Path

import pytest
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import file_checker
from pytest_logikal.plugin import ItemRunError

ERROR_MESSAGE = 'check failed'


class ValidPlugin(file_checker.CachedFileCheckPlugin):
    name = 'valid'
    item = file_checker.CachedFileCheckItem


class ValidBatchPlugin(file_checker.CachedBatchFileCheckPlugin):
    name = 'valid_batch'

    def runtest(
        self, paths: list[Path], workers: int | None,
    ) -> dict[Path, file_checker.BatchFileCheckResult]:
        return {
            path: file_checker.BatchFileCheckResult(
                errors=[ERROR_MESSAGE] if path.name == 'failed.py' else [],
            ) for path in paths
        }


def test_invalid_arguments(mocker: MockerFixture) -> None:
    for plugin in [ValidPlugin, ValidBatchPlugin]:
        with raises(RuntimeError, match='without a cache'):
            plugin(config=mocker.Mock(cache=None))


def test_modification_times(mocker: MockerFixture) -> None:
    config = mocker.Mock(workeroutput={})
    config.cache.get.return_value = {'test_file.py': 42}

    plugin = ValidPlugin(config=config)

    # Simulate a test node going down
    new_mtimes = {'test_file.py': 4242}
    plugin.pytest_testnodedown(node=mocker.Mock(workeroutput={plugin.mtimes_path: new_mtimes}))

    # Simulate a session finish on the worker node
    mocker.patch('pytest_logikal.file_checker.is_xdist_worker', return_value=True)
    plugin.pytest_sessionfinish(session=mocker.Mock(config=config))

    # Simulate a session finish on the controller node
    mocker.patch('pytest_logikal.file_checker.is_xdist_worker', return_value=False)
    plugin.pytest_sessionfinish(session=mocker.Mock(config=config))

    # Check whether the cache has been properly updated
    config.cache.set.assert_called_with(plugin.mtimes_path, new_mtimes)


def test_check_item(tmp_path: Path, mocker: MockerFixture) -> None:
    class ValidItem(file_checker.CachedFileCheckItem):
        def run(self) -> None:
            pass

    path = tmp_path / 'test.py'
    path.touch()  # create the test file
    path_mtime = path.lstat().st_mtime

    plugin = ValidPlugin(config=mocker.Mock())
    plugin.mtimes = {str(path): path_mtime}
    parent = mocker.Mock(nodeid='parent', path=path)

    item = ValidItem.from_parent(parent=parent, name='pylint', plugin=plugin)

    # Check skipping
    pytest_mock = mocker.patch('pytest_logikal.file_checker.pytest')
    item.setup()
    assert pytest_mock.skip.called

    # Check modification times
    item.runtest()
    assert plugin.new_mtimes[str(path)] == path_mtime

    # Check error handling
    excinfo = mocker.Mock(value=ItemRunError(ERROR_MESSAGE))
    excinfo.errisinstance.return_value = True
    assert item.repr_failure(excinfo) == ERROR_MESSAGE

    mocker.patch('pytest.Item.repr_failure', return_value='Error')
    excinfo.errisinstance.return_value = False
    assert item.repr_failure(excinfo) == 'Error'


def test_batch_check(tmp_path: Path, mocker: MockerFixture) -> None:
    # Create test files
    paths = {name: tmp_path / f'{name}.py' for name in ['cached', 'passed', 'failed']}
    for path in paths.values():
        path.touch()

    cached_modification_time = paths['cached'].lstat().st_mtime_ns
    passed_modification_time = paths['passed'].lstat().st_mtime_ns

    # Create plugin
    cache = mocker.Mock()
    cache.get.return_value = {str(paths['cached']): cached_modification_time}
    cache.mkdir.return_value = tmp_path
    config = mocker.Mock(cache=cache)
    config.pluginmanager.get_plugin.return_value = mocker.Mock()
    config_options = {'verbose': True}
    config.getoption = config_options.get

    plugin = ValidBatchPlugin(config=config)
    runtest = mocker.spy(plugin, 'runtest')

    # Create individual items
    items = {}
    for name, path in paths.items():
        parent = mocker.Mock(nodeid='parent', config=config, path=path)
        items[name] = plugin.item.from_parent(parent=parent, name='pylint', plugin=plugin)

    # Simulate a collection finish without xdist
    mocker.patch('pytest_logikal.file_checker.is_xdist_controller', return_value=False)
    mocker.patch('pytest_logikal.file_checker.is_xdist_worker', return_value=False)
    session = mocker.Mock(testsfailed=0, items=list(items.values()))
    plugin.pytest_collection_finish(session=session)

    assert plugin.results == file_checker.BatchFileCheckResults(path_check_results={
        paths['cached']: file_checker.BatchFileCheckResult(skipped=True),
        paths['passed']: file_checker.BatchFileCheckResult(),
        paths['failed']: file_checker.BatchFileCheckResult(errors=[ERROR_MESSAGE]),
    })
    runtest.assert_called_once_with(paths=[paths['passed'], paths['failed']], workers=None)
    cache.set.assert_called_once_with(plugin.path_modification_times_key, {
        str(paths['cached']): cached_modification_time,
        str(paths['passed']): passed_modification_time,
    })

    # Check that repeated collection hooks do not run the batch checks again
    plugin.pytest_collection_finish(session=session)
    runtest.assert_called_once()

    # Check success
    items['passed'].runtest()

    # Check skipping
    with raises(pytest.skip.Exception, match='file has previously passed check'):
        items['cached'].runtest()

    # Check failure
    with raises(pytest.fail.Exception, match=ERROR_MESSAGE):
        items['failed'].runtest()

    # Check a missing path result
    plugin.results.path_check_results = {}
    with raises(pytest.fail.Exception, match='Results not found'):
        items['passed'].runtest()

    # Check collection failure
    session.testsfailed = 1
    plugin.pytest_collection_finish(session=session)
    del plugin.results
    with raises(pytest.skip.Exception, match='test collection failure'):
        items['passed'].runtest()

    # Check a missing results file
    plugin.results_path.unlink()
    del plugin.results
    with raises(pytest.fail.Exception, match='batch check execution error'):
        items['passed'].runtest()


def test_batch_xdist_collection_failure(tmp_path: Path, mocker: MockerFixture) -> None:
    cache = mocker.Mock()
    cache.get.return_value = {}
    cache.mkdir.return_value = tmp_path
    config = mocker.Mock(cache=cache, rootpath=tmp_path, workerinput={'valid_batch_run_id': 'run'})
    config.pluginmanager.get_plugin.return_value = mocker.Mock(testsfailed=1)
    plugin = ValidBatchPlugin(config=config)

    node = mocker.Mock(workerinput={'workercount': 1})
    node.gateway.id = 'gw0'

    plugin.pytest_configure_node(node=node)
    assert node.workerinput[plugin.run_id_key] == plugin.run_id

    plugin.pytest_xdist_node_collection_finished(node=node, ids=[])
    assert plugin.results == file_checker.BatchFileCheckResults(collection_failed=True)


def test_batch_cleanup(tmp_path: Path, mocker: MockerFixture) -> None:
    is_xdist_worker = mocker.patch('pytest_logikal.file_checker.is_xdist_worker')

    # Add results files
    cache = mocker.Mock()
    cache.get.return_value = {}
    cache.mkdir.return_value = tmp_path
    config = mocker.Mock(cache=cache, workerinput={'valid_batch_run_id': 'run'})
    plugin = ValidBatchPlugin(config=config)
    plugin.results_path.touch()
    stale_results_path = tmp_path / 'results_stale.json'
    stale_results_path.touch()
    os.utime(stale_results_path, (0, 0))  # set access and modified times

    # Workers must not remove shared result files
    is_xdist_worker.return_value = True
    plugin.pytest_sessionfinish(session=mocker.Mock())
    assert plugin.results_path.exists()
    assert stale_results_path.exists()

    # The controller removes this run's file and stale files
    is_xdist_worker.return_value = False
    plugin.pytest_sessionfinish(session=mocker.Mock())
    assert not plugin.results_path.exists()
    assert not stale_results_path.exists()
