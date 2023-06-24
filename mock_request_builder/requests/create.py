import asyncio
import logging
from typing import List, Callable, Awaitable, Coroutine, Any, Type

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeMeta
from starlette.responses import JSONResponse

from mock_request_builder import ParentConfig
from mock_request_builder.config.auth import BaseAuthProvider
from mock_request_builder.config.config import MockRequestConfig
from mock_request_builder.sqlalchemy_to_pydantic import sqlalchemy_create_builder, sqlalchemy_to_json
from mock_request_builder.utils import model_enable_soft_delete
from mock_request_builder.utils.not_null import not_null

def _create_request_builder(router: APIRouter,
                            config :MockRequestConfig,
                            sqlalchemy_model: Type[DeclarativeMeta],
                            tags: List[str] | None,
                            path: str | None,
                            response_model: Type[BaseModel],
                            post_function: Callable[[BaseAuthProvider, DeclarativeMeta], Coroutine[Any, Any, None]] | None = None):
    if getattr(sqlalchemy_model, "create_keys", None) is None:
        logging.exception(f"Model {sqlalchemy_model} has no create_keys")
        return

    create_keys = getattr(sqlalchemy_model, "create_keys", [])
    create_request_model = sqlalchemy_create_builder(sqlalchemy_model)
    optional_create_keys = getattr(sqlalchemy_model, "create_keys_optional", [])

    not_null(getattr(sqlalchemy_model, "__tablename__", None), "Model has no __tablename__")

    @router.post(path, response_model=response_model, tags=tags,
                 operation_id='create_' + sqlalchemy_model.__tablename__)
    async def create(request_data: create_request_model, auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):
        db = auth_state.db

        model = sqlalchemy_model()

        for i in create_keys:
            setattr(model, i, getattr(request_data, i))
        for i in optional_create_keys:
            if getattr(request_data, i, None) is not None:
                setattr(model, i, getattr(request_data, i))

        db.add(model)
        db.commit()
        db.refresh(model)
        if post_function is not None:
            asyncio.create_task(post_function(auth_state, model))
        db.refresh(model)
        return sqlalchemy_to_json(model)


def _parent_create_request_builder(router: APIRouter,
                                   config: MockRequestConfig,
                                   parent_config: ParentConfig,
                                   sqlalchemy_model,
                                   tags,
                                   response_model,
                                   override_parent_id_type: type = int,
                                   post_function: Callable[[BaseAuthProvider, DeclarativeMeta], Awaitable[None]] | None = None):

    if getattr(sqlalchemy_model, "create_keys", None) is None:
        logging.exception(f"Model {sqlalchemy_model} has no create_keys")
        return

    create_keys: List[str] = getattr(sqlalchemy_model, "create_keys", [])
    create_request_model = sqlalchemy_create_builder(sqlalchemy_model, exclude=[parent_config.child_parent_key])
    optional_create_keys = getattr(sqlalchemy_model, "create_keys_optional", [])

    @router.post(parent_config.parent_path, response_model=response_model, tags=tags,
                 operation_id='create_' + sqlalchemy_model.__tablename__ + '_on_parent')
    async def create_by_parent(id: override_parent_id_type,
                               request_data: create_request_model,
                               auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):
        db = auth_state.db
        primary_key = inspect(parent_config.sqlalchemy_model).primary_key[0].name
        parent_model = db.query(parent_config.sqlalchemy_model).filter(getattr(parent_config.sqlalchemy_model, primary_key) == id).first()
        if parent_model is None or (
                model_enable_soft_delete(parent_config.sqlalchemy_model) and parent_model.soft_delete is not None):
            return JSONResponse(status_code=404, content={"message": "Item not found"})

        model = sqlalchemy_model()

        setattr(model, parent_config.child_parent_key, id)

        for key in create_keys:
            if key == parent_config.child_parent_key:
                continue
            setattr(model, key, getattr(request_data, key))

        for i in optional_create_keys:
            if getattr(request_data, i, None) is not None:
                setattr(model, i, getattr(request_data, i))

        db.add(model)
        db.commit()
        db.refresh(model)

        if post_function is not None:
            async def post():
                await post_function(auth_state, model)

            asyncio.create_task(post())
        db.refresh(model)
        return sqlalchemy_to_json(model)
