import sys
from io import BytesIO
from logging import getLogger
from operator import methodcaller
from os import getcwd
from pathlib import Path
from shutil import copy
from subprocess import run
from typing import Any, Callable, Optional, Type, TypeVar

from PIL import Image, ImageChops

logger = getLogger(__name__)

Function = TypeVar('Function', bound=Callable[..., Any])


def hide_traceback(function: Function, error: Type[Exception] = AssertionError) -> Function:
    getattr(function, '__globals__')['__tracebackhide__'] = methodcaller('errisinstance', error)
    return function


@hide_traceback
def assert_image_equal(actual: bytes, expected: Path, temp_path: Path) -> None:
    temp_actual_path = temp_path / 'actual.png'
    temp_expected_path = temp_path / 'expected.png'
    temp_diff_path = temp_path / 'diff.png'

    logger.info(f'Checking expected image in "{expected}"')
    if expected.is_file():
        with Image.open(BytesIO(actual)) as actual_image, Image.open(expected) as expected_image:
            if actual_image == expected_image:
                logger.info('The actual image matches the expected image')
                return

            temp_actual_path.write_bytes(actual)  # saving the temporary actual image
            copy(expected, temp_expected_path)  # saving the temporary expected image
            diff_image = ImageChops.invert(ImageChops.difference(
                expected_image.convert('RGB'),
                actual_image.convert('RGB'),
            ))
            diff_image.save(str(temp_diff_path))  # saving the temporary diff image
            save_image_prompt(
                message='Actual image differs from the expected image',
                source=temp_actual_path, destination=expected, difference=temp_diff_path,
            )
    else:
        logger.info('Expected image not found')
        temp_expected_path.write_bytes(actual)  # saving the temporary actual image as expected
        save_image_prompt(
            message='Expected image file does not exist',
            source=temp_expected_path, destination=expected,
        )


def save_image_prompt(
    message: str,
    source: Path,
    destination: Path,
    difference: Optional[Path] = None,
) -> None:
    if not sys.stdin.isatty():
        error_lines = [
            f'{message} and this is not an interactive session (consider using --live)',
            f'  Actual: {source}',
            f'  Expected: {destination}',
        ]
        if difference:
            error_lines.append(f'  Difference: {difference}')
        raise AssertionError('\n'.join(error_lines))
    try:
        short_destination = destination.relative_to(getcwd())
    except ValueError:
        short_destination = destination

    colors = {'red': '\033[31m\033[1m', 'reset': '\033[0m'}
    print(f'\n{colors["red"]}{message}!{colors["reset"]}')
    print(short_destination)

    response = input('> Press "enter" to open or type "s" to skip or "c" to cancel: ')
    if response == '':
        # This subprocess call is secure as it is not using untrusted input
        run(['/usr/bin/xdg-open', str(source)], check=False)  # nosec
    elif response == 's':
        logger.info('Image opening skipped')
    else:
        raise AssertionError('Image opening cancelled')

    response = input('> Type "accept" to accept this version or press "enter" to reject: ')
    if response == 'accept':
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy(source, destination)
        logger.info(f'Image saved at "{short_destination}"')
    else:
        raise AssertionError('Image rejected')
