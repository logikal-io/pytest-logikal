import subprocess
from pathlib import Path
from sys import stderr

from termcolor import colored


def install_node_packages(node_prefix: Path | None = None) -> None:
    node_prefix = node_prefix or Path(__file__).parent
    if not (node_prefix / 'node_modules').exists():
        print(colored('Installing Node.js packages', 'yellow', attrs=['bold']), file=stderr)
        args = ['--no-save', '--no-audit', '--no-fund']
        command = ['npm', 'install', *args, '--prefix', str(node_prefix)]
        subprocess.run(command, text=True, check=True)  # nosec: secure, not using untrusted input
