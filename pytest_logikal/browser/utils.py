import os
import shutil
import stat
from pathlib import Path
from sys import stderr
from zipfile import ZipFile

import requests
from tqdm import tqdm


def download(url: str, output: Path) -> Path:
    print(f'Downloading "{url}"...', file=stderr)
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
        for member_info in archive_file.infolist():
            extracted_path = archive_file.extract(member_info, archive.parent / archive.stem)

            attributes = member_info.external_attr >> 16
            attributes &= stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO  # extract permission bits
            if member_info.is_dir():
                os.chmod(extracted_path, mode=0o755)
            elif attributes:
                os.chmod(extracted_path, mode=attributes)


def move(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(destination, ignore_errors=True)
    shutil.move(str(source), str(destination))
