import os
import subprocess
from time import sleep, time
from typing import Optional

from docker import DockerClient, from_env as client_from_env
from docker.models.containers import Container
from termcolor import colored

from pytest_logikal.core import PYPROJECT


class Service:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str,
        project: Optional[str] = None,
        start_timeout_seconds: float = 30,
        ready_log_text: Optional[str] = None,
        log_poll_seconds: float = 3,
    ):
        self.name = name
        self.project = project or PYPROJECT['project']['name']
        self.start_timeout_seconds = start_timeout_seconds
        self.ready_log_text = ready_log_text
        self.log_poll_seconds = log_poll_seconds
        try:
            client = client_from_env()
            self.container = self._running_container(client=client, start_services=True)
        finally:
            client.close()

    def __str__(self) -> str:
        return f'Docker Compose project "{self.project}" service "{self.name}"'

    def start_services(self) -> None:
        print(colored('Starting Docker Compose services', 'yellow', attrs=['bold']))
        command = [
            'docker', 'compose', 'up', '--detach',
            *(['--quiet-pull'] if 'GITHUB_ACTIONS' in os.environ else []),
            '--wait', '--wait-timeout', str(self.start_timeout_seconds),
        ]
        subprocess.run(command, text=True, check=True)  # nosec: secure, not using untrusted input
        print()

    def _running_container(self, client: DockerClient, start_services: bool) -> Container:
        filters = {
            'status': 'running',
            'label': [
                f'com.docker.compose.project={self.project}',
                f'com.docker.compose.service={self.name}',
            ],
        }
        if containers := client.containers.list(limit=1, filters=filters):
            container = containers[0]
            container.reload()  # refresh container attributes

            health = container.attrs['State'].get('Health', {})
            health_status = health.get('Status')
            if health_status and health_status != 'healthy':
                logs = [log['Output'].strip() for log in health.get('Log', {}) if 'Output' in log]
                logs_str = ('\n\nLogs:\n' + '\n'.join(logs)) if logs else ''
                raise RuntimeError(f'{self} is not healthy{logs_str}')

            if self.ready_log_text and not start_services:
                print(f'Waiting for service "{self.name}" to be ready...')
                wait_start_time = time()
                while (  # pylint: disable=while-used
                    self.ready_log_text not in container.logs().decode()
                ):
                    if time() - wait_start_time >= self.start_timeout_seconds:
                        raise RuntimeError(f'{self} is not ready')
                    sleep(self.log_poll_seconds)
                print()

            return container

        if start_services:
            self.start_services()
            return self._running_container(client=client, start_services=False)

        raise RuntimeError(f'{self} not found')

    def container_port(self, service_port: str) -> str:
        return str(self.container.ports[service_port][0]['HostPort'])
