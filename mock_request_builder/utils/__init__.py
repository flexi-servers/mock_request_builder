from typing import Type

def set_create_model_keys(db_model: Type, request_data) -> Type:
    create_keys = getattr(db_model, "create_keys", [])
    optional_create_keys = getattr(db_model, "create_keys_optional", [])
    for i in create_keys:
        setattr(db_model, i, getattr(request_data, i))

    for i in optional_create_keys:
        if getattr(request_data, i, None) is not None:
            setattr(db_model, i, getattr(request_data, i))

    return db_model


def model_enable_soft_delete(sql_model) -> bool:
    enable_soft_delete = False
    if getattr(sql_model, "soft_delete", None) is not None and getattr(sql_model, "delete", None) is not None:
        enable_soft_delete = True
    return enable_soft_delete
