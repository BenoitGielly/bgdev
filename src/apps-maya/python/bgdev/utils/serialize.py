"""Utility methods for data serialization (JSON, YAML, PKL, etc...).

:created: 26/04/2018
:author: Benoit Gielly <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from collections import OrderedDict
import json
import logging
import os

import yaml
import yaml.representer

LOG = logging.getLogger(__name__)


# JSON utils ---
def json_load(path, **kwargs):
    """Import JSON file.

    Args:
        path (str): JSON file path to save data
        kwargs (dict): Any extra flags to pass in the :func:`json.load` command

    Returns:
        dict: The loaded data.
    """
    data = {}
    if not os.path.exists(path):
        LOG.warning("Path doesn't exists, returning empty dictionary.")
    else:
        with open(path) as _file:
            data = json.load(_file, **kwargs)

    return data


def json_dump(data, path, **kwargs):
    """Export JSON file.

    Args:
        data (dict): Dictionary to export as JSON
        path (str): JSON file path to save data
        kwargs (dict): Any extra flags to pass in the :func:`json.dump` command

    Returns:
        str: given file path
    """
    with open(path, "w") as _file:
        json.dump(data, _file, **kwargs)

    return path


# YAML utils ---
def yaml_load(path, ordered=False, **kwargs):
    """Import YAML file.

    Args:
        path (str): YAML file path to save data
        ordered (bool): Load data in an orderedDict when True.
        kwargs (dict): Any extra flags to pass in the :func:`json.load` command

    Returns:
        dict: the loaded data
    """
    data = {}
    if ordered:
        data = OrderedDict()
        kwargs["Loader"] = Loader

    if not os.path.exists(path):
        LOG.warning("Path doesn't exists, returning empty dictionary.")
    else:
        with open(path) as _file:
            data = yaml.load(_file, **kwargs)

    return data


def yaml_dump(data, path, ordered=False, **kwargs):
    """Export YAML file.

    Args:
        data (dict): Dictionary to export as JSON
        path (str): YAML file path to save data
        ordered (bool): Dump data ordered when True.
        kwargs (dict): Any extra flags to pass in the :func:`json.dump` command

    Returns:
        str: given file path
    """
    if ordered:
        kwargs["Dumper"] = Dumper

    with open(path, "w") as _file:
        yaml.dump(data, _file, **kwargs)

    return path


class Loader(yaml.Loader):
    """Custom YAML Loader to load data in an OrderedDict."""

    def __init__(self, *args, **kwargs):
        super(Loader, self).__init__(*args, **kwargs)
        self.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            self.dict_constructor,
        )

    @staticmethod
    def dict_constructor(loader, node):
        """Create a custom constructor for yaml loader"""
        return OrderedDict(loader.construct_pairs(node))


class Dumper(yaml.Dumper):
    """Custom YAML Dumper to dump data from an OrderedDict."""

    def __init__(self, *args, **kwargs):
        super(Dumper, self).__init__(*args, **kwargs)
        rpz = yaml.representer.SafeRepresenter
        self.add_representer(OrderedDict, self.dict_representer)
        self.add_representer(str, rpz.represent_str)
        self.add_representer(unicode, rpz.represent_unicode)

    @staticmethod
    def dict_representer(dumper, data):
        """Create a custom representer for yaml dumper"""
        return dumper.represent_dict(data.iteritems())
