from pwdlib import PasswordHash
from http import HTTPStatus
from jwt import encode, decode
from jwt.exceptions import PyJWTError
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from fast_zero.database import get_session
from fast_zero.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
pwd_context = PasswordHash.recommended()
SECRET_KEY = 'your-secret-key'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data_payload: dict):
    to_encode = data_payload.copy()

    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({'exp': expire})

    encode_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encode_jwt


def get_current_user(
    session=Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    credencials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        if not username:
            raise credencials_exception
    except PyJWTError:
        raise credencials_exception

    user_db = session.scalar(select(User).where(User.email == username))

    if user_db is None:
        raise credencials_exception

    return user_db
