import logging
from typing import Optional, Type, Any, Tuple, List

from pydantic import create_model, BaseConfig
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty, Mapper, DeclarativeMeta
from sqlalchemy.orm.properties import ColumnProperty



def memoize(function):
    memo = {}

    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key in memo:
            return memo[key]
        else:
            rv = function(*args, **kwargs)
            memo[key] = rv
            return rv

    return wrapper


class OrmConfig(BaseConfig):
    from_attributes = True


def get_type_of_column(column: ColumnProperty,
                       name: str,
                       optional=None,
                       all_optional: bool = False,
                       override_all_optional: bool = False,
                       override_key_optional=None) -> Tuple[type, Any]:
    if override_key_optional is None:
        override_key_optional = []
    if optional is None:
        optional = []

    python_type: Optional[type] = None
    # Checking if the Column Type has an Implemented python type
    # Varchar(45) --> str
    if hasattr(column.type, "impl"):
        if hasattr(column.type.impl, "python_type"):
            python_type = column.type.impl.python_type
    elif hasattr(column.type, "python_type"):
        python_type = column.type.python_type
    assert python_type, f"Could not infer python_type for {column}"

    # Checking if the column is optional
    default = None
    # This line is original from the package. Could be improved
    if not all_optional and name not in optional and column.default is None and not column.nullable:
        default = ...
    if override_all_optional or name in override_key_optional:
        default = None
    return python_type, default


# memoize to avoid recreating the same model
@memoize
def sqlalchemy_to_pydantic(db_model: Any,
                           config: Type[BaseConfig] = OrmConfig,
                           exclude=None,
                           add_keys=None,
                           override_include=None,
                           override_name: str | None = None,
                           load_mode=True,
                           lazy_load_keys=None,
                           edit_mode=False,
                           **kwargs):
    if override_include is None:
        override_include = list()
    if lazy_load_keys is None:
        lazy_load_keys = []
    if add_keys is None:
        add_keys = {}
    if exclude is None:
        exclude = []
    # Used to Global exclude columns
    for i in getattr(db_model, "exclude_keys", []):
        exclude.append(i)
    for i in getattr(db_model, "load_lazy", []):
        lazy_load_keys.append(i)

    mapper: Mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                # Checking if the column should be excluded
                name = attr.key
                if name in exclude:
                    continue

                if override_include is not None and len(override_include) > 0:
                    if name not in override_include:
                        continue
                column = attr.columns[0]
                # Getting the type of the column
                fields[name] = get_type_of_column(column, name, kwargs)

        # Lazy loading of relationships
        if isinstance(attr, RelationshipProperty) and not edit_mode:
            if attr.key in lazy_load_keys:
                tmp = attr.entity.entity
                # Adding the Lazy load key to the fields
                if attr.uselist:
                    fields[attr.key] = (List[sqlalchemy_to_pydantic(tmp)], list)
                else:
                    # See https://docs.pydantic.dev/latest/usage/models/#required-optional-fields
                    fields[attr.key] = (Optional[sqlalchemy_to_pydantic(tmp)], ...) if attr.key in lazy_load_keys else (
                    sqlalchemy_to_pydantic(tmp), None)
    for i in add_keys:
        fields[i] = add_keys[i]

    # Just a check for the pydantic_to_json method
    if load_mode and getattr(db_model, "load_keys", None) is not None:
        for i in getattr(db_model, "load_keys"):
            if i not in fields:
                logging.exception("Could not find key %s in fields", i)
                raise Exception(f"Could not find key {i} in fields in {db_model.__name__}")

    model_name = db_model.__name__
    if override_name is not None:
        model_name = override_name
    # Creating the model DeclarativeMetad on the fields
    pydantic_model = create_model(model_name, __config__=config, **fields)
    return pydantic_model


def get_type_of_sqlalchemy_field(db_model: Type[DeclarativeMeta], name: str) -> type | None:
    mapper = inspect(db_model)
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                if attr.key == name:
                    column = attr.columns[0]
                    return get_type_of_column(column, name)[0]
    return None
