# Depends on the `browser` extra
try:
    from logikal_browser import Browser, scenarios
except ImportError:
    pass

try:
    from pytest_logikal.browser import set_browser
except ImportError:
    pass


# Depends on the `django` extra
try:
    from pytest_logikal.django import LiveURL
except ImportError:
    pass


__all__ = ['Browser', 'scenarios', 'set_browser', 'LiveURL']
