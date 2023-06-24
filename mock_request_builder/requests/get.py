from typing import List

from fastapi import APIRouter
from fastapi import Depends
from starlette.responses import JSONResponse

from mock_request_builder import MockRequestConfig, ParentConfig
from mock_request_builder.config.auth import BaseAuthProvider
from mock_request_builder.sqlalchemy_to_pydantic import sqlalchemy_to_json
from mock_request_builder.utils import model_enable_soft_delete


def _build_multi_get_request(router: APIRouter,
                             config: MockRequestConfig,
                             sqlalchemy_model, tags, path, response_model):

    enable_soft_delete = model_enable_soft_delete(sqlalchemy_model)

    @router.get(path,
                response_model=List[response_model],
                tags=tags,
                operation_id='get_all_' + sqlalchemy_model.__tablename__ +
                             ('' if str(sqlalchemy_model.__tablename__).endswith('s') else 's'))
    async def get_all(auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):
        query = auth_state.db.query(sqlalchemy_model)

        if enable_soft_delete:
            query = query.filter(sqlalchemy_model.soft_delete == None)

        return sqlalchemy_to_json(query.all())


def _build_parent_get_request(router: APIRouter,
                              config: MockRequestConfig,
                              parent_config: ParentConfig,
                              sqlalchemy_model, tags,
                              response_model, override_parent_id_type: type = int):

    if not parent_config.parent_path.count("{id}"):
        raise Exception("Path must have {id} as a part of it.")

    enable_soft_delete = model_enable_soft_delete(sqlalchemy_model)

    @router.get(parent_config.parent_path,
                response_model=List[response_model],
                tags=tags,
                operation_id='get_' + sqlalchemy_model.__tablename__ + (
                        '' if str(sqlalchemy_model.__tablename__).endswith('s') else 's') + '_by_parent')
    async def get_by_parent(id: override_parent_id_type, auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):


        query = auth_state.db.query(parent_config.sqlalchemy_model).filter(parent_config.sqlalchemy_model.id == id)
        if query.first() is None:
            return JSONResponse(status_code=404, content={"message": "NOT FOUND"})

        data_query = auth_state.db.query(sqlalchemy_model).filter(getattr(sqlalchemy_model, parent_config.child_parent_key) == id)

        if enable_soft_delete:
            data_query = data_query.filter(parent_config.sqlalchemy_model.soft_delete == None)

        return sqlalchemy_to_json(data_query.all())


def _build_single_get_request(router: APIRouter,
                              config: MockRequestConfig, sqlalchemy_model, tags, path, response_model,
                              override_id_type: type = int):
    if not path.count("{id}"):
        raise Exception("Path must have {id} as a part of it.")

    enable_soft_delete = model_enable_soft_delete(sqlalchemy_model)

    @router.get(path, response_model=response_model, tags=tags, operation_id='get_' + sqlalchemy_model.__tablename__)
    async def get_single(id: override_id_type, auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):
        row = auth_state.db.query(sqlalchemy_model).filter(sqlalchemy_model.id == id).first()
        if row is None or (enable_soft_delete and row.soft_delete is not None):
            return JSONResponse(status_code=404, content={"message": "NOT FOUND"})

        return sqlalchemy_to_json(row)
