"""Utility functions for datatypes (dict, lists, etc...).

:author: Benoit Gielly (benoit.gielly@gmail.com)
:created: 03/07/2022
"""
from __future__ import absolute_import, print_function

import logging

LOG = logging.getLogger(__name__)


def get_key_from_value(value, data):
    """Retrieve dictionary key from given value.

    Args:
        value (str): Name of the value to search its matching key.
        data (dict): The dictionary to search into

    Returns:
        str: Name of the matching key found, None otherwise.
    """
    match = []
    for key, name in data.items():
        if value in name:
            match.append(key)
    key = sorted(match, key=lambda x: len(value.replace(x, "")))
    return key[0] if key else None
