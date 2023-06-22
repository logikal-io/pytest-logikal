import shutil
import subprocess
from pathlib import Path

import pytest
from logikal_utils.project import PYPROJECT

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('build')
    group.addoption('--build', action='store_true', default=False, help='run build checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'build: tests package building.')
    if config.option.build:
        config.pluginmanager.register(BuildPlugin(config=config))


class BuildItem(CachedFileCheckItem):
    def run(self) -> None:
        # Deleting existing distributions
        shutil.rmtree('dist', ignore_errors=True)

        # Checking build process
        process = subprocess.run(  # nosec: secure, not using untrusted input
            ['python3', '-m', 'build', '--sdist', '--wheel'],
            capture_output=True, text=True, check=False,
        )
        errors = (process.stderr or process.stdout) if process.returncode else process.stderr
        cleaned_errors = [
            error for error in (errors.strip().split('\n') if errors else [])
            # Remove unnecessary warnings from output
            if '_BetaConfiguration' not in error
            and 'warnings.warn(' not in error
            and 'shallow and may cause errors' not in error
            and 'config = read_configuration' not in error
        ]
        if cleaned_errors:
            raise ItemRunError('\n'.join(cleaned_errors))

        # Checking distribution
        process = subprocess.run(  # nosec: secure, not using untrusted input
            ['twine', 'check', '--strict', 'dist/*'], capture_output=True, text=True, check=False,
        )
        if process.returncode:
            raise ItemRunError(process.stdout or process.stderr)


class BuildPlugin(CachedFileCheckPlugin):
    name = 'build'
    item = BuildItem

    def check_file(self, file_path: Path) -> bool:
        if file_path.relative_to(self.config.invocation_params.dir) == Path('pyproject.toml'):
            return 'build-system' in PYPROJECT
        return False
