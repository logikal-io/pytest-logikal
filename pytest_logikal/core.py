import logging
import os
import shutil
import sys
from importlib.util import find_spec
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import pytest
from termcolor import colored

sys.path.insert(0, os.getcwd())

PLUGINS = {
    'core': [
        'mypy', 'bandit', 'build', 'docs', 'isort', 'licenses', 'pylint', 'requirements', 'style',
    ],
    'django': ['migration', 'translations', 'html', 'css', 'svg', 'js'],
}
DEFAULT_INI_OPTIONS: Dict[str, Any] = {
    'max_line_length': {'value': 99, 'help': 'the maximum line length to use'},
    'max_complexity': {'value': 10, 'help': 'the maximum complexity to allow'},
    'cov_fail_under': {'value': 100, 'help': 'target coverage percentage'},
}
EXTRAS = {
    'black': bool(find_spec('black')),
    'browser': bool(find_spec('selenium')),
    'django': bool(find_spec('pytest_django')),
}

ReportInfoType = Tuple[Union[Any, str], Optional[int], str]


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('logikal')
    group.addoption('--live', action='store_true', help='run live tests')
    group.addoption('--fast', action='store_true', help='do not run any additional checks')
    group.addoption('--clear', action='store_true', help='clear cache before running tests')
    group.addoption('--no-defaults', action='store_true', help='do not use our own defaults')
    group.addoption('--no-mypy', action='store_true', help='do not use mypy')
    group.addoption('--no-bandit', action='store_true', help='do not use bandit')
    group.addoption('--no-build', action='store_true', help='do not run build checks')
    group.addoption('--no-docs', action='store_true', help='do not run documentation checks')
    group.addoption('--no-isort', action='store_true', help='do not use isort')
    group.addoption('--no-licenses', action='store_true', help='do not check licenses')
    group.addoption('--no-pylint', action='store_true', help='do not use pylint')
    group.addoption('--no-requirements', action='store_true', help='do not check requirements')
    group.addoption('--no-style', action='store_true', help='do not use pycodestyle & pydocstyle')
    group.addoption('--no-install', action='store_true', help='do not install packages')

    if EXTRAS['django']:
        group.addoption('--no-migration', action='store_true', help='do not check migrations')
        group.addoption('--no-translations', action='store_true', help='do not check translations')
        group.addoption('--no-html', action='store_true', help='do not run html template checks')
        group.addoption('--no-css', action='store_true', help='do not run css checks')
        group.addoption('--no-svg', action='store_true', help='do not run svg checks')
        group.addoption('--no-js', action='store_true', help='do not run js checks')

    for option, entry in DEFAULT_INI_OPTIONS.items():
        parser.addini(option, default=str(entry['value']), help=entry['help'])


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    # Block uninstalled extra plugins
    for extra, installed in EXTRAS.items():
        if not installed:
            pluginmanager.set_blocked(f'logikal_{extra}')
            for plugin in PLUGINS.get(extra, [extra]):
                pluginmanager.set_blocked(f'logikal_{plugin}')


@pytest.hookimpl(wrapper=True)
def pytest_load_initial_conftests(early_config: pytest.Config, args: List[str]) -> Iterator[None]:
    if '--no-defaults' in args:
        yield

    # Updating arguments
    args.extend(['--strict-config', '--strict-markers'])
    namespace = early_config.known_args_namespace
    if '--live' in args:
        args.append('--capture=no')
        namespace.capture = 'no'
    if '--clear' in args:
        args.append('--cache-clear')
        namespace.cacheclear = True
    if '-r' not in args:
        args.extend(['-r', 'fExX'])
    if '-n' not in args:
        args.extend(['-n', 'auto' if '--live' not in args else '0'])
        namespace.dist = 'load' if '--live' not in args else 'no'
    for plugin in chain(*(plugins for name, plugins in PLUGINS.items() if EXTRAS.get(name, True))):
        if '--fast' not in args and f'--no-{plugin}' not in args:
            args.append(f'--{plugin}')
            setattr(namespace, plugin, True)
    if all(arg not in args for arg in ['--cov', '--no-cov', '--live', '--fast']):
        args.extend(['--cov', '--no-cov-on-fail'])
        namespace.no_cov_on_fail = True

    # Setting coverage options
    if '--cov' in args:
        fail_under = early_config.getini('cov_fail_under')
        namespace.cov_source = ['.']
        namespace.cov_fail_under = float(fail_under) if '.' in fail_under else int(fail_under)
        namespace.cov_report = {'term-missing': 'skip-covered'}

    # Updating config
    ini_defaults: Dict[str, Union[str, List[str]]] = {
        'console_output_style': 'classic',
        'xfail_strict': 'True',
        'filterwarnings': ['error'],
        'log_cli': 'True' if '--live' in args else 'False',
        'log_level': 'DEBUG',
        'log_format': '%(asctime)s.%(msecs)03d %(levelname)s %(message)s (%(name)s:%(lineno)s)',
        'log_date_format': '%Y-%m-%d %H:%M:%S',
        'log_auto_indent': 'True',
    }
    early_config.inicfg = {**ini_defaults, **early_config.inicfg}
    yield


def pytest_sessionstart(session: pytest.Session) -> None:
    # Clearing cache
    if session.config.getoption('clear'):
        print(colored('Clearing cache', 'yellow', attrs=['bold']))
        Path('.coverage').unlink(missing_ok=True)
        shutil.rmtree('.pytest_cache', ignore_errors=True)
        shutil.rmtree('.mypy_cache', ignore_errors=True)


def pytest_configure(config: pytest.Config) -> None:
    # Hiding information
    if not config.getoption('verbose'):
        # Hiding overly verbose debug and info log messages
        logging.getLogger('django_migration_linter').setLevel(logging.WARNING)
        logging.getLogger('docker').setLevel(logging.INFO)
        logging.getLogger('faker').setLevel(logging.INFO)
        logging.getLogger('filelock').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.INFO)
        logging.getLogger('PIL').setLevel(logging.INFO)
        logging.getLogger('pydocstyle').setLevel(logging.WARNING)
        logging.getLogger('pytest_logikal.validator').setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.INFO)
        logging.getLogger('pydocstyle').setLevel(logging.ERROR)
        logging.getLogger('blib2to3').setLevel(logging.WARNING)  # used by Black

        # Hiding worker information lines
        reports = config.pluginmanager.get_plugin('reports')
        reports.getworkerinfoline = lambda *_args, **_kwargs: ''  # type: ignore[union-attr]

    # Configuring mypy
    mypy = config.pluginmanager.get_plugin('mypy')
    mypy.mypy_argv = [  # type: ignore[union-attr]
        '--no-error-summary',
        '--strict',
        '--show-column-numbers',
        '--warn-unreachable',
    ]


def unified_reportinfo(item: pytest.Item, header: str) -> Callable[[], ReportInfoType]:
    def reportinfo() -> ReportInfoType:
        return (item.path, None, header)
    return reportinfo


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    for item in items:
        source = item.nodeid.split('::')[-1].lower()
        if source == 'mypy':
            header = f'[{item.name}] {item.path.relative_to(item.config.invocation_params.dir)}'
            setattr(item, 'reportinfo', unified_reportinfo(item=item, header=header))
        if source == 'mypy-status':
            setattr(item, '_nodeid', '::check::mypy-status')
            setattr(item, 'reportinfo', unified_reportinfo(item=item, header='[mypy-status]'))
