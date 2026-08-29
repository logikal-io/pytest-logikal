import json
import subprocess
from collections import defaultdict
from pathlib import Path

import pytest

from pytest_logikal.file_checker import (
    BatchFileCheckResult, CachedBatchFileCheckItem, CachedBatchFileCheckPlugin,
)
from pytest_logikal.utils import get_ini_option, render_template
from pytest_logikal.validator import Validator

PACKAGE_ROOT_PATH = Path(__file__).parent


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('css')
    group.addoption('--css', action='store_true', default=False, help='run css checks')


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'css: checks CSS files.')
    if config.option.css:
        config.pluginmanager.register(CSSPlugin(config=config))


class CSSPlugin(CachedBatchFileCheckPlugin):
    name = 'css'
    item = CachedBatchFileCheckItem

    def __init__(self, config: pytest.Config):
        super().__init__(config=config)
        self.validator = Validator()

    def runtest(
        self, paths: list[Path], workers: int | None,
    ) -> dict[Path, BatchFileCheckResult]:
        results: dict[Path, BatchFileCheckResult] = defaultdict(BatchFileCheckResult)

        # Validate
        # Note: we had to disable validation due to https://github.com/w3c/css-validator/issues/481
        # for path in paths:
        #     content = path.read_text(encoding='utf-8')
        #     errors = self.validator.errors(content, content_type='text/css')
        #     results[path].errors.extend(
        #         f'{error.first_line}: validation {error.severity}: {error.message}'
        #         for error in errors
        #     )

        # Lint
        # Note: we cannot specify max_line_length via CLI arguments currently
        # (see https://github.com/stylelint/stylelint/issues/6805)
        context = {'max_line_length': get_ini_option('max_line_length')}
        with render_template(PACKAGE_ROOT_PATH / 'css_config.yml', context) as config_path:
            command = [
                'npx', '--no',
                'stylelint', *(str(path) for path in paths), '--formatter', 'json',
                '--config', str(config_path),
            ]
            process = subprocess.run(  # nosec
                command, capture_output=True, text=True, check=False, cwd=PACKAGE_ROOT_PATH,
            )
        if process.returncode < 0:
            raise RuntimeError(
                f'Stylelint was terminated by signal {-process.returncode}: '
                f'{process.stderr.strip() or process.stdout.strip() or '(no output)'}'
            )
        try:
            reports = json.loads(process.stderr)
        except json.decoder.JSONDecodeError as error:
            raise RuntimeError((process.stderr or process.stdout).strip()) from error

        path_set = set(paths)  # speed up path checking on large projects
        for report in reports:
            if (path := Path(report['source'])) not in path_set:
                raise RuntimeError(f'Invalid path: {path}')
            if report['errored']:
                results[path].errors.extend(
                    f'{error['line']}:{error['column']}: {error['severity']}: {error['text']}'
                    for error in report['warnings']
                )
        return results

    def check_file(self, file_path: Path) -> bool:
        return file_path.suffix == '.css'
