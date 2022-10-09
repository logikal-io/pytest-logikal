from typing import Any

import pytest
from mypy_django_plugin import config as mypy_django_plugin_config


def pytest_configure(config: pytest.Config) -> None:
    # Patching django-stubs
    def parse_toml_file(self: Any, *_args: Any, **_kwargs: Any) -> None:
        self.django_settings_module = str(config.inicfg['DJANGO_SETTINGS_MODULE'])

    mypy_django_plugin_config.DjangoPluginConfig.parse_toml_file = parse_toml_file  # type: ignore
