import os
from dataclasses import dataclass
from functools import lru_cache
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
    @staticmethod
    @lru_cache(maxsize=None)
    def service_url() -> str:
        if not (service_url := os.environ.get('VALIDATOR_SERVICE_URL')):
            service = Service(name='validator', ready_log_text='Checker service started')
            service_url = f'http://127.0.0.1:{service.container_port("8888/tcp")}'

        logger.debug(f'Using HTML/CSS/SVG validator service running at "{service_url}"')
        return service_url

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
