import subprocess
from pathlib import Path
from typing import Optional

from termcolor import colored


def install_node_packages(node_prefix: Optional[Path] = None) -> None:
    node_prefix = node_prefix or Path(__file__).parent
    if not (node_prefix / 'node_modules').exists():
        print(colored('Installing Node.js packages', 'yellow', attrs=['bold']))
        command = ['npm', 'install', '--no-save', '--prefix', str(node_prefix)]
        subprocess.run(command, text=True, check=True)  # nosec: secure, not using untrusted input
