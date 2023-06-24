import uvicorn
from fastapi import FastAPI, APIRouter
from starlette.responses import RedirectResponse

from examples.basic.auth import MockConfig, auth_router
from mock_request_builder import MockBuilder, ParentConfig
from mock_request_builder.sqlalchemy_to_pydantic import sqlalchemy_to_pydantic
from models import Parent, Child, Base
from database import *

api = FastAPI()


# create all models
Base.metadata.create_all(engine)
MockBuilder.create_tables(engine)



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
api.include_router(auth_router)
@api.get("/")
async def root():
    return RedirectResponse(url="/docs")




if __name__ == "__main__":
    uvicorn.run("main:api")