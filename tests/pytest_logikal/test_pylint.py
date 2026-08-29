import json
import re
from collections.abc import Callable
from subprocess import CompletedProcess

from pytest import mark, raises
from pytest_mock import MockerFixture

from pytest_logikal.file_checker import CachedBatchFileCheckItem
from pytest_logikal.pylint import PylintPlugin

INVALID_PATH_MESSAGE = json.dumps({'messages': [{'absolutePath': 'invalid_path'}]})


def test_run(plugin_item: Callable[..., CachedBatchFileCheckItem]) -> None:
    item = plugin_item(
        plugin=PylintPlugin, item=CachedBatchFileCheckItem, file_contents="x = 'invalid'",
        set_django_settings_module=False,
    )
    path = item.path.resolve()

    results = item.plugin.runtest(paths=[path], workers=1)

    assert len(results) == 1
    assert path in results
    result = results[path]
    assert len(result.errors) == 1
    error = (
        '1:0: convention: Constant name "x" doesn\'t conform to UPPER_CASE naming style'
        r' \(.* pattern\) \(invalid-name\)'
    )
    assert re.fullmatch(error, result.errors[0])


@mark.parametrize(('process', 'error'), [
    (CompletedProcess(args=[], returncode=0, stdout=INVALID_PATH_MESSAGE, stderr=''),
     'Invalid path'),
    (CompletedProcess(args=[], returncode=-9, stdout='', stderr='process failed'),
     'Pylint was terminated by signal 9: process failed'),
    (CompletedProcess(args=[], returncode=32, stdout='', stderr='process failed'),
     'Pylint failed with a usage error'),
])
def test_error(
    mocker: MockerFixture,
    plugin_item: Callable[..., CachedBatchFileCheckItem],
    process: CompletedProcess[str],
    error: str,
) -> None:
    item = plugin_item(plugin=PylintPlugin, item=CachedBatchFileCheckItem)
    mocker.patch('pytest_logikal.pylint.subprocess.run', return_value=process)

    with raises(RuntimeError, match=error):
        item.plugin.runtest(paths=[item.path.resolve()], workers=None)
