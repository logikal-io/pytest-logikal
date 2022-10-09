import sys

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]
intersphinx_mapping = {
    'python': (f'https://docs.python.org/{sys.version_info[0]}.{sys.version_info[1]}', None),
    'pytest_mock': ('https://pytest-mock.readthedocs.io/en/latest/', None),
    'selenium': ('https://www.selenium.dev/selenium/docs/api/py/', None),
}
