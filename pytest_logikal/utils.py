from collections.abc import Callable, Generator
from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, TypeVar

from logikal_utils.project import tool_config

from pytest_logikal.core import DEFAULT_INI_OPTIONS

logger = getLogger(__name__)

Function = TypeVar('Function', bound=Callable[..., Any])
Fixture = Callable[[Function], Function]


def get_ini_option(name: str) -> Any:
    ini_options = tool_config('pytest').get('ini_options', {})
    default = DEFAULT_INI_OPTIONS[name]['value']
    return type(default)(ini_options.get(name, default))


@contextmanager
def render_template(path: Path, context: dict[str, Any]) -> Generator[Path]:
    with TemporaryDirectory(prefix='pytest_logikal_', suffix='_template') as tmp_dir:
        rendered = path.read_text(encoding='utf-8').format(**context)
        config_path = Path(tmp_dir) / path.name
        config_path.write_text(rendered)
        yield config_path
