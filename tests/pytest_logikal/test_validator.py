from pytest import raises
from pytest_mock import MockerFixture

from pytest_logikal import validator


def test_invalid_response(mocker: MockerFixture) -> None:
    requests = mocker.patch('pytest_logikal.validator.requests')
    requests.post.return_value.status_code = 500
    with raises(RuntimeError, match='Cannot validate content'):
        validator.Validator().errors('test')


def test_empty_content() -> None:
    with raises(RuntimeError, match='Empty content'):
        validator.Validator().errors(content='')


def test_ignore() -> None:
    content_validator = validator.Validator()
    content = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Title</title></head></html>'

    errors = content_validator.errors(content)
    assert len(errors) == 1
    assert 'Consider adding a “lang” attribute' in errors[0].message

    assert not content_validator.errors(f'{content}<!-- validator: ignore -->')
