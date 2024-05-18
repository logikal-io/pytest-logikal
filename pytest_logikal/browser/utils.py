import os
import shutil
import stat
from pathlib import Path
from zipfile import ZipFile

import requests
from tqdm import tqdm


def download(url: str, output: Path) -> Path:
    print(f'Downloading "{url}"...')
    data_stream = requests.get(url, stream=True, timeout=30)
    total_size = int(data_stream.headers.get('content-length', 0))

    with tqdm(
        total=total_size, leave=False,
        unit='iB', unit_scale=True, unit_divisor=1024,
        disable='GITHUB_ACTIONS' in os.environ,
    ) as progress_bar:
        with open(output, 'wb') as output_file:
            for data in data_stream.iter_content(chunk_size=1024):
                progress_bar.update(output_file.write(data))

    return output


def unzip(archive: Path) -> None:
    with ZipFile(archive) as archive_file:
        archive_file.extractall(archive.parent / archive.stem)


def make_executable(file: Path) -> None:
    file.chmod(file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def move(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(destination, ignore_errors=True)
    shutil.move(str(source), str(destination))
