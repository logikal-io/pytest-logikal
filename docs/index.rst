.. toctree::
    :caption: Documentation
    :hidden:

    self
    fixtures
    development
    license

.. toctree::
    :caption: External Links
    :hidden:

    Release Notes <https://github.com/logikal-io/pytest-logikal/releases>
    Issue Tracker <https://github.com/logikal-io/pytest-logikal/issues>
    Source Code <https://github.com/logikal-io/pytest-logikal>

Getting Started
===============
.. contents::
    :local:
    :depth: 1

Introduction
------------
The pytest-logikal package provides an improved `pytest <https://docs.pytest.org/>`_ environment
which automatically runs a broad range of checks:

- Typing checks (via `mypy <http://www.mypy-lang.org/>`_
  and `pytest-mypy <https://github.com/dbader/pytest-mypy>`_)
- Linting (via `Pylint <https://pylint.pycqa.org/>`_)
- Code style checks (via `isort <https://pycqa.github.io/isort/>`_,
  `pycodestyle <https://pycodestyle.pycqa.org/>`_ and `pydocstyle <http://www.pydocstyle.org/>`_)
- Coverage checks (via `coverage.py <https://coverage.readthedocs.io/>`_
  and `pytest-cov <https://pytest-cov.readthedocs.io/>`_)
- Security checks (via `Bandit <https://bandit.readthedocs.io/>`_)
- License checks (via `pip-licenses <https://github.com/raimon49/pip-licenses>`_)
- Requirements lockfile checks (via `pyorbs <https://pyorbs.readthedocs.io/>`_)
- Package build checks (when applicable)

The checks are configured to be strict, and all checks and tests are distributed across multiple
CPUs by default (via `pytest-xdist <https://pytest-xdist.readthedocs.io/>`_).

Installation
------------
You can simply install ``pytest-logikal`` from `pypi <https://pypi.org/project/pytest-logikal/>`_:

.. code-block:: shell

    pip install pytest-logikal

In addition to providing an opinionated default configuration, it also makes the output of the
various pytest plugins more consistent.

Extras
------
browser
~~~~~~~
The ``browser`` extra installs `Selenium <https://www.selenium.dev/>`_ and provides the
:func:`browser <pytest_logikal.browser.browser>` fixture for convenient browser automation in
tests:

.. code-block:: shell

    pip install pytest-logikal[browser]

django
~~~~~~
You may also use the ``django`` extra to install the necessary packages, plugins and fixtures for
testing Django projects:

.. code-block:: shell

    pip install pytest-logikal[django]

This will additionally install and configure
`django-stubs <https://github.com/typeddjango/django-stubs>`_,
`pylint-django <https://github.com/PyCQA/pylint-django>`_,
`pytest-django <https://pytest-django.readthedocs.io/>`_
and `pytest-factoryboy <https://github.com/pytest-dev/pytest-factoryboy>`_.

When using the ``django`` extra you must also specify the Django settings module and mypy plugin
path in your ``pyproject.toml`` file as follows:

.. code-block:: toml

    [tool.pytest.ini_options]
    DJANGO_SETTINGS_MODULE = 'project.settings.testing'

    [tool.mypy]
    plugins = ['mypy_django_plugin.main']

Configuration
-------------
You shall not change the standard, default configuration when working on Logikal software.
Nonetheless, regular configuration options for the various tools in the ``pyproject.toml`` file
will be typically respected. Additionally, you can extend the allowed licenses and packages for
the license checker plugin as follows:

.. code-block:: toml

    [tool.licenses]
    extend_allowed_licenses = ['Allowed License']

    [tool.licenses.extend_allowed_packages]
    package = 'Package License'

You can also override the default licenses and packages (instead of extending them) via the
``tool.licenses.allowed_licenses`` and ``tool.licenses.allowed_packages`` options.
