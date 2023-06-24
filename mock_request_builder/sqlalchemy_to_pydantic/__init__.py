from typing import Type

from pydantic import BaseModel
from pydantic.main import ModelMetaclass
from sqlalchemy.orm import DeclarativeMeta

from .sql_alchemy import sqlalchemy_to_pydantic


def copy_of_dict(dictionary: dict):
    return {k: v for k, v in dictionary.items()}


def object_as_json(sql_object, return_model=None):
    if return_model is None:
        return _old_object_as_json(sql_object)
    else:
        return improved_object_as_json(sql_object, return_model)


def improved_object_as_json(sql_object, return_model: ModelMetaclass):
    # iterate through the return_model and get the values from the sql_object
    ret_dict = {}
    print(return_model)
    print(type(return_model))
    try:
        print(return_model.__fields__)
        print(return_model.__fields__.keys())
    except AttributeError:
        print("No fields")

    return {}


def _old_object_as_json(sql_object):

    ret_dict = {}
    for i in copy_of_dict(sql_object.__dict__):
        if type(sql_object.__dict__[i]) == list:
            ret_dict[i] = sqlalchemy_to_json(sql_object.__dict__[i])
        else:
            ret_dict[i] = sql_object.__dict__[i]
    # Lazy loading
    if getattr(sql_object, "load_lazy", None) is not None:
        for i in getattr(sql_object, "load_lazy"):
            if isinstance(getattr(sql_object, i), list):
                ret_dict[i] = [object_as_json(item) for item in getattr(sql_object, i)]
            else:
                ret_dict[i] = object_as_json(getattr(sql_object, i))
    if getattr(sql_object, "load_keys_special", None) is not None:
        for i in getattr(sql_object, "load_keys_special"):
            ret_dict[i] = getattr(sql_object, "load_keys_special")[i](sql_object)

    for i in getattr(sql_object, "load_keys", {}):
        key = None
        for j in sql_object.load_keys[i]:
            if key is None:
                key = getattr(sql_object, j, None)
            else:
                key = getattr(key, j, None)
        ret_dict[i] = key

    return ret_dict


def sqlalchemy_to_json(data):
    if isinstance(data, list):
        return [sqlalchemy_to_json(item) for item in data if item is not None]
    else:
        return object_as_json(data)


def sqlalchemy_update_builder(db_model: Type[DeclarativeMeta], **kwargs):
    if getattr(db_model, "update_keys", None) is None:
        raise Exception(f"Model {db_model} has no update_able_keys")
    update_keys = getattr(db_model, "update_keys")
    return sqlalchemy_to_pydantic(db_model,
                                  override_include=update_keys,
                                  override_all_optional=True,
                                  override_name="Update" + getattr(db_model, "__tablename__").capitalize(),
                                  load_mode=False, edit_mode=True, **kwargs)


def sqlalchemy_create_builder(db_model: Type[DeclarativeMeta],
                              override_name: str | None = None,
                              **kwargs) -> Type[BaseModel]:
    if getattr(db_model, "create_keys", None) is None:
        raise Exception(f"Model {db_model} has no create_keys")
    if override_name is None:
        override_name = "Create" + getattr(db_model, "__tablename__").capitalize()
    override_key_optional = getattr(db_model, "create_keys_optional", [])
    create_keys = [*getattr(db_model, "create_keys"), *override_key_optional]

    return sqlalchemy_to_pydantic(db_model,
                                  override_include=create_keys,
                                  override_all_optional=True,
                                  override_name=override_name,
                                  load_mode=False, override_key_optional=override_key_optional,
                                  edit_mode=True, **kwargs)
