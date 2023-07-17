# pylint: disable=import-outside-toplevel
import inspect
import logging
import re
from contextlib import contextmanager
from importlib import import_module
from operator import itemgetter
from pathlib import Path
from time import sleep
from typing import Any, Dict, Iterable, Iterator, Optional, TypeVar, Union, cast

import pytest
from logikal_utils.project import PYPROJECT
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome

from pytest_logikal.utils import Fixture, Function, assert_image_equal

logger = logging.getLogger(__name__)

Setting = TypeVar('Setting')


class BrowserSettings:  # pylint: disable=too-many-instance-attributes
    UNLIMITED_HEIGHT = 'unlimited'
    FRAME_HEIGHT = 'frame'

    # Note: make sure to update the docstring of the set_browser fixture when changing the defaults
    DEFAULTS = {
        'desktop': {'width': 1800, 'frame_height': 900},  # 1920x1080 -dash -scrollbar -header
        'laptop-l': {'width': 1440, 'frame_height': 900},
        'laptop': {'width': 1024, 'frame_height': 768},
        'tablet': {'width': 768, 'frame_height': 1024, 'mobile': True},
        'mobile-l': {'width': 425, 'frame_height': 680, 'mobile': True},
        'mobile-m': {'width': 375, 'frame_height': 600, 'mobile': True},
        'mobile-s': {'width': 320, 'frame_height': 512, 'mobile': True},
    }

    def __init__(  # pylint: disable=too-many-arguments
        self,
        setting: Optional[str] = 'desktop',
        name: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[Union[int, str]] = None,
        frame_height: Optional[int] = None,
        mobile: Optional[bool] = None,
    ):
        """
        Browser settings data.

        Args:
            setting: The named setting to use.
            name: The name to use for screenshots. Defaults to the setting name.
            width: The width of the browser window.
            height: The height of the browser window (use 'unlimited' for unlimited and 'frame' to
                use the frame height). Defaults to 'unlimited'.
            frame_height: The browser window frame height to use when taking 'unlimited'
                screenshots.
            mobile: Whether it is a mobile browser. Defaults to :data:`False`.

        """
        pyproject_settings = PYPROJECT.get('tool', {}).get('browser', {}).get('settings', {})
        settings = {**self.DEFAULTS, **pyproject_settings}
        if setting and setting not in settings:
            raise ValueError(f'Unknown browser setting "{setting}"')
        self.settings = settings[setting] if setting else {}
        self.setting = setting
        self.name = name or setting
        self.width = self._setting(width, 'width')

        self.height = self._setting(height, 'height', self.UNLIMITED_HEIGHT)
        regular_height = self.height not in (self.UNLIMITED_HEIGHT, self.FRAME_HEIGHT)
        self.frame_height = self._setting(frame_height, 'frame_height',
                                          default=self.height if regular_height else None)
        self.browser_height = self.height if regular_height else self.frame_height

        self.mobile = self._setting(mobile, 'mobile', False)

    def _setting(
        self, value: Optional[Setting], name: str, default: Optional[Setting] = None,
    ) -> Setting:
        setting = value if value is not None else self.settings.get(name, default)
        if default is None and setting is None:
            raise ValueError(f'The browser setting "{name}" must be specified')
        return setting  # type: ignore

    def __str__(self) -> str:
        attributes = ['setting', 'name', 'width', 'height', 'frame_height', 'mobile']
        settings = ', '.join(f'{name!r}: {getattr(self, name)!r}' for name in attributes)
        return f'{{{settings}}}'


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
        <selenium.webdriver.chrome.webdriver>` instance.
        """
        self.temp_path = temp_path
        self.settings = settings or BrowserSettings()
        logger.debug(f'Browser settings: {self.settings}')
        self.name = self.settings.name
        self.screenshot_path = screenshot_path
        logger.debug(f'Using screenshot path "{self.screenshot_path}"')

        options = cast(Any, ChromeOptions())  # add_argument is not yet typed
        if self.settings.mobile:
            options.add_argument('--hide-scrollbars')
        options.add_argument('--headless')
        options.add_argument(f'--window-size={self.settings.width},{self.settings.browser_height}')
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
    def auto_height(self, wait_milliseconds: Optional[int]) -> Iterator[None]:
        if self.settings.height != BrowserSettings.UNLIMITED_HEIGHT:
            yield
            return
        logger.debug('Using full page height')
        original_size = self.driver.get_window_size()
        if wait_milliseconds:  # we use a small delay to mitigate height flakiness
            logger.debug(f'Waiting {wait_milliseconds} ms')
            sleep(wait_milliseconds / 1000)
        elements = [
            'document.body.clientHeight',
            'document.body.scrollHeight',
            'document.body.offsetHeight',
            'document.documentElement.clientHeight',
            'document.documentElement.scrollHeight',
            'document.documentElement.offsetHeight',
        ]
        script = f'return Math.max({",".join(elements)});'
        height = self.driver.execute_script(script)  # type: ignore[no-untyped-call]
        logger.debug(f'Calculated page height: {height}')
        self.driver.set_window_size(original_size['width'], height)
        try:
            yield
        finally:
            self.driver.set_window_size(**original_size)

    def check(self, name: Optional[str] = None, wait_milliseconds: Optional[int] = 100) -> None:
        """
        Create a screenshot and check it against an expected version.

        Args:
            name: The name of the expected screenshot.
            wait_milliseconds: The milliseconds to wait before calculating the screenshot height
                for unlimited height checks.

        """
        name_parts = [self.screenshot_path.name, self.name, name]
        full_name = '_'.join(part for part in name_parts if part is not None)
        expected = self.screenshot_path.with_name(full_name).with_suffix('.png')

        script = 'document.body.style.caretColor = "transparent";'  # hide the blinking caret
        self.driver.execute_script(script)  # type: ignore[no-untyped-call]

        with self.auto_height(wait_milliseconds=wait_milliseconds):
            logger.debug('Taking screenshot')
            # Note: we are disabling debug remote logs because they contain the verbose image data
            logging.getLogger('selenium.webdriver.remote').setLevel(logging.INFO)
            screenshot = self.driver.get_screenshot_as_png()
            logging.getLogger('selenium.webdriver.remote').setLevel(logging.DEBUG)
        assert_image_equal(actual=screenshot, expected=expected, temp_path=self.temp_path)

    def login(self, user: Any, force: bool = True) -> None:
        """
        .. note:: The ``django`` extra must be installed for this method to work.

        Log in a given user.

        Args:
            user: The user to log in.
            force: Whether to log the user in without going through the authentication steps.

        """
        try:
            from django.conf import settings
            from django.contrib.auth import login as django_auth_login
            from django.http import HttpRequest
        except ImportError as error:  # pragma: no cover
            raise RuntimeError('The `django` extra must be installed for login to work') from error
        if not force:
            raise NotImplementedError('Only the forced login is implemented currently')

        request = HttpRequest()
        request.session = import_module(settings.SESSION_ENGINE).SessionStore()
        django_auth_login(request, user)
        request.session.save()
        self.driver.add_cookie({
            'name': settings.SESSION_COOKIE_NAME,
            'value': request.session.session_key,
        })


@pytest.fixture
def browser(tmp_path: Path, request: Any) -> Iterable[Browser]:  # noqa: D400,D402,D415
    """
    browser() -> Browser

    Yield a :class:`Browser` instance.
    """
    function = request.node.obj
    if not (source_file := inspect.getsourcefile(function)):  # pragma: no cover, defensive line
        raise RuntimeError(f'Source file cannot be found for "{function}"')
    source_path = Path(source_file)
    screenshots = source_path.parent / 'screenshots' / source_path.stem / function.__name__

    settings = BrowserSettings(**getattr(request, 'param', {}))
    with Browser(temp_path=tmp_path, settings=settings, screenshot_path=screenshots) as instance:
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


        @set_browser(setting='tablet')
        def test_homepage(browser: Browser, live_server: LiveServer) -> None:
            browser.get(live_server.url)
            browser.check()

    The currently available settings are the following:

    ========  =====  =========  =====  ======
    Setting   Width   Height    Frame  Mobile
    ========  =====  =========  =====  ======
    desktop   1800   unlimited    900  False
    laptop-l  1440   unlimited    900  False
    laptop    1024   unlimited    768  False
    tablet     768   unlimited   1024  True
    mobile-l   425   unlimited    680  True
    mobile-m   375   unlimited    600  True
    mobile-s   320   unlimited    512  True
    ========  =====  =========  =====  ======

    You can also run your test in multiple browser environments:

    .. code-block:: python

        @set_browser(
            dict(setting='desktop'),
            dict(setting='mobile'),
        )
        def test_homepage(browser: Browser, live_server: LiveServer) -> None:
            browser.get(live_server.url)
            browser.check()

    The named settings can be overridden or extended via the ``tool.browser.settings`` table in
    ``pyproject.toml``:

    .. code-block:: toml

        [tool.browser.settings]
        desktop = {width = 1024, height = 768}
        mobile-xl = {width = 480, frame_height = 768, mobile = true}

    You can then use your custom named setting as follows:

    .. code-block:: python

        @set_browser(setting='mobile-xl')
        def test_homepage(browser: Browser, live_server: LiveServer) -> None:
            browser.get(live_server.url)
            browser.check()

    While we recommend using named settings, you can also use completely arbitrary settings for a
    test as follows:

    .. code-block:: python

        @set_browser(name='laptop-xl', width=1920, height=1080)
        def test_homepage(browser: Browser, live_server: LiveServer) -> None:
            browser.get(live_server.url)
            browser.check()

    """
    argvalues = args or [kwargs]

    def test_id(argvalue: Dict[str, Any]) -> str:
        if 'name' in argvalue and (value := argvalue['name']):
            return str(value)
        if 'setting' in argvalue and len(argvalue) == 1 and (value := argvalue['setting']):
            return str(value)
        return re.sub(r'[{}\[\]\':,]', '', str(argvalue)).replace(' ', '_').lower()

    def parametrized_test_function(function: Function) -> Any:
        for argvalue in argvalues:
            argvalue['name'] = test_id(argvalue)
        return pytest.mark.parametrize(
            argnames='browser', argvalues=argvalues, indirect=True, ids=itemgetter('name'),
        )(function)

    return parametrized_test_function
