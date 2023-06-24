def not_null(value, message):
    if value is None:
        raise ValueError(message)
    return value