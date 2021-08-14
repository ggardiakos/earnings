import collections
import re


def flatten(d: dict, parent_key='', sep='_'):
    """Flatten a dictionary"""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def camel_to_snake(name):
    '''Converts CamelCased strings to snake_case'''
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    return name