import abc

from sqlalchemy.orm import Session


class BaseAuthProvider(abc.ABC):

    @property
    @abc.abstractmethod
    def db(self)-> Session:
        raise NotImplementedError()

