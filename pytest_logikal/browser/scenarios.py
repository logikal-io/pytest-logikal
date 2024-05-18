from dataclasses import dataclass
from typing import Iterable, Optional, Union


@dataclass
class Settings:
    """
    Browser settings specification.

    Args:
        name: Name of the settings.
        width: Browser window width.
        height: Browser window height.
        full_page_height: Whether to use the full page height for screenshots.
        mobile: Whether it is a mobile browser.

    """
    name: str
    width: int
    height: int
    full_page_height: bool = True
    mobile: bool = False


@dataclass
class Scenario:
    """
    Browser scenario specification.

    Args:
        settings: Settings to use.
        browsers: Browsers to use. Defaults to using all registered browser versions.

    """
    settings: Union[Settings, Iterable[Settings]]
    browsers: Optional[Iterable[str]] = None


desktop_4k = Scenario(Settings('desktop_4k', width=2560, height=1440))  #:
desktop = Scenario(Settings(
    'desktop',
    width=1920 - 120,  # offset for e.g. top bar, bottom bar, dash bar, task bar
    height=1080 - 180,  # offset for e.g. dash bar
))  #:
laptop_l = Scenario(Settings('laptop_l', width=1440, height=900))  #:
laptop = Scenario(Settings('laptop', width=1024, height=768))  #:
tablet = Scenario(Settings('tablet', width=768, height=1024, mobile=True))  #:
mobile_l = Scenario(Settings('mobile_l', width=425, height=680, mobile=True))  #:
mobile_m = Scenario(Settings('mobile_m', width=375, height=600, mobile=True))  #:
mobile_s = Scenario(Settings('mobile_s', width=320, height=512, mobile=True))  #:
