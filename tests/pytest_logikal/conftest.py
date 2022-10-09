from importlib import reload
from pathlib import Path
from typing import Callable, Dict, Type, Union, cast

import pytest
from pytest_mock import MockerFixture

from pytest_logikal import (
    bandit, build, core, file_checker, isort, licenses,
    plugin as pytest_logikal_plugin, pylint, requirements, style,
)

# Reload plugins to ensure coverage captures definitions (order is important)
reload(core)
reload(pytest_logikal_plugin)
reload(file_checker)

reload(bandit)
reload(build)
reload(isort)
reload(licenses)
reload(pylint)
reload(requirements)
reload(style)


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
                if name == 'pyproject.toml':
                    path = pytester.makepyprojecttoml(file_contents[name])
                else:
                    path = pytester.makefile(Path(name).suffix, **{name: contents})
        else:
            path = makepyfile(file_contents)

        inicfg: Dict[str, Union[str, int]] = {'max_line_length': 99, 'cov_fail_under': 100}
        if set_django_settings_module:
            inicfg['DJANGO_SETTINGS_MODULE'] = 'tests.dummy_django_settings'
        config = mocker.Mock(inicfg=inicfg)
        config.getini = inicfg.get
        config.invocation_params.dir = path.parent

        plugin_obj = plugin(config=config)
        parent = mocker.Mock(nodeid='parent', config=plugin_obj.config, path=path)
        args = {'parent': parent, 'name': plugin_obj.name}
        if issubclass(item, file_checker.CheckItem):
            args['plugin'] = plugin_obj
        item_obj = item.from_parent(**args)
        return cast(pytest_logikal_plugin.Item, item_obj)

    return plugin_item_wrapper
