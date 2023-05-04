import sys

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]
intersphinx_mapping = {
    'python': (f'https://docs.python.org/{sys.version_info[0]}.{sys.version_info[1]}', None),
    # For these libraries only the "latest" version is published
    'pytest_mock': ('https://pytest-mock.readthedocs.io/en/latest/', None),
    'pytest_django': ('https://pytest-django.readthedocs.io/en/latest/', None),
    'selenium': ('https://www.selenium.dev/selenium/docs/api/py/', None),
}
nitpick_ignore = [
    ('py:class', 'pytest_django.live_server_helper.LiveServer'),
]
