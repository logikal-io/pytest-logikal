from collections.abc import Callable
from importlib import import_module, reload
from itertools import chain
from pathlib import Path
from typing import Any

import pytest
from _pytest.config.findpaths import ConfigValue  # pylint: disable=import-private-name
from pytest_mock import MockerFixture

from pytest_logikal import core, file_checker, plugin as pytest_logikal_plugin

FILES_DIR = Path(__file__).parent / 'files'

# Reload modules to ensure coverage captures definitions (order is important)
MODULES = [
    # Core modules
    'core', 'file_checker', 'plugin',
    # Additional modules
    'black', 'browser', 'django', 'node_install', 'utils', 'validator',
]
for submodule in chain.from_iterable([MODULES, *core.PLUGINS.values()]):
    if submodule == 'mypy':
        continue
    reload(import_module(f'pytest_logikal.{submodule}'))


def append_newline(file: Path) -> Path:
    # Necessary because makefile and makepyfile strips ending new lines
    with file.open('a') as file_obj:
        file_obj.write('\n')
    return file


@pytest.fixture
def plugin_item(
    pytester: pytest.Pytester,
    pytestconfig: pytest.Config,
    mocker: MockerFixture,
) -> Callable[..., pytest_logikal_plugin.Item]:

    def plugin_item_wrapper(
        plugin: type[pytest_logikal_plugin.Plugin],
        item: type[pytest_logikal_plugin.Item],
        file_contents: str | dict[str, str] = '',
        set_django_settings_module: bool = True,
    ) -> pytest_logikal_plugin.Item:
        """
        Create new files and create a check item pointing to the last one.
        """
        if isinstance(file_contents, dict):
            for name, contents in file_contents.items():
                pyproject = 'pyproject.toml'
                path = (
                    pytester.makepyprojecttoml(file_contents[name]) if name == pyproject else
                    append_newline(pytester.makefile(Path(name).suffix, **{name: contents}))
                )
        else:
            path = append_newline(pytester.makepyfile(file_contents))

        def getini(name: str) -> Any:
            if config := inicfg.get(name):
                return config.value
            return config

        inicfg: dict[str, ConfigValue] = {
            option: ConfigValue(value=entry['value'], origin='file', mode='toml')
            for option, entry in core.DEFAULT_INI_OPTIONS.items()
        }
        if set_django_settings_module:
            inicfg['DJANGO_SETTINGS_MODULE'] = ConfigValue(
                value='tests.website.settings', origin='file', mode='toml',
            )
        config = mocker.Mock(inicfg=inicfg)
        config.getini = getini
        config.invocation_params.dir = path.parent
        config.rootpath = pytestconfig.rootpath
        config.stash = pytestconfig.stash
        config.option = pytestconfig.option

        plugin_obj = plugin(config=config)
        parent = mocker.Mock(nodeid='parent', config=plugin_obj.config, path=path)
        args = {'parent': parent, 'name': plugin_obj.name}
        if issubclass(item, file_checker.FileCheckItem):
            args['plugin'] = plugin_obj
        item_obj = item.from_parent(**args)
        item_obj.setup()
        return item_obj

    return plugin_item_wrapper
