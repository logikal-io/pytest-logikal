from pathlib import Path

from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import file_checker
from pytest_logikal.plugin import Item, ItemRunError


class ItemlessPlugin(file_checker.FileCheckPlugin):
    name = 'itemless'


class ValidPlugin(file_checker.FileCheckPlugin):
    name = 'valid'
    item = Item


def test_invalid_arguments(mocker: MockerFixture) -> None:
    with raises(AttributeError):
        ItemlessPlugin(config=mocker.Mock())
    with raises(RuntimeError, match='without a cache'):
        ValidPlugin(config=mocker.Mock(cache=None))


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
    class ValidItem(file_checker.CheckItem):
        def run(self) -> None:
            pass

    path = tmp_path / 'test.py'
    path.touch()  # create the test file
    path_mtime = path.lstat().st_mtime

    plugin = ValidPlugin(config=mocker.Mock())
    plugin.mtimes = {str(path): path_mtime}
    parent = mocker.Mock(nodeid='parent', path=path)

    item = ValidItem.from_parent(parent=parent, name='style', plugin=plugin)

    # Check skipping
    pytest = mocker.patch('pytest_logikal.file_checker.pytest')
    item.setup()
    assert pytest.skip.called

    # Check modification times
    item.runtest()
    assert plugin.new_mtimes[str(path)] == path_mtime

    # Check error handling
    error_message = 'check failed'
    excinfo = mocker.Mock(value=ItemRunError(error_message))
    excinfo.errisinstance.return_value = True
    assert item.repr_failure(excinfo) == error_message

    mocker.patch('pytest.Item.repr_failure', return_value='Error')
    excinfo.errisinstance.return_value = False
    assert item.repr_failure(excinfo) == 'Error'
