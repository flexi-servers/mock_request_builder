from typing import List

from fastapi import APIRouter
from fastapi import Depends
from starlette.responses import JSONResponse

from mock_request_builder.requests.models.revision import Revision
from mock_request_builder.sqlalchemy_to_pydantic import sqlalchemy_to_pydantic, sqlalchemy_to_json
from mock_request_builder.utils import model_enable_soft_delete
from mock_request_builder import BaseAuthProvider, MockRequestConfig


def _get_revisions(router: APIRouter, sqlalchemy_model, tags, path,
                   config: MockRequestConfig,
                   override_id_type: type = int):
    if not path.count("{id}"):
        raise Exception("Path must have {id} as a part of it.")

    revision_docs = sqlalchemy_to_pydantic(Revision)
    enable_soft_delete = model_enable_soft_delete(sqlalchemy_model)

    @router.get(path + "/revisions", response_model=List[revision_docs], tags=[*tags, "Revision"],
                operation_id='get_' + sqlalchemy_model.__tablename__ + "_revisions")
    async def get_revision(id: override_id_type, auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):
        row = auth_state.db.query(sqlalchemy_model).filter(sqlalchemy_model.id == id)

        if enable_soft_delete:
            row = row.filter(sqlalchemy_model.soft_delete == None)

        if row.first() is None:
            return JSONResponse(status_code=404, content={"error": "Item not found"})

        row = auth_state.db.query(Revision).filter(Revision.row_id == id) \
            .filter(Revision.tablename == sqlalchemy_model.__tablename__).all()
        return sqlalchemy_to_json(row)
