# pylint: disable=protected-access
from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import browser as plugin, core


def test_report_header(mocker: MockerFixture) -> None:
    config = mocker.MagicMock()
    config.stash.__getitem__.return_value.values.return_value = [
        mocker.Mock(browser_version='test_browser'),
    ]

    config.get_verbosity.return_value = 0
    assert plugin.pytest_report_header(config) == 'browsers: test_browser'

    config.get_verbosity.return_value = 1
    assert plugin.pytest_report_header(config) == ['browsers:', "  'test_browser'"]


def test_browser_fixture_errors(mocker: MockerFixture) -> None:
    with raises(RuntimeError, match='must specify a browser scenario'):
        plugin._check_browser_fixture_request(request=mocker.Mock(param={}))
    mocker.patch.dict(core.EXTRAS, {'django': False})
    with raises(RuntimeError, match='`django` extra must be installed'):
        plugin._language_context('en-us')


def test_languages(mocker: MockerFixture) -> None:
    with plugin._language_context(None) as language_context:
        assert language_context is None
    assert plugin._get_languages(None) == ['en-us', 'en-gb']  # from django.conf.settings.LANGUAGES
    assert plugin._get_languages(['test']) == ['test']

    mocker.patch.dict(core.EXTRAS, {'django': False})
    assert plugin._get_languages(None) == [None]
    with raises(RuntimeError, match='`django` extra must be installed'):
        plugin._get_languages(['en-us'])
