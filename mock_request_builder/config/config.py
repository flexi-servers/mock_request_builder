import abc

from fastapi import APIRouter

from .auth import BaseAuthProvider


class MockRequestConfig(abc.ABC):
    enable_revision = False
    router: APIRouter


    @abc.abstractmethod
    async def get_auth_provider(self) -> BaseAuthProvider:
        raise NotImplementedError()

