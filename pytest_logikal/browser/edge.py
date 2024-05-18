from subprocess import run

from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.webdriver import WebDriver

from pytest_logikal.browser.base import BrowserVersion
from pytest_logikal.browser.chromium import ChromiumBrowser
from pytest_logikal.browser.utils import download, make_executable, move, unzip
from pytest_logikal.utils import tmp_path


class Edge(ChromiumBrowser, WebDriver):
    """
    Microsoft Edge WebDriver.
    """
    options_class = Options
    service_class = Service


class EdgeVersion(BrowserVersion):
    name = 'edge'
    driver_class = Edge
    binary_name = 'microsoft-edge'
    driver_binary_name = 'msedgedriver'

    def install(self) -> None:
        if not self.path.exists():
            self.print(f'Installing Microsoft Edge {self.version}')
            root = 'https://packages.microsoft.com/repos/edge/pool/main/m/microsoft-edge-stable'
            url = f'{root}/microsoft-edge-stable_{self.version}-1_amd64.deb'
            tmp = tmp_path(self.name)
            package = download(url, tmp / 'edge.deb')
            run(['dpkg', '-x', str(package), str(tmp / 'edge')], check=True)  # nosec
            move(tmp / 'edge/opt/microsoft/msedge', self.path.parent)

        if not self.driver_path.exists():
            self.print(f'Installing Microsoft Edge WebDriver {self.driver_version}')
            url = f'https://msedgedriver.azureedge.net/{self.version}/edgedriver_linux64.zip'
            tmp = tmp_path(self.driver_name)
            unzip(download(url, tmp / 'edgedriver.zip'))
            move(tmp / 'edgedriver', self.driver_path.parent)
            make_executable(self.driver_path)
