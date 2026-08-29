import json
from collections.abc import Callable
from subprocess import CompletedProcess

from pytest import mark, raises
from pytest_mock import MockerFixture

from pytest_logikal.css import CSSPlugin
from pytest_logikal.file_checker import CachedBatchFileCheckItem
from tests.pytest_logikal.conftest import FILES_DIR

INVALID_PATH_STDERR = json.dumps([{'source': 'invalid_path', 'errored': False}])


def test_run(plugin_item: Callable[..., CachedBatchFileCheckItem]) -> None:
    contents = {
        'valid.css': (FILES_DIR / 'valid.css').read_text(),
        'invalid.css': (FILES_DIR / 'invalid.css').read_text(),
    }
    item = plugin_item(plugin=CSSPlugin, item=CachedBatchFileCheckItem, file_contents=contents)
    paths = {path: item.path.parent / path for path in contents}
    results = item.plugin.runtest(paths=list(paths.values()), workers=None)

    # Valid file
    assert paths['valid.css'] not in results

    # Invalid file
    assert paths['invalid.css'] in results
    errors = '\n'.join(results[paths['invalid.css']].errors)
    for message in [
        'Unknown type selector "unknown"',
        'Unknown property "unknown-property"',
        'Expected indentation',
        'Expected a trailing semicolon',
        'Expected "p .unnested" inside "p"',
        'Expected id selector "#id_invalid_pattern" to be kebab-case',
    ]:
        assert message in errors


@mark.parametrize(('process', 'error'), [
    (CompletedProcess(args=[], returncode=0, stderr='invalid_json'), 'invalid_json'),
    (CompletedProcess(args=[], returncode=0, stderr=INVALID_PATH_STDERR), 'Invalid path'),
    (CompletedProcess(args=[], returncode=-9, stdout='', stderr='process failed'),
     'Stylelint was terminated by signal 9: process failed'),
])
def test_run_error(
    mocker: MockerFixture,
    plugin_item: Callable[..., CachedBatchFileCheckItem],
    process: CompletedProcess[str],
    error: str,
) -> None:
    empty_file = {'file.css': ''}
    item = plugin_item(plugin=CSSPlugin, item=CachedBatchFileCheckItem, file_contents=empty_file)
    mocker.patch('pytest_logikal.css.subprocess.run', return_value=process)

    with raises(RuntimeError, match=error):
        item.plugin.runtest(paths=[item.path.resolve()], workers=None)
