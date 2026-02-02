import tomllib
from datetime import datetime
from pathlib import Path
from time import sleep

from pytest import Pytester
from time_machine import Traveller

from tests.pytest_logikal.conftest import append_newline
from tests.pytest_logikal.test_core import PYTEST_ARGS, generate_pyproject_toml

PYPROJECT_FROZEN_TIMESTAMP = datetime(2025, 1, 25, 14, 30, 55)


def test_frozen_time(frozen_timestamp: datetime, frozen_time: Traveller) -> None:
    assert frozen_timestamp == PYPROJECT_FROZEN_TIMESTAMP
    assert datetime.now() == frozen_timestamp
    destination_time = datetime(2025, 1, 28, 11, 22, 33)
    frozen_time.move_to(destination_time)
    assert datetime.now() == destination_time
    sleep(1)
    assert datetime.now() == destination_time


def test_frozen_time_no_config(pytester: Pytester) -> None:
    # Time is the current time
    pytester.makepyprojecttoml(generate_pyproject_toml())
    append_newline(pytester.makepyfile("""
        from datetime import datetime

        def test_frozen_time() -> None:
            assert datetime.now() > datetime(2025, 1, 30)
    """))
    result = pytester.runpytest_subprocess('--fast', *PYTEST_ARGS)
    assert result.parseoutcomes() == {'passed': 1}


def test_frozen_time_config(pytester: Pytester) -> None:
    # Time is the configured time
    pyproject = (Path(__file__).parent / 'docs_examples/pyproject_frozen_time.toml').read_text()
    tool_config = tomllib.loads(pyproject)['tool']
    pytester.makepyprojecttoml(generate_pyproject_toml(tool_config=tool_config))
    append_newline(pytester.makepyfile("""
        from datetime import datetime

        def test_frozen_time() -> None:
            assert datetime.now() == datetime(1985, 10, 26, 1, 20, 42)
    """))
    result = pytester.runpytest_subprocess('--fast', *PYTEST_ARGS)
    assert result.parseoutcomes() == {'passed': 1}
