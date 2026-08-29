import json
import re
from collections.abc import Callable
from subprocess import CompletedProcess

from pytest import mark, raises
from pytest_mock import MockerFixture

from pytest_logikal.file_checker import CachedBatchFileCheckItem
from pytest_logikal.pylint import PylintPlugin

INVALID_PATH_STDOUT = json.dumps({'messages': [{'absolutePath': 'invalid_path'}]})


def test_run(plugin_item: Callable[..., CachedBatchFileCheckItem]) -> None:
    contents = {
        'valid.py': "VALID = 'valid'",
        'invalid.py': "x = 'invalid'",
    }
    item = plugin_item(
        plugin=PylintPlugin, item=CachedBatchFileCheckItem, file_contents=contents,
        set_django_settings_module=False,
    )
    paths = {path: item.path.parent / path for path in contents}
    results = item.plugin.runtest(paths=list(paths.values()), workers=1)

    # Valid file
    assert paths['valid.py'] not in results

    # Invalid file
    assert paths['invalid.py'] in results
    errors = results[paths['invalid.py']].errors
    assert len(errors) == 1
    error = (
        '1:0: convention: Constant name "x" doesn\'t conform to UPPER_CASE naming style'
        r' \(.* pattern\) \(invalid-name\)'
    )
    assert re.fullmatch(error, '\n'.join(errors))


@mark.parametrize(('process', 'error'), [
    (CompletedProcess(args=[], returncode=0, stdout='invalid_json'), 'invalid_json'),
    (CompletedProcess(args=[], returncode=0, stdout=INVALID_PATH_STDOUT), 'Invalid path'),
    (CompletedProcess(args=[], returncode=-9, stdout='', stderr='process failed'),
     'Pylint was terminated by signal 9: process failed'),
    (CompletedProcess(args=[], returncode=32, stdout='', stderr='process failed'),
     'Pylint failed with a usage error'),
])
def test_run_error(
    mocker: MockerFixture,
    plugin_item: Callable[..., CachedBatchFileCheckItem],
    process: CompletedProcess[str],
    error: str,
) -> None:
    item = plugin_item(plugin=PylintPlugin, item=CachedBatchFileCheckItem)
    mocker.patch('pytest_logikal.pylint.subprocess.run', return_value=process)

    with raises(RuntimeError, match=error):
        item.plugin.runtest(paths=[item.path.resolve()], workers=None)
