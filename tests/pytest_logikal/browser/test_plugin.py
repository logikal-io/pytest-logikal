import re

from logikal_utils.project import PYPROJECT
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal.browser import plugin


def test_config_errors(mocker: MockerFixture) -> None:
    mocker.patch.dict(PYPROJECT, {'tool': {}})
    with raises(RuntimeError, match='specify at least one browser version'):
        plugin.pytest_sessionstart(session=mocker.Mock())

    mocker.patch.dict(PYPROJECT, {'tool': {'browser': {'versions': {'invalid': None}}}})
    with raises(RuntimeError, match='"invalid" .* not supported'):
        plugin.pytest_sessionstart(session=mocker.Mock())


def test_report_header(mocker: MockerFixture) -> None:
    config = mocker.Mock()

    config.get_verbosity.return_value = 0
    assert re.match(r'browsers:.*chrome \([^)]+\)', str(plugin.pytest_report_header(config)))

    config.get_verbosity.return_value = 1
    assert plugin.pytest_report_header(config)[0] == 'browsers:'


def test_browser_fixture_error(mocker: MockerFixture) -> None:
    with raises(RuntimeError, match='must specify a browser scenario'):
        plugin.check_browser_fixture_request(request=mocker.Mock(param={}))
