Fixtures
========

mocker
------
The default installation provides the :doc:`mocker <pytest_mock:usage>` fixture via `pytest-mock
<https://pytest-mock.readthedocs.io/>`_.

browser
-------
The :ref:`browser extra <index:browser>` provides a new
:func:`browser <pytest_logikal.browser.browser>` fixture:

.. autofunction:: pytest_logikal.browser.browser

Browser settings must be specified via the :func:`~pytest_logikal.browser.set_browser` decorator:

.. autodecorator:: pytest_logikal.browser.set_browser

You can specify browser scenarios with this decorator as follows:

.. literalinclude:: ../tests/pytest_logikal/docs_examples/test_single_scenario.py
   :language: python

You can also run your test in multiple scenarios:

.. literalinclude:: ../tests/pytest_logikal/docs_examples/test_multiple_scenarios.py
   :language: python

live_url
--------
The :ref:`django extra <index:django>` provides a new :func:`live_url
<pytest_logikal.django.live_url>` fixture:

.. autofunction:: pytest_logikal.django.live_url

language
--------
The :ref:`django extra <index:django>` also provides the :func:`language
<pytest_logikal.django.language>` fixture:

.. autofunction:: pytest_logikal.django.language

You may control the language for a specific test with the :func:`set_language
<pytest_logikal.django.set_language>` or :func:`all_languages
<pytest_logikal.django.all_languages>` decorators:

.. autodecorator:: pytest_logikal.django.set_language
.. autodecorator:: pytest_logikal.django.all_languages

timezone
--------
The :ref:`django extra <index:django>` also provides the :func:`timezone
<pytest_logikal.django.timezone>` fixture:

.. autofunction:: pytest_logikal.django.timezone

You may control the time zone for a specific test with the :func:`set_timezone
<pytest_logikal.django.set_timezone>` decorator:

.. autodecorator:: pytest_logikal.django.set_timezone
