from pathlib import Path
from zipfile import ZipFile

from pytest_logikal.browser import utils


def test_download(tmp_path: Path) -> None:
    logikal_index = utils.download('https://logikal.io', tmp_path / 'index.html')
    assert 'Creating perfect digital experiences' in logikal_index.read_text()


def test_unzip(tmp_path: Path) -> None:
    test_zip_path = tmp_path / 'test.zip'
    with ZipFile(test_zip_path, 'w') as test_zip:
        test_zip.writestr('test.txt', data='test')
        test_zip.mkdir('test_dir')

    utils.unzip(test_zip_path)
    assert (tmp_path / 'test/test.txt').read_text() == 'test'
    assert (tmp_path / 'test/test_dir').is_dir()


def test_move(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    source.mkdir(parents=True)
    test_file = 'test.txt'
    test_file_contents = 'test'
    (source / test_file).write_text(test_file_contents)

    destination = tmp_path / 'destination'
    utils.move(source=source, destination=destination)
    assert (destination / test_file).read_text() == test_file_contents
