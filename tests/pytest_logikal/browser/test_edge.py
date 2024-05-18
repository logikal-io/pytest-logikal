from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile

from pytest_mock import MockerFixture

from pytest_logikal.browser import Browser, scenarios, set_browser
from pytest_logikal.browser.base import BrowserVersion
from pytest_logikal.browser.edge import EdgeVersion


def test_install(mocker: MockerFixture, tmp_path: Path) -> None:
    mocker.patch('pytest_logikal.browser.edge.tmp_path', return_value=tmp_path)
    mocker.patch('pytest_logikal.browser.base.BrowserVersion.created')

    driver_zip_path = tmp_path / 'edgedriver.zip'
    with ZipFile(driver_zip_path, 'w') as driver_zip:
        driver_zip.writestr('msedgedriver', data='')

    mocker.patch('pytest_logikal.browser.edge.download', side_effect=[tmp_path, driver_zip_path])
    mocker.patch('pytest_logikal.browser.edge.run')

    browser = tmp_path / 'edge/opt/microsoft/msedge/microsoft-edge'
    browser.parent.mkdir(parents=True)
    browser.touch()

    version = EdgeVersion(version='test version', install_path=tmp_path / 'install')
    assert version.path.exists()
    assert version.driver_path.exists()


@set_browser(replace(scenarios.desktop, browsers=['edge']))
def test_installed_version(browser: Browser) -> None:
    assert browser.capabilities['browserVersion'] == BrowserVersion.created['edge'].version
