from typing import Type

from sqlalchemy.orm import DeclarativeMeta


class ParentConfig:
    """


    """
    override_parent_id_type: type = int,
    parent_path: str


    sqlalchemy_model: Type[DeclarativeMeta] | None = None,



    """Foreign key name of the parent-child relationship.
    child.parent_id = 1
    --> parent_child_key = "parent_id"
    """
    child_parent_key: str

    def __init__(self, sqlalchemy_model, parent_path, child_parent_key, override_parent_id_type=None):
        self.sqlalchemy_model = sqlalchemy_model
        self.parent_path = parent_path
        self.child_parent_key = child_parent_key
        if override_parent_id_type is not None:
            self.override_parent_id_type = override_parent_id_type
