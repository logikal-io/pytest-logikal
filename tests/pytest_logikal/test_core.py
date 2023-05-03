from itertools import chain
from pathlib import Path
from shutil import copy
from typing import Callable, List, Tuple

import pytest
from pytest_mock.plugin import MockerFixture

from pytest_logikal import core

pytest_plugins = ['pytester']
PYTEST_ARGS = [
    '--assert', 'plain',  # modules are already imported so assertions cannot be rewritten
    '--no-licenses',  # no need to check licenses here again
    '--no-install',  # do not install packages
    '-p', 'no:django', '--no-djlint',  # settings module is not available
]


def test_run_errors(makepyfile: Callable[[str], Path], pytester: pytest.Pytester) -> None:
    pytester.makepyprojecttoml("[project]\nname = 'pytest-logikal'")
    makepyfile("""
        import pickle  # triggers a bandit error
        import re  # triggers a pylint error
        import os  # triggers an isort error

        # triggers a pycodestyle error (single blank line)
        def test_errors() -> None:
            '''Invalid docstring quotes.'''  # triggers a pydocstyle error
            test: int = 'invalid'  # triggers a mypy error
    """)
    result = pytester.runpytest('--clear', *PYTEST_ARGS)
    result.stdout.re_match_lines_random([
        r'.*\[bandit\] test_run_errors\.py.*',
        r'.*\[pylint\] test_run_errors\.py.*',
        r'.*\[isort\] test_run_errors\.py.*',
        r'.*\[style\] test_run_errors\.py.*',
        r'.*\[mypy\] test_run_errors\.py.*',
        r'.*\[mypy-status\].*',
    ])
    result.stdout.no_re_match_line(r'.*\(filelock:\d+\)')
    result.stdout.no_re_match_line('.*coverage: platform.*')
    assert result.parseoutcomes() == {'failed': 6, 'passed': 1}


def test_run_success(makepyfile: Callable[[str], Path], pytester: pytest.Pytester) -> None:
    pytester.makepyprojecttoml("[project]\nname = 'pytest-logikal'")
    makepyfile("""
        def test_success() -> None:
            \"\"\"A test that will succeed.\"\"\"
    """)
    result = pytester.runpytest(*PYTEST_ARGS)
    result.stdout.re_match_lines_random(['.*coverage: platform.*'])
    assert result.parseoutcomes() == {'passed': 7}

    # Running the tests again skips file-based checks
    result = pytester.runpytest('-v', *PYTEST_ARGS)
    result.stdout.re_match_lines_random([
        r'.*SKIPPED test_run_success.py::bandit',
        r'.*SKIPPED test_run_success.py::isort',
        r'.*SKIPPED test_run_success.py::pylint',
        r'.*SKIPPED test_run_success.py::style',
    ])
    assert result.parseoutcomes() == {'passed': 3, 'skipped': 4}


def test_clear(mocker: MockerFixture) -> None:
    path = mocker.patch('pytest_logikal.core.Path')
    shutil = mocker.patch('pytest_logikal.core.shutil')

    config = mocker.Mock()
    config.getoption.return_value = True
    core.pytest_configure(config)

    assert path.return_value.unlink.called
    assert shutil.rmtree.called


def test_install_packages(tmp_path: Path) -> None:
    for file in ['package.json', 'package-lock.json']:
        copy(Path(core.__file__).parent / file, tmp_path)
    core.install_packages(node_prefix=tmp_path)
    assert (tmp_path / 'node_modules/stylelint').exists()


def test_run_without_extras(pytester: pytest.Pytester, mocker: MockerFixture) -> None:
    args = PYTEST_ARGS + ['--no-cov']  # avoids coverage "no data to report" warning
    find_spec = mocker.patch('pytest_logikal.core.find_spec')

    find_spec.side_effect = lambda module: module != 'selenium'  # selenium extra missing
    result = pytester.runpytest(*args)
    assert result.parseoutcomes() == {}

    find_spec.side_effect = lambda module: module != 'pytest_django'  # django extra missing
    result = pytester.runpytest(*args, *[f'--no-{plugin}' for plugin in core.PLUGINS['django']])
    assert result.parseoutcomes() == {}


def load_initial_conftests(
    early_config: pytest.Config, args: List[str],
) -> Tuple[pytest.Config, List[str]]:
    next(core.pytest_load_initial_conftests(early_config, args))
    return early_config, args


def test_defaults(mocker: MockerFixture) -> None:
    early_inicfg = {'log_level': 'INFO', 'cov_fail_under': '100'}
    config = mocker.Mock(inicfg=early_inicfg)
    config.getini = early_inicfg.get
    early_config, args = load_initial_conftests(early_config=config, args=[])
    assert args == [
        '--strict-config', '--strict-markers', '-r', 'fExX', '-n', 'auto',
        *[f'--{plugin}' for plugin in chain.from_iterable(core.PLUGINS.values())],
        '--cov', '--no-cov-on-fail',
    ]
    assert early_config.inicfg['log_level'] == 'INFO'
    assert early_config.inicfg['console_output_style'] == 'classic'


def test_no_defaults(mocker: MockerFixture) -> None:
    early_config = mocker.Mock()
    early_config, args = load_initial_conftests(early_config, ['--no-defaults'])
    assert args == ['--no-defaults']
    assert not early_config.called


def test_live(mocker: MockerFixture) -> None:
    _, args = load_initial_conftests(mocker.Mock(inicfg={}), ['--live'])
    assert args == [
        '--live', '--strict-config', '--strict-markers', '--capture=no', '-r', 'fExX', '-n', '0',
        *[f'--{plugin}' for plugin in chain.from_iterable(core.PLUGINS.values())],
    ]


def test_fast(mocker: MockerFixture) -> None:
    _, args = load_initial_conftests(mocker.Mock(inicfg={}), ['--fast'])
    assert all(f'--{plugin}' not in args for plugin in chain.from_iterable(core.PLUGINS.values()))
