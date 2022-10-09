from importlib import reload
from pathlib import Path

from PIL import Image
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import utils

utils = reload(utils)  # ensures coverage captures definitions


def test_expected_not_found(tmp_path: Path, mocker: MockerFixture) -> None:
    tty = mocker.patch('pytest_logikal.utils.sys.stdin.isatty')
    run = mocker.patch('pytest_logikal.utils.run')
    input_keys = mocker.patch('pytest_logikal.utils.input')

    # Non-interactive
    tty.return_value = False
    with raises(AssertionError, match='file does not exist'):
        utils.assert_image_equal(b'', tmp_path / 'non_interactive', temp_path=tmp_path)
    assert (tmp_path / 'expected.png').is_file()

    # Interactive
    tty.return_value = True
    expected = tmp_path / 'interactive.png'

    input_keys.side_effect = 'c'  # opening cancelled
    with raises(AssertionError, match='cancelled'):
        utils.assert_image_equal(b'', expected, temp_path=tmp_path)
    assert not run.called
    assert not expected.is_file()

    input_keys.side_effect = ['s', '']  # opening skipped, rejected
    with raises(AssertionError, match='rejected'):
        utils.assert_image_equal(b'', expected, temp_path=tmp_path)
    assert not run.called
    assert not expected.is_file()

    input_keys.side_effect = ['', 'accept']  # opened and accepted
    utils.assert_image_equal(b'', expected, temp_path=tmp_path)
    assert expected.is_file()
    assert run.called


def test_difference(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch('pytest_logikal.utils.sys.stdin.isatty', return_value=False)
    screenshots = Path(__file__).parent / 'screenshots/test_browser'

    actual = screenshots / 'test_browser_check_desktop_perennrose.png'
    expected = screenshots / 'test_browser_check_desktop_nincs-ido.png'
    with raises(AssertionError, match='differs'):
        utils.assert_image_equal(actual.read_bytes(), expected, temp_path=tmp_path)

    actual = tmp_path / 'diff.png'
    expected = screenshots / 'difference.png'
    with Image.open(actual) as actual_image, Image.open(expected) as expected_image:
        assert actual_image == expected_image, '\n'.join([
            'Incorrect difference', f'  Actual: {actual}', f'  Expected: {expected}',
        ])
