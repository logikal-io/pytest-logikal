from logikal_utils.project import PYPROJECT
from pytest_mock import MockerFixture

from pytest_logikal import utils
from pytest_logikal.core import DEFAULT_INI_OPTIONS


def test_ini_option(mocker: MockerFixture) -> None:
    option = 'max_line_length'
    mocker.patch.dict(PYPROJECT, clear=True)
    assert utils.get_ini_option(option) == DEFAULT_INI_OPTIONS[option]['value']

    test_value = 78
    mocker.patch.dict(PYPROJECT, {'tool': {'pytest': {'ini_options': {option: test_value}}}})
    assert utils.get_ini_option(option) == test_value
