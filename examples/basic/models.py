
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    test = Column(String(255))
    foo = Column(String(255))
    bar = Column(String(255))


    # mock_request
    create_keys = ["name", "test", "foo", "bar"]
    update_keys = ["name", "test"]

class Child(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    child_name = Column(String(255))
    parent_id = Column(Integer)

    create_keys = ["child_name", "parent_id"]
    update_keys = ["child_name"]
