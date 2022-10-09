import logging
import os
import shutil
import sys
from importlib.util import find_spec
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Tuple, Union

import pytest
import tomli

sys.path.insert(0, os.getcwd())

PYPROJECT = (
    tomli.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
    if Path('pyproject.toml').exists() else {}
)
PLUGINS = ['mypy', 'bandit', 'build', 'isort', 'licenses', 'pylint', 'requirements', 'style']

ReportInfoType = Tuple[Union[os.PathLike, str], Optional[int], str]


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('logikal')
    group.addoption('--live', action='store_true', help='run live tests')
    group.addoption('--clear', action='store_true', help='clear cache before running tests')
    group.addoption('--no-defaults', action='store_true', help='do not use our own defaults')
    group.addoption('--no-mypy', action='store_true', help='do not use mypy')
    group.addoption('--no-bandit', action='store_true', help='do not use bandit')
    group.addoption('--no-build', action='store_true', help='do not run build checks')
    group.addoption('--no-isort', action='store_true', help='do not use isort')
    group.addoption('--no-licenses', action='store_true', help='do not check licenses')
    group.addoption('--no-pylint', action='store_true', help='do not use pylint')
    group.addoption('--no-requirements', action='store_true', help='do not check requirements')
    group.addoption('--no-style', action='store_true', help='do not use pycodestyle & pydocstyle')
    parser.addini('max_line_length', default='99', help='the maximum line length to use')
    parser.addini('cov_fail_under', default='100', help='target coverage percentage')


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    if not find_spec('pytest_django'):
        pluginmanager.set_blocked('logikal_django')


# Untyped decorator (see https://github.com/pytest-dev/pytest/issues/7469)
@pytest.hookimpl(hookwrapper=True)  # type: ignore[misc]
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
    for plugin in PLUGINS:
        if f'--no-{plugin}' not in args:
            args.append(f'--{plugin}')
            setattr(namespace, plugin, True)
    if '--no-cov' not in args and '--live' not in args and '--cov' not in args:
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


def pytest_configure(config: pytest.Config) -> None:
    # Clearing cache
    if config.getoption('clear'):
        print('Clearing cache')
        Path('.coverage').unlink(missing_ok=True)
        shutil.rmtree('.pytest_cache', ignore_errors=True)
        shutil.rmtree('.mypy_cache', ignore_errors=True)

    # Hiding overly verbose debug and info log messages
    logging.getLogger('faker').setLevel(logging.INFO)
    logging.getLogger('filelock').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.INFO)
    logging.getLogger('pydocstyle').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.INFO)

    # Hiding worker information lines
    if not config.getoption('verbose'):
        config.pluginmanager.get_plugin('reports').getworkerinfoline = lambda *_args, **_kwargs: ''

    # Configuring mypy
    mypy = config.pluginmanager.get_plugin('mypy')
    mypy.mypy_argv = [
        '--no-error-summary',
        '--strict',
        '--show-column-numbers',
        '--show-error-codes',
        '--warn-unreachable',
    ]


def unified_reportinfo(item: pytest.Item, header: str) -> Callable[[], ReportInfoType]:
    def reportinfo() -> ReportInfoType:
        return (item.path, None, header)
    return reportinfo


# Untyped decorator (see https://github.com/pytest-dev/pytest/issues/7469)
@pytest.hookimpl(trylast=True)  # type: ignore[misc]
def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    for item in items:
        source = item.nodeid.split('::')[-1].lower()
        if source == 'mypy':
            header = f'[{item.name}] {item.path.relative_to(item.config.invocation_params.dir)}'
            setattr(item, 'reportinfo', unified_reportinfo(item=item, header=header))
        if source == 'mypy-status':
            setattr(item, 'reportinfo', unified_reportinfo(item=item, header='[mypy-status]'))
