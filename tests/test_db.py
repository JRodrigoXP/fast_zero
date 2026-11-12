from sqlalchemy.orm import Session

from fast_zero.database import get_session


def test_get_session():
    session = next(get_session())

    assert isinstance(session, Session)
    session.close()
