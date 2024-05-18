from pathlib import Path
from shutil import copy

from pytest_logikal import node_install


def test_install_node_packages(tmp_path: Path) -> None:
    for file in ['package.json', 'package-lock.json']:
        copy(Path(node_install.__file__).parent / file, tmp_path)
    node_install.install_node_packages(node_prefix=tmp_path)
    assert (tmp_path / 'node_modules/stylelint').exists()
