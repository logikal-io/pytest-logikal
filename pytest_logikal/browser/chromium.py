from abc import abstractmethod
from typing import Any, Dict, Type

from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.chromium.service import ChromiumService

from pytest_logikal.browser.base import Browser

DEFAULT_JS_RANDOM_SEED = 42


class ChromiumBrowser(Browser):
    @property
    @abstractmethod
    def options_class(self) -> Type[ChromiumOptions]:
        ...

    @property
    @abstractmethod
    def service_class(self) -> Type[ChromiumService]:
        ...

    # See https://www.selenium.dev/documentation/webdriver/browsers/chrome/#options
    # See https://github.com/GoogleChrome/chrome-launcher/blob/main/docs/chrome-flags-for-tools.md
    def init_args(self) -> Dict[str, Any]:
        args = [
            '--headless',
            f'--window-size={self.settings.width},{self.settings.height}',
            # Unwanted features
            '--no-default-browser-check',
            '--no-first-run',
            '--ash-no-nudges',
            '--disable-search-engine-choice-screen',
            # Web platform behavior
            f'--js-flags=--random-seed={DEFAULT_JS_RANDOM_SEED}',
        ]

        options = self.options_class()
        options.binary_location = str(self.version.path)
        if self.settings.mobile:
            args.append('--hide-scrollbars')
        for arg in args:
            options.add_argument(arg)

        service = self.service_class(executable_path=str(self.version.driver_path))

        return {'options': options, 'service': service}
