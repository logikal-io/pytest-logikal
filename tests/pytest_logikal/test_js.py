import json
import re
from collections.abc import Callable
from subprocess import CompletedProcess

from pytest import mark, raises
from pytest_mock import MockerFixture

from pytest_logikal.file_checker import CachedBatchFileCheckItem
from pytest_logikal.js import JSPlugin
from tests.pytest_logikal.conftest import FILES_DIR

INVALID_PATH_STDOUT = json.dumps([{'filePath': 'invalid_path', 'messages': []}])


def test_run(plugin_item: Callable[..., CachedBatchFileCheckItem]) -> None:
    contents = {
        'valid.js': (FILES_DIR / 'valid.js').read_text(),
        'valid.mjs': (FILES_DIR / 'valid.mjs').read_text(),
        'invalid.js': (FILES_DIR / 'invalid.js').read_text(),
    }
    item = plugin_item(plugin=JSPlugin, item=CachedBatchFileCheckItem, file_contents=contents)
    paths = {path: item.path.parent / path for path in contents}
    results = item.plugin.runtest(paths=list(paths.values()), workers=1)

    # Valid file
    assert paths['valid.js'] in results
    assert not results[paths['valid.js']].errors
    assert paths['valid.mjs'] in results
    assert not results[paths['valid.mjs']].errors

    # Invalid file
    assert paths['invalid.js'] in results
    errors = '\n'.join(results[paths['invalid.js']].errors)
    for message in [
        r'Missing semicolon.*\(@stylistic/semi\)',
        r'Expected indentation.*\(@stylistic/indent\)',
        r'Expected multiple line comments.*\(multiline-comment-style\)',
        r'This line has a length of.*\(max-len\)',
        r'Strings must use singlequote.*\(@stylistic/quotes\)',
        r'Expected no linebreak.*\(@stylistic/nonblock-statement-body-position\)',
    ]:
        assert re.search(message, errors)


@mark.parametrize(('process', 'error'), [
    (CompletedProcess(args=[], returncode=0, stdout='invalid_json'), 'invalid_json'),
    (CompletedProcess(args=[], returncode=0, stdout=INVALID_PATH_STDOUT), 'Invalid path'),
    (CompletedProcess(args=[], returncode=-9, stdout='', stderr='process failed'),
     'ESLint was terminated by signal 9: process failed'),
])
def test_run_error(
    mocker: MockerFixture,
    plugin_item: Callable[..., CachedBatchFileCheckItem],
    process: CompletedProcess[str],
    error: str,
) -> None:
    empty_file = {'file.js': ''}
    item = plugin_item(plugin=JSPlugin, item=CachedBatchFileCheckItem, file_contents=empty_file)
    mocker.patch('pytest_logikal.js.subprocess.run', return_value=process)

    with raises(RuntimeError, match=error):
        item.plugin.runtest(paths=[item.path.resolve()], workers=None)
