from dataclasses import dataclass
from logging import getLogger
from typing import List, Optional

import requests
from django.utils.html import escape
from django.utils.safestring import mark_safe
from logikal_utils.docker import Service

logger = getLogger(__name__)


@dataclass
class ValidationError:
    message: str
    severity: str
    extract: Optional[str]
    first_line: int
    last_line: int


class Validator:
    _SERVICE_NAME = 'validator'
    _SERVICE_PORT = '8888/tcp'
    _service: Optional[Service] = None
    _service_url: Optional[str] = None

    @staticmethod
    def service() -> Service:
        if not Validator._service:
            Validator._service = Service(
                name=Validator._SERVICE_NAME,
                ready_log_text='Checker service started',
            )
        return Validator._service

    @staticmethod
    def service_url() -> str:
        if not Validator._service_url:
            port = Validator.service().container_port(Validator._SERVICE_PORT)
            Validator._service_url = f'http://127.0.0.1:{port}'
            logger.debug(
                f'Using HTML/CSS/SVG validator service running at {Validator._service_url} '
                f'(container: {Validator.service().container.short_id})'
            )
        return Validator._service_url

    @staticmethod
    def start_service() -> None:
        Validator.service()

    def errors(self, content: str, content_type: str = 'text/html') -> List[ValidationError]:
        # Checking content
        if not content:
            raise RuntimeError('Empty content')

        response = requests.post(
            self.service_url(), params={'out': 'json'}, headers={'Content-Type': content_type},
            data=content.encode(), timeout=10,
        )
        if response.status_code != 200:
            raise RuntimeError(f'Cannot validate content: {response}')

        # Parsing error messages
        source_lines = content.splitlines()
        errors: List[ValidationError] = []

        for message in response.json()['messages']:
            last_line = message.get('lastLine')
            first_line = message.get('firstLine', last_line)

            if first_line and source_lines[first_line - 1].endswith('<!-- validator: ignore -->'):
                continue

            extract = message.get('extract')
            if extract and (start := message.get('hiliteStart')):
                length = message.get('hiliteLength')
                extract = (
                    escape(extract[:start])
                    + mark_safe('<span class="hll">')  # nosec: fixed literal
                    + escape(extract[start:start + length])
                    + mark_safe('</span>')  # nosec: fixed literal
                    + escape(extract[start + length:])
                )

            errors.append(ValidationError(
                message=message['message'],
                severity=message['type'] if message['type'] != 'info' else 'warning',
                extract=extract,
                first_line=first_line,
                last_line=last_line,
            ))
        return errors
