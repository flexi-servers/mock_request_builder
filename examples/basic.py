import uvicorn
from fastapi import FastAPI, APIRouter
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from mock_request_builder import MockBuilder, MockRequestConfig, BaseAuthProvider, ParentConfig
from mock_request_builder.sqlalchemy_to_pydantic import sqlalchemy_to_pydantic

api = FastAPI()

engine = create_engine(
    "sqlite:///./sql_app.db", pool_pre_ping=True, pool_recycle=3600, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    test = Column(String(255))


    # mock_request
    create_keys = ["name", "test"]
    update_keys = ["name", "test"]

class Child(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    child_name = Column(String(255))
    parent_id = Column(Integer)

    create_keys = ["child_name", "parent_id"]
    update_keys = ["child_name"]



# create all models
Base.metadata.create_all(engine)

class MockConfig(MockRequestConfig):
    class DBAuthProvider(BaseAuthProvider):
        def __init__(self, db: Session):
            self._db = db
        @property
        def db(self) -> Session:
            return self._db

    async def get_auth_provider(self) -> BaseAuthProvider:
        return self.DBAuthProvider(db = next(get_db()))

config  = MockConfig()

router = APIRouter()
mock_builder = MockBuilder(router=router,config=config, path="/parent",pydantic_model=sqlalchemy_to_pydantic(Parent),sql_alchemy_model=Parent, tags=["parent"])
mock_builder.create()
mock_builder.get()
mock_builder.delete()
mock_builder.update()


parent_config = ParentConfig(sqlalchemy_model=Parent,parent_path="/parent/{id}/children", child_parent_key="parent_id")
child_mock_builder = MockBuilder(router=router,config=config, path="/child",pydantic_model=sqlalchemy_to_pydantic(Child),sql_alchemy_model=Child, tags=["child"], parent_config=parent_config)
child_mock_builder.create()
child_mock_builder.get()
child_mock_builder.delete()
child_mock_builder.update()


api.include_router(router)

if __name__ == "__main__":
    uvicorn.run("basic:api")