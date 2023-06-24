import logging
import os
import random
import string

import jwt
from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from examples.basic.database import get_db
from mock_request_builder import MockRequestConfig, BaseAuthProvider


jwt_time = os.getenv("JWT_TIME")
jwt_secret = os.getenv("JWT_SECRET")

if jwt_time is None:
    jwt_time = 3600
if jwt_secret is None:
    jwt_secret = ''.join(
        random.choice(string.ascii_uppercase + string.digits + string.ascii_letters) for _ in range(200))
    logging.exception("JWT_SECRET not set, using Random String!")


auth_router = APIRouter()

@auth_router.post("/auth/login", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # TODO: implement login
    # Generate a jwt access token
    token_data= {}
    return {"access_token": jwt.encode(token_data, jwt_secret, algorithm='HS256'), "token_type": "bearer"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

class MockConfig(MockRequestConfig):
    class DBAuthProvider(BaseAuthProvider):
        def __init__(self, db: Session, data: dict):
            self._db = db
            self.data = data
        @property
        def db(self) -> Session:
            return self._db



    async def get_auth_provider(self,token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> BaseAuthProvider:

        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            # The TOKEN here is a JWT token
            # TODO: Check if the token is valid
            # here we just check it with the secret
            data = jwt.decode(token, jwt_secret, algorithms='HS256')
            # Return a AuthProvider, It must be a subclass of BaseAuthProvider
            return self.DBAuthProvider(db, data)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
