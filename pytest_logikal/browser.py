import inspect
import logging
import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from operator import itemgetter
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, Optional, cast

import pytest
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome

from pytest_logikal.utils import Function, assert_image_equal

logger = logging.getLogger(__name__)

Fixture = Callable[[Function], Function]


@pytest.fixture(scope='session', autouse=True)
def faker_seed() -> int:
    """
    Set a default seed for Faker for deterministic testing. Automatically applied.
    """
    return 42


@dataclass(frozen=True)
class BrowserSettings:
    """
    Browser settings data.

    Args:
        name: The name to use for screenshots.
        width: The width of the browser window.
        height: The height of the browser window (use :obj:`None` for unlimited).
        mobile: Whether it is a mobile browser.

    """
    name: Optional[str] = None
    width: int = 1920
    height: Optional[int] = None
    mobile: bool = False


class Browser:
    def __init__(
        self,
        temp_path: Path,
        settings: Optional[BrowserSettings] = None,
        screenshot_path: Path = Path('screenshot'),
    ):
        """
        Browser automation.

        Has the same attributes and methods as a :mod:`selenium.webdriver.Chrome
        <selenium.webdriver.chrome.webdriver>` object.
        """
        self.temp_path = temp_path
        self.settings = settings or BrowserSettings()
        logger.debug(f'Browser settings: {asdict(self.settings)}')
        self.name = self.settings.name
        self.screenshot_path = screenshot_path
        logger.debug(f'Using screenshot path "{self.screenshot_path}"')

        options = cast(Any, ChromeOptions())  # add_argument is not yet typed
        if self.settings.mobile:
            options.add_argument('--hide-scrollbars')
        options.add_argument('--headless')
        options.add_argument(f'--window-size={self.settings.width},{self.settings.height or 1080}')
        self.driver = Browser._get_driver(options=options)

    @staticmethod
    def _get_driver(options: ChromeOptions) -> Chrome:
        try:
            return Chrome(options=options)
        except SessionNotCreatedException as error:
            if driver_version_error := Browser._driver_version_error(str(error.msg)):
                raise RuntimeError(driver_version_error) from None  # override parent exception
            raise

    @staticmethod
    def _driver_version_error(error_message: str) -> Optional[str]:
        search = re.search(
            'This version of ChromeDriver only supports Chrome version (.*?)\n'
            'Current browser version is (.*?) with binary path',
            error_message,
        )
        return '\n'.join([
            f'Invalid ChromeDriver version (compatible with Chrome {search.group(1)})',
            f'Please download a release compatible with Chrome version {search.group(2)} '
            '(see https://chromedriver.chromium.org/downloads)'
        ]) if search else None

    def __enter__(self) -> 'Browser':
        return self

    def __exit__(self, *args: Any) -> None:
        self.driver.__exit__(*args)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.driver, name)

    @contextmanager
    def auto_height(self) -> Generator[None, None, None]:
        if self.settings.height:
            yield
            return
        logger.debug('Using full page height')
        original_size = self.driver.get_window_size()
        script = 'return document.body.parentNode.scrollHeight'
        height = self.driver.execute_script(script)  # type: ignore[no-untyped-call]
        self.driver.set_window_size(original_size['width'], height)
        try:
            yield
        finally:
            self.driver.set_window_size(**original_size)

    def check(self, name: Optional[str] = None) -> None:
        """
        Create a screenshot and check it against an expected version.

        Args:
            name: The name of the expected screenshot.

        """
        name_parts = [self.screenshot_path.name, self.name, name]
        full_name = '_'.join(part for part in name_parts if part is not None)
        expected = self.screenshot_path.with_name(full_name).with_suffix('.png')
        with self.auto_height():
            screenshot = self.driver.get_screenshot_as_png()
        assert_image_equal(actual=screenshot, expected=expected, temp_path=self.temp_path)


@pytest.fixture
def browser(tmp_path: Path, request: Any) -> Iterable[Browser]:
    """
    Yield a :class:`Browser` instance.
    """
    params = getattr(request, 'param', {})
    screenshot_path = params.pop('screenshot_path', None)
    kwargs = {'screenshot_path': screenshot_path} if screenshot_path else {}
    with Browser(temp_path=tmp_path, settings=BrowserSettings(**params), **kwargs) as instance:
        yield instance


def set_browser(*args: Dict[str, Any], **kwargs: Any) -> Fixture[Any]:
    """
    Control the creation of the :class:`Browser` object in the :func:`browser <browser>` fixture.

    Args:
        *args: A list of arguments to forward to the underlying :class:`BrowserSettings` instances.
        **kwargs: The arguments to forward to the underlying :class:`BrowserSettings` instance.

    You can specify browser settings with this decorator as follows:

    .. code-block:: python

        from pytest_django.live_server_helper import LiveServer
        from pytest_logikal.browser import Browser, set_browser


        @set_browser(width=1800, height=900)
        def test_homepage(browser: Browser, live_server: LiveServer) -> None:
            browser.get(live_server.url)
            browser.check()

    You can also run your test in multiple browser environments:

    .. code-block:: python

        from pytest_django.live_server_helper import LiveServer
        from pytest_logikal.browser import Browser, set_browser


        @set_browser(
            dict(name='desktop', width=1800),
            dict(name='mobile', width=600, mobile=True),
        )
        def test_homepage(browser: Browser, live_server: LiveServer) -> None:
            browser.get(live_server.url)
            browser.check()

    """
    argvalues = args or [kwargs]
    for argvalue in argvalues:
        argvalue['name'] = argvalue.get(
            'name', re.sub(r'[{}\[\]\':,]', '', str(argvalue)).replace(' ', '_').lower(),
        )

    def parametrized_test_function(function: Function) -> Any:
        source_file = inspect.getsourcefile(function)
        if not source_file:
            raise RuntimeError(f'Source file cannot be found for "{function}"')
        source_file_path = Path(source_file)

        for argvalue in argvalues:
            argvalue['screenshot_path'] = (
                source_file_path.parent / 'screenshots' / source_file_path.stem / function.__name__
            )

        return pytest.mark.parametrize(
            argnames='browser', argvalues=argvalues, indirect=True, ids=itemgetter('name'),
        )(function)

    return parametrized_test_function
