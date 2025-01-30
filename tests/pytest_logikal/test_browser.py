from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import browser as plugin


def test_report_header(mocker: MockerFixture) -> None:
    config = mocker.MagicMock()
    config.stash.__getitem__.return_value.values.return_value = [
        mocker.Mock(browser_version='test_browser'),
    ]

    config.get_verbosity.return_value = 0
    assert plugin.pytest_report_header(config) == 'browsers: test_browser'

    config.get_verbosity.return_value = 1
    assert plugin.pytest_report_header(config) == ['browsers:', "  'test_browser'"]


def test_browser_fixture_error(mocker: MockerFixture) -> None:
    with raises(RuntimeError, match='must specify a browser scenario'):
        plugin.check_browser_fixture_request(request=mocker.Mock(param={}))
