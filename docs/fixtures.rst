Fixtures
========

mocker
------
The default installation provides the :doc:`mocker <pytest_mock:usage>` fixture via `pytest-mock
<https://pytest-mock.readthedocs.io/>`_.

browser
-------
The :ref:`browser extra <index:browser>` provides a new :func:`browser
<pytest_logikal.browser.browser>` fixture:

.. autofunction:: pytest_logikal.browser.browser()
.. autoclass:: pytest_logikal.browser.Browser()
.. autoclass:: pytest_logikal.browser.BrowserSettings

You may control browser settings for a specific test with the
:func:`~pytest_logikal.browser.set_browser` decorator:

.. autodecorator:: pytest_logikal.browser.set_browser
