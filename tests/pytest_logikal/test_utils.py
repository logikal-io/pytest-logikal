from pathlib import Path

from logikal_utils.project import PYPROJECT
from PIL import Image
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import utils
from pytest_logikal.core import DEFAULT_INI_OPTIONS


def test_tmp_path(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch('pytest_logikal.utils.mkdtemp', return_value=str(tmp_path))
    assert utils.tmp_path('test_tmp_path').exists()


def test_ini_option(mocker: MockerFixture) -> None:
    option = 'max_line_length'
    mocker.patch.dict(PYPROJECT, clear=True)
    assert utils.get_ini_option(option) == DEFAULT_INI_OPTIONS[option]['value']

    test_value = 78
    mocker.patch.dict(PYPROJECT, {'tool': {'pytest': {'ini_options': {option: test_value}}}})
    assert utils.get_ini_option(option) == test_value


def test_expected_not_found(tmp_path: Path, mocker: MockerFixture) -> None:
    tty = mocker.patch('pytest_logikal.utils.sys.stdin.isatty')
    run = mocker.patch('pytest_logikal.utils.run')
    input_keys = mocker.patch('pytest_logikal.utils.input')

    # Non-interactive
    tty.return_value = False
    with raises(AssertionError, match='file does not exist'):
        utils.assert_image_equal(b'', tmp_path / 'non_interactive', image_tmp_path=tmp_path)
    assert (tmp_path / 'expected.png').is_file()

    # Interactive
    tty.return_value = True
    expected = tmp_path / 'interactive.png'

    input_keys.side_effect = 'c'  # opening cancelled
    with raises(AssertionError, match='cancelled'):
        utils.assert_image_equal(b'', expected, image_tmp_path=tmp_path)
    assert not run.called
    assert not expected.is_file()

    input_keys.side_effect = ['s', '']  # opening skipped, rejected
    with raises(AssertionError, match='rejected'):
        utils.assert_image_equal(b'', expected, image_tmp_path=tmp_path)
    assert not run.called
    assert not expected.is_file()

    input_keys.side_effect = ['', 'accept']  # opened and accepted
    utils.assert_image_equal(b'', expected, image_tmp_path=tmp_path)
    assert expected.is_file()
    assert run.called


def test_difference(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch('pytest_logikal.utils.sys.stdin.isatty', return_value=False)
    screenshots = Path(__file__).parent / 'browser/screenshots/test_browser'

    actual = screenshots / 'test_browser_check_chrome_desktop_perennrose.png'
    expected = screenshots / 'test_browser_check_chrome_desktop_nincs-ido.png'
    with raises(AssertionError, match='differs'):
        utils.assert_image_equal(actual.read_bytes(), expected, image_tmp_path=tmp_path)

    actual = tmp_path / 'diff.png'
    expected = screenshots / 'difference.png'
    with Image.open(actual) as actual_image, Image.open(expected) as expected_image:
        assert actual_image == expected_image, '\n'.join([
            'Incorrect difference', f'  Actual: {actual}', f'  Expected: {expected}',
        ])


def test_no_opener(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch('pytest_logikal.utils.Path.exists', return_value=False)
    mocker.patch('pytest_logikal.utils.sys.stdin.isatty', return_value=True)
    mocker.patch('pytest_logikal.utils.input', return_value='reject')
    with raises(AssertionError, match='rejected'):
        utils.save_image_prompt(message='Test message', source=tmp_path, destination=tmp_path)
