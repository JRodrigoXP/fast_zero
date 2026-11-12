from http import HTTPStatus

import pytest
from fastapi import HTTPException
from jwt import decode

from fast_zero.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)


def test_jwt():
    data = {'sub': 'test@test.com'}
    token = create_access_token(data)

    result = decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert result['sub'] == data['sub']
    assert 'exp' in result


def test_password_hash_and_verify():
    password = 'password'
    password_hash = get_password_hash(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password('wrong-password', password_hash)


def test_get_current_user(session, test_user):
    token = create_access_token({'sub': test_user.email})

    result = get_current_user(session=session, token=token)

    assert result is test_user


@pytest.mark.parametrize(
    'token',
    [
        'invalid-token',
        create_access_token({'sub': ''}),
        create_access_token({'sub': 'unknown@example.com'}),
    ],
)
def test_get_current_user_invalid_credentials(session, token):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(session=session, token=token)

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == 'Could not validate credentials'
    assert exc_info.value.headers == {'WWW-Authenticate': 'Bearer'}
