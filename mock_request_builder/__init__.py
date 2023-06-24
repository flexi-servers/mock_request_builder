from typing import List, Callable, Awaitable, Type, Coroutine, Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeMeta

from mock_request_builder.config.config import MockRequestConfig
from mock_request_builder.config.parent import ParentConfig
from mock_request_builder.provider import BaseAuthProvider
from mock_request_builder.requests.create import _create_request_builder, _parent_create_request_builder
from mock_request_builder.requests.delete import _build_delete_request
from mock_request_builder.requests.get import _build_multi_get_request, _build_parent_get_request, _build_single_get_request
from mock_request_builder.requests.not_implemented.revision import _get_revisions
from mock_request_builder.requests.update import _build_update_request


class MockBuilder:
    router: APIRouter
    sqlalchemy_model: Type[DeclarativeMeta]
    pydantic_model: BaseModel
    tags: List[str] | None

    path = None
    """
    The path must have /{id} as a part of it.
    """
    config: MockRequestConfig
    parent_config: ParentConfig | None = None
    used_methods: list = []

    def __init__(self,
                 router: APIRouter,
                 sql_alchemy_model: Any,
                 pydantic_model: BaseModel,
                 path: str,
                 config: MockRequestConfig,
                 parent_config: ParentConfig | None = None,
                 tags: List[str] | None = None,
                 primary_key_type: type = int,):

        self.router = router
        self.path = path
        self.sqlalchemy_model = sql_alchemy_model
        self.pydantic_model = pydantic_model
        if tags is None:
            tags = []
        self.tags = tags
        self.parent_config = parent_config
        self.config = config



        # Override id type
        if primary_key_type is None:
            raise Exception("primary_key_type cannot be None")
        self.primary_key_type = primary_key_type

    def create(self,
               post_function: Callable[[BaseAuthProvider, DeclarativeMeta], Coroutine[Any, Any, None]] | None = None):
        self.used_methods.append("create")
        if self.parent_config is None:
            _create_request_builder(
                router=self.router,
                sqlalchemy_model=self.sqlalchemy_model,
                config=self.config,
                tags=self.tags,
                path=self.path,
                response_model=self.pydantic_model,
                post_function=post_function)
        else:
            _parent_create_request_builder(router=self.router,
                                           config=self.config,
                                           parent_config=self.parent_config,
                                           sqlalchemy_model=self.sqlalchemy_model, tags=self.tags,
                                            response_model=self.pydantic_model,
                                           post_function=post_function)

    def get(self,
            override_load_multiple: bool = False,
            tags=None):
        if tags is None:
            tags = []
        if self.parent_config is not None:
            self.get_all_parent(tags=tags)
        if override_load_multiple or self.parent_config is None:
            self.get_all(tags=tags)

        self.get_single(tags=tags)

    def get_single(self, tags: List[str]):
        self.used_methods.append("get_single")
        _build_single_get_request(router=self.router, sqlalchemy_model=self.sqlalchemy_model,
                                  tags=[*self.tags, *tags], path=self.path + "/{id}", response_model=self.pydantic_model,
                                override_id_type=self.primary_key_type,config=self.config)

    def get_all(self, tags=None):
        self.used_methods.append("get_all")
        _build_multi_get_request(router=self.router, sqlalchemy_model=self.sqlalchemy_model, tags=[*self.tags, *tags],
                                 path=self.path, response_model=self.pydantic_model,config=self.config
                                 )

    def get_all_parent(self, tags=None):
        self.used_methods.append("get_all_parent")
        _build_parent_get_request(router=self.router, sqlalchemy_model=self.sqlalchemy_model,
                                  tags=[*self.tags, *tags],
                                  response_model=self.pydantic_model,config=self.config,parent_config=self.parent_config,)

    def update(self,
               post_function: Callable[[BaseAuthProvider, DeclarativeMeta, List], Awaitable[None]] = None):
        self.used_methods.append("update")
        _build_update_request(router=self.router, sqlalchemy_model=self.sqlalchemy_model, tags=self.tags, path=self.path + "/{id}/update",
                              response_model=self.pydantic_model,
                              config=self.config,
                              override_id_type=self.primary_key_type, post_function=post_function)

    def delete(self, permissions=None):
        self.used_methods.append("delete")
        _build_delete_request(router=self.router, config=self.config,sqlalchemy_model=self.sqlalchemy_model, tags=self.tags, path=self.path + "/{id}",
                              required_permission=permissions, override_id_type=self.primary_key_type)

    def revisions(self, permissions=None):
        self.used_methods.append("revisions")
        _get_revisions(router=self.router, sqlalchemy_model=self.sqlalchemy_model, tags=self.tags, path=self.path + "/{id}",
                       required_permission=permissions, override_id_type=self.primary_key_type)
