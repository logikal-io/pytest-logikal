import os
from abc import abstractmethod
from typing import Any, Dict, Type

from logikal_utils.random import DEFAULT_RANDOM_SEED
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.chromium.service import ChromiumService

from pytest_logikal.browser.base import Browser


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
            '--in-process-gpu',  # memory saving
            # Unwanted features
            '--no-default-browser-check',
            '--no-first-run',
            '--ash-no-nudges',
            '--disable-search-engine-choice-screen',
            # Deterministic rendering
            # See https://issuetracker.google.com/issues/172339334
            '--allow-pre-commit-input',
            # See https://issues.chromium.org/issues/40039960#comment29
            '--disable-partial-raster',
            '--disable-skia-runtime-opts',
            # Deterministic mode
            # '--deterministic-mode',
            '--run-all-compositor-stages-before-draw',
            '--disable-new-content-rendering-timeout',
            # See https://issues.chromium.org/issues/40288100
            # '--enable-begin-frame-control',  # part of deterministic mode
            '--disable-threaded-animation',
            '--disable-threaded-scrolling',
            '--disable-checker-imaging',
            '--disable-image-animation-resync',
            # Web platform behavior
            f'--js-flags=--random-seed={DEFAULT_RANDOM_SEED}',
            *(['--no-sandbox'] if os.getenv('DOCKER_RUN') == '1' else [])
        ]

        options = self.options_class()
        options.binary_location = str(self.version.path)
        if self.settings.mobile:
            args.append('--hide-scrollbars')
        for arg in args:
            options.add_argument(arg)

        service = self.service_class(executable_path=str(self.version.driver_path))

        return {'options': options, 'service': service}
