import json
import subprocess
from pathlib import Path

import pytest

from pytest_logikal.file_checker import CachedFileCheckItem, CachedFileCheckPlugin
from pytest_logikal.plugin import ItemRunError
from pytest_logikal.utils import get_ini_option


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('js')
    group.addoption('--js', action='store_true', default=False, help='run js checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'js: checks JS files.')
    if config.option.js:
        config.pluginmanager.register(JSPlugin(config=config))


class JSItem(CachedFileCheckItem):
    def run(self) -> None:
        command = [
            'npx', '--no',
            'eslint', str(self.path), '--format', 'json', '--max-warnings', '0',
            '--config', str(Path(__file__).parent / 'js_config.yml'),
            '--rule', f'max-len: [error, {get_ini_option("max_line_length")}]',
            '--rule', f'complexity: [error, {get_ini_option("max_complexity")}]',
        ]
        process = subprocess.run(  # nosec
            command, capture_output=True, text=True, check=False, cwd=Path(__file__).parent,
        )
        try:
            severity = {1: 'warning', 2: 'error'}
            report = json.loads(process.stdout)[0]
            if report['messages']:
                raise ItemRunError('\n'.join(
                    f'{error["line"]}:{error["column"]}: {severity[error["severity"]]}: '
                    + f'{error["message"]}'
                    + (f' ({error["ruleId"]})' if error['ruleId'] else '')
                    for error in report['messages']
                ))
        except json.decoder.JSONDecodeError as error:
            raise ItemRunError((process.stdout or process.stderr).strip()) from error


class JSPlugin(CachedFileCheckPlugin):
    name = 'js'
    item = JSItem

    def check_file(self, file_path: Path) -> bool:
        return file_path.suffix == '.js'
