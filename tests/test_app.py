from http import HTTPStatus

from fast_zero.schemas import UserPublic


def test_read_users(client):
    response = client.get('/users')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}


def test_read_users_with_user(client, test_user):
    user_schema = UserPublic.model_validate(test_user).model_dump()
    # pega os atributos do usuário e transforma em um dicionário
    response = client.get('/users')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_get_user_with_id(client, test_user):
    user_schema = UserPublic.model_validate(test_user).model_dump()
    response = client.get(f'/users/{test_user.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == user_schema


def test_get_user_not_found(client):
    response = client.get('/users/999')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_create_user(client):
    user = {
        'username': 'Rodrigo',
        'email': 'Rodrigo@example.com',
        'password': '1q2w3e4r',
    }

    response = client.post('/users', json=user)

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': user['username'],
        'email': user['email'],
        'id': 1,
    }


def test_create_user_conflict_username(client, test_user):
    user = {
        'username': test_user.username,
        'email': f'new_{test_user.email}',
        'password': '1q2w3e4r',
    }

    response = client.post('/users', json=user)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username already exists'}


def test_create_user_conflict_email(client, test_user):
    user = {
        'username': f'{test_user.username}_new',
        'email': test_user.email,
        'password': '1q2w3e4r',
    }

    response = client.post('/users', json=user)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Email already exists'}


def test_update_user(client, test_user):
    updated_user = {
        'username': 'updated_user',
        'email': 'updated@example.com',
        'password': 'new_password',
    }

    response = client.put(
        f'/users/{test_user.id}',
        json=updated_user,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': test_user.id,
        'username': updated_user['username'],
        'email': updated_user['email'],
    }


def test_update_user_not_found(client):
    updated_user = {
        'username': 'updated_user',
        'email': 'updated@example.com',
        'password': 'new_password',
    }

    response = client.put(
        '/users/999',
        json=updated_user,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_delete_user(client, test_user):
    response = client.delete(f'/users/{test_user.id}')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}


def test_delete_user_not_found(client):
    response = client.delete('/users/999')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_get_token(client, test_user):
    response = client.post(
        '/token',
        data={
            'username': test_user.email,
            'password': test_user.clean_password,
        },
    )

    assert response.status_code == HTTPStatus.OK
    token = response.json()
    assert token['token_type'] == 'Bearer'
    assert 'access_token' in token
