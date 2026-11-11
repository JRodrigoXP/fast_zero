from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select
from sqlalchemy.orm import Session

from fast_zero.database import get_session
from fast_zero.models import User
from fast_zero.schemas import Message, UserList, UserPublic, UserSchema, Token
from fast_zero.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)

app = FastAPI()


@app.get('/users', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(limit: int = 10, offset: int = 0, session=Depends(get_session)):
    users = session.scalars(
        select(User).limit(limit).offset(offset)
        # limit limita a quantidade de resultado
        # offset pula a quantidade de resultado
    ).all()
    return {'users': users}


@app.get(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def get_user(user_id: int, session=Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    return user


@app.post('/users', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserSchema, session: Session = Depends(get_session)):
    db_user = session.scalar(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    )

    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Username already exists',
            )
        elif db_user.email == user.email:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Email already exists',
            )

    db_user = User(
        username=user.username,
        password=get_password_hash(user.password),
        email=user.email,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@app.put(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def update_user(user_id: int, user: UserSchema, session=Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    existing_user = session.scalar(
        select(User).where(
            ((User.username == user.username) | (User.email == user.email))
            & (User.id != user_id)
        )
    )
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Username already exists',
            )
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Email already exists',
        )

    db_user.username = user.username
    db_user.email = user.email
    db_user.password = get_password_hash(user.password)

    session.commit()
    session.refresh(db_user)

    return db_user


@app.delete(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=Message
)
def delete_user(user_id: int, session=Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )
    session.delete(db_user)
    session.commit()
    return Message(message='User deleted')


@app.post('/token', response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session=Depends(get_session),
):
    user = session.scalar(
        select(User).where(User.email == form_data.username)
    )  # checa se o user existe

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=400, detail='incorrect email or password'
        )
    access_token = create_access_token(data_payload={'sub': user.email})

    return {'access_token': access_token, 'token_type': 'Bearer'}
