import json
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest

from pytest_logikal.file_checker import (
    BatchFileCheckResult, CachedBatchFileCheckItem, CachedBatchFileCheckPlugin,
)
from pytest_logikal.utils import get_ini_option

PACKAGE_ROOT_PATH = Path(__file__).parent
SUFFIX_CONFIG = {'.js': 'js_config.mjs', '.mjs': 'js_config_module.mjs'}
SEVERITY = {1: 'warning', 2: 'error'}


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('js')
    group.addoption('--js', action='store_true', default=False, help='run js checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'js: checks JS files.')
    if config.option.js:
        config.pluginmanager.register(JSPlugin(config=config))


class JSPlugin(CachedBatchFileCheckPlugin):
    name = 'js'
    item = CachedBatchFileCheckItem

    @staticmethod
    def _config_batch_paths(paths: list[Path]) -> dict[str, list[Path]]:
        config_batch_paths = {
            config: [path for path in paths if path.suffix == suffix]
            for suffix, config in SUFFIX_CONFIG.items()
        }
        return {config: paths for config, paths in config_batch_paths.items() if paths}

    def runtest(
        self, paths: list[Path], workers: int | None,
    ) -> dict[Path, BatchFileCheckResult]:
        results: dict[Path, BatchFileCheckResult] = defaultdict(BatchFileCheckResult)
        for config, batch_paths in self._config_batch_paths(paths=paths).items():
            batch_path_set = set(batch_paths)  # speed up path checking on large projects
            command = [
                'npx', '--prefix', str(PACKAGE_ROOT_PATH), '--no', '--',
                'eslint', *(str(path) for path in batch_paths),
                '--format=json', '--max-warnings=0',
                f'--config={PACKAGE_ROOT_PATH / config}',
                f'--concurrency={workers or 'auto'}',
                f'--rule=max-len: ["error", {get_ini_option('max_line_length')}]',
                f'--rule=complexity: ["error", {get_ini_option('max_complexity')}]',
            ]
            process = subprocess.run(  # nosec
                command, capture_output=True, text=True, check=False,
                cwd=self.config.invocation_params.dir,
            )
            if process.returncode < 0:
                raise RuntimeError(
                    f'ESLint was terminated by signal {-process.returncode}: '
                    f'{process.stderr.strip() or process.stdout.strip() or '(no output)'}'
                )
            try:
                reports = json.loads(process.stdout)
            except json.decoder.JSONDecodeError as error:
                raise RuntimeError((process.stdout or process.stderr).strip()) from error

            for report in reports:
                if (path := Path(report['filePath'])) not in batch_path_set:
                    raise RuntimeError(f'Invalid path: {path}')
                results[path].errors.extend(
                    f'{error['line']}:{error['column']}: {SEVERITY[error['severity']]}: '
                    + f'{error['message']}'
                    + (f' ({error['ruleId']})' if error['ruleId'] else '')
                    for error in report['messages']
                )
        return results

    def check_file(self, file_path: Path) -> bool:
        return file_path.suffix in SUFFIX_CONFIG
