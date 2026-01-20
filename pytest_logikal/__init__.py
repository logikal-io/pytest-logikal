# Depends on the `browser` extra
try:
    from logikal_browser import Browser, scenarios
except ImportError:  # pragma: no cover
    pass

try:
    from pytest_logikal.browser import set_browser
except ImportError:  # pragma: no cover
    pass


# Depends on the `django` extra
try:
    from pytest_logikal.django import LiveURL
except ImportError:  # pragma: no cover
    pass


__all__ = ['Browser', 'scenarios', 'set_browser', 'LiveURL']
