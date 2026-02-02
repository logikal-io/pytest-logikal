# pylint: disable=redefined-outer-name
from collections.abc import Iterator
from datetime import datetime
from logging import getLogger

import time_machine
from logikal_utils.project import tool_config
from pytest import Parser, fixture

FROZEN_TIMESTAMP = tool_config('pytest').get('frozen_time')
FROZEN_TIME = bool(FROZEN_TIMESTAMP)

time_machine.naive_mode = time_machine.NaiveMode.LOCAL

logger = getLogger(__name__)


def pytest_addoption(parser: Parser) -> None:
    parser.addini('frozen_time', 'the frozen timestamp to use')


@fixture(scope='session')
def frozen_timestamp() -> datetime:
    """
    Return the frozen timestamp.

    The frozen timestamp can be set under the ``frozen_time`` value in the ``tool.pytest`` section
    of ``pyproject.toml``. It must be in ``%Y-%m-%d %H:%M:%S`` format. When the frozen timestamp is
    not configured, it defaults to the current timestamp generated at session startup.
    """
    if FROZEN_TIMESTAMP:
        return datetime.strptime(FROZEN_TIMESTAMP, '%Y-%m-%d %H:%M:%S')
    return datetime.now()  # pragma: no cover, tested in subprocess


@fixture(autouse=FROZEN_TIME)
def frozen_time(
    frozen_timestamp: datetime,
) -> Iterator[time_machine.Traveller]:  # noqa: D400, D402, D415
    """
    frozen_time() -> time_machine.Traveller

    Freeze time and return a traveller instance for managing time.

    Automatically applied to each test when a frozen timestamp has been configured.
    """
    logger.debug(f'Setting the time to "{frozen_timestamp}"')
    with time_machine.travel(destination=frozen_timestamp, tick=False) as traveller:
        yield traveller
