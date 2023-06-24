from fastapi import APIRouter
from fastapi import Depends
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_204_NO_CONTENT

from mock_request_builder import MockRequestConfig
from mock_request_builder.config.auth import BaseAuthProvider
from mock_request_builder.utils import model_enable_soft_delete


def _build_delete_request(router: APIRouter,
                          config: MockRequestConfig,
                          sqlalchemy_model, tags, path,
                           override_id_type: type = int):
    if not path.count("{id}"):
        raise Exception("Path must have {id} as a part of it.")

    enable_soft_delete = model_enable_soft_delete(sqlalchemy_model)

    @router.delete(path, tags=tags, status_code=204, operation_id='delete_' + sqlalchemy_model.__tablename__)
    async def delete(id: override_id_type, auth_state: BaseAuthProvider = Depends(config.get_auth_provider)):

        row = auth_state.db.query(sqlalchemy_model).filter(sqlalchemy_model.id == id).first()

        if row is None or (model_enable_soft_delete(sqlalchemy_model) and sqlalchemy_model.soft_delte is not None):
            return JSONResponse(status_code=404, content={"error": "Item not found"})

        if not enable_soft_delete:
            auth_state.db.delete(row)
        else:
            row.delete()
        auth_state.db.commit()
        return Response(status_code=HTTP_204_NO_CONTENT)
