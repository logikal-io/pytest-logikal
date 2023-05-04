from importlib import import_module, reload
from itertools import chain
from pathlib import Path
from typing import Callable, Dict, Type, Union, cast

import pytest
from pytest_mock import MockerFixture

from pytest_logikal import core, file_checker, plugin as pytest_logikal_plugin

FILES_DIR = Path(__file__).parent / 'files'

# Reload modules to ensure coverage captures definitions (order is important)
MODULES = ['core', 'file_checker', 'plugin', 'browser', 'docker', 'utils', 'validator']
for submodule in chain.from_iterable([MODULES, *core.PLUGINS.values()]):
    if submodule == 'mypy':
        continue
    reload(import_module(f'pytest_logikal.{submodule}'))


@pytest.fixture
def makepyfile(pytester: pytest.Pytester) -> Callable[[str], Path]:
    def makepyfile_wrapper(file_contents: str) -> Path:
        """
        Create a new Python source file and append a new line at the end of the file.
        """
        pyfilepath = pytester.makepyfile(file_contents)
        with pyfilepath.open('a') as pyfile:
            pyfile.write('\n')
        return pyfilepath

    return makepyfile_wrapper


@pytest.fixture
def plugin_item(
    pytester: pytest.Pytester,
    pytestconfig: pytest.Config,
    makepyfile: Callable[[str], Path],  # pylint: disable=redefined-outer-name
    mocker: MockerFixture,
) -> Callable[..., pytest_logikal_plugin.Item]:

    def plugin_item_wrapper(
        plugin: Type[pytest_logikal_plugin.Plugin],
        item: Type[pytest_logikal_plugin.Item],
        file_contents: Union[str, Dict[str, str]] = '',
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
                    pytester.makefile(Path(name).suffix, **{name: contents})
                )
        else:
            path = makepyfile(file_contents)

        inicfg: Dict[str, Union[str, int]] = {
            option: entry['value'] for option, entry in core.DEFAULT_INI_OPTIONS.items()
        }
        if set_django_settings_module:
            inicfg['DJANGO_SETTINGS_MODULE'] = 'tests.website.settings'
        config = mocker.Mock(inicfg=inicfg)
        config.getini = inicfg.get
        config.invocation_params.dir = path.parent
        config.rootpath = pytestconfig.rootpath

        plugin_obj = plugin(config=config)
        parent = mocker.Mock(nodeid='parent', config=plugin_obj.config, path=path)
        args = {'parent': parent, 'name': plugin_obj.name}
        if issubclass(item, file_checker.FileCheckItem):
            args['plugin'] = plugin_obj
        item_obj = item.from_parent(**args)
        item_obj.setup()
        return cast(pytest_logikal_plugin.Item, item_obj)

    return plugin_item_wrapper
