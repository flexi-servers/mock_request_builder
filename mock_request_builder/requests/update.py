import json
import logging
from typing import Callable, List, Awaitable

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import DeclarativeMeta
from starlette.responses import JSONResponse

from mock_request_builder import MockRequestConfig
from mock_request_builder.config.auth import BaseAuthProvider
from mock_request_builder.sqlalchemy_to_pydantic import sqlalchemy_update_builder, sqlalchemy_to_json
from mock_request_builder.utils import model_enable_soft_delete


def _build_update_request(router: APIRouter,
                          config: MockRequestConfig,
                          sqlalchemy_model, tags, path, response_model,
                          override_id_type: type = int,
                          post_function: Callable[[BaseAuthProvider, DeclarativeMeta, List], Awaitable[None]] = None):

    if not path.count("{id}"):
        raise Exception("Path must have {id} as a part of it.")

    if getattr(sqlalchemy_model, "update_keys", None) is None:
        logging.exception(f"Model {sqlalchemy_model} has no update_keys")
        return
    update_keys = getattr(sqlalchemy_model, "update_keys")
    update_model = sqlalchemy_update_builder(sqlalchemy_model)
    enable_soft_delete = model_enable_soft_delete(sqlalchemy_model)

    @router.post(path, response_model=response_model, tags=tags,
                 operation_id='update_' + sqlalchemy_model.__tablename__)
    async def update(id: override_id_type, model: update_model, auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):

        data = json.loads(model.json(exclude_unset=True))
        db = auth_state.db

        if len(data.keys()) == 0:
            return JSONResponse(status_code=400, content={"error": "No parameters given"})
        row = db.query(sqlalchemy_model)

        query = row.filter(sqlalchemy_model.id == id)
        if enable_soft_delete:
            # must be == None because of sqlalchemy
            query = query.filter(sqlalchemy_model.soft_delete == None)
        row = query.first()

        if row is None:
            return JSONResponse(status_code=404, content={"error": "Item not found"})

        updated_keys = []
        for j in update_keys:
            if j not in data:
                continue
            # skip keys not included in received update model
            if j not in model.__dict__:
                continue

            new_value = getattr(model, j, None)
            column_nullable = getattr(sqlalchemy_model, j, None).expression.nullable

            # Update to new value and update None if column is nullable
            if new_value is not None or column_nullable is True and new_value is None:
                updated_keys.append([j, getattr(model, j)])

                setattr(row, j, getattr(model, j))

        if post_function is not None:
            await post_function(auth_state, row, updated_keys)
        db.commit()
        db.refresh(row)
        return sqlalchemy_to_json(row)
