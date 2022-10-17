import json
import subprocess
from pathlib import Path

import pytest

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('bandit')
    group.addoption('--bandit', action='store_true', default=False, help='run bandit')
    parser.addini('bandit_config_file', help='the Bandit configuration file to use')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'bandit: tests checking common security issues.')
    if config.option.bandit:
        config.pluginmanager.register(BanditPlugin(config=config))


class BanditItem(CachedFileCheckItem):
    def run(self) -> None:
        severity = {'LOW': 'warning', 'MEDIUM': 'error', 'HIGH': 'critical'}
        config_file = (
            self.config.getini('bandit_config_file')
            or str(Path(__file__).parent / 'bandit_config.yml')
        )
        command = [
            'bandit', '--configfile', config_file, '--quiet', '--format', 'json', str(self.path),
        ]

        # This subprocess call is secure as it is not using untrusted input
        process = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec
        try:
            report = json.loads(process.stdout)
            if report.get('results'):
                raise ItemRunError('\n\n'.join(
                    f'{error["line_number"]}:{error["col_offset"]}: '
                    f'{severity[error["issue_severity"]]}: {error["issue_text"]} '
                    f'({error["test_id"]}: {error["test_name"]}, '
                    f'confidence: {error["issue_confidence"].lower()})\n'
                    f'More info: {error["more_info"]}'
                    for error in report['results']
                ))
        except json.decoder.JSONDecodeError as error:
            raise ItemRunError(f'Error: {process.stdout or process.stderr}') from error


class BanditPlugin(CachedFileCheckPlugin):
    name = 'bandit'
    item = BanditItem
