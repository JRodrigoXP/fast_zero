import pytest

from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient

from fast_zero.models import User, table_registry
from fast_zero.database import get_session
from fast_zero.app import app
from fast_zero.security import get_password_hash


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def session():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={
            'check_same_thread': False
        },  # deixa a conexão com o banco de dados acessível a partir de múltiplas threads
        poolclass=StaticPool,  # não fecha a conexão com o banco de dados após cada teste
    )  # conexão com o banco
    table_registry.metadata.create_all(engine)  # criação da tabela
    with Session(engine) as session:
        yield session
    table_registry.metadata.drop_all(engine)
    engine.dispose()  # fecha a conexão com o banco de dados


@pytest.fixture
def test_user(session):
    user = User(
        username='testuser',
        email='testuser@example.com',
        password=get_password_hash('password'),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    user.clean_password = 'password'

    return user


@pytest.fixture
def token(client, test_user):
    response = client.post(
        '/token',
        data={
            'username': test_user.email,
            'password': test_user.clean_password,
        },
    )
    return response.json()['access_token']
