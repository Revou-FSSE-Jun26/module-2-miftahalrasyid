import nh3
import marshmallow as ma


def sanitize_string(value):
    """Strip all HTML tags from a string using nh3."""
    if isinstance(value, str):
        return nh3.clean(value, tags=set())
    return value


def sanitize_dict(data):
    """Recursively sanitize all string values in a dict/list structure."""
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, dict):
        return {k: sanitize_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    return data


class SanitizeMixin:
    """
    Marshmallow schema mixin that strips HTML from all string fields on pre_load.
    Add this as the FIRST parent class in any schema that accepts user input.
    """
    @ma.pre_load
    def _sanitize_input(self, data, **kwargs):
        if isinstance(data, dict):
            return sanitize_dict(data)
        return data
