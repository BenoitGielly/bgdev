"""Utility method used in the toolbar.

:created: 12/11/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from collections import OrderedDict
import importlib
import logging
import os
import pkgutil
import sys

from PySide2 import QtCore
import six
import yaml
import yaml.representer

from . import cfg

LOG = logging.getLogger(__name__)
PY_EXTS = (".py", ".pyc", ".pyo", ".pyw", ".so", ".dll")


def get_dcc_package():
    """Get the current DCC's "check" package."""
    modpath = modpath_from_file(__file__).rpartition(".")[0]
    module = "{}.tabs.{}.main".format(modpath, get_dcc())
    return importlib.import_module(module)


def get_dcc():
    """Get current DCC application."""
    apps = {"maya": "maya", "houdini": "hou", "nuke": "nuke"}
    for dcc, module in apps.items():
        if pkgutil.find_loader(module):
            return dcc
    return "system"


def modpath_from_file(filename):
    """Get the module import path from its filename.

    Args:
        filename (str): Path to python file.

    Raises:
        ImportError: When module cannot be found in sys.path.

    Returns:
        str: The module import path.
    """
    filename = os.path.realpath(os.path.expanduser(filename))
    base = os.path.splitext(filename)[0]
    for path in sys.path:
        if not path:
            continue
        path = os.path.realpath(os.path.expanduser(path))
        path = os.path.normcase(os.path.abspath(path))
        if path and os.path.normcase(base).startswith(path):
            modpath = [
                pkg for pkg in base[len(path) :].split(os.sep) if pkg  # noqa
            ]
            if check_modpath_has_init(path, modpath[:-1]):
                return ".".join(modpath)
    raise ImportError("Can't find module for {} in sys.path".format(filename))


def check_modpath_has_init(path, parts):
    """Check if given module parts all contains an __init__ file.

    Args:
        path (str): Path to python file.
        parts (list): Each parts of a module path. (Eg. ["sanity", "core"]).

    Returns:
        bool: True if each part as an __init__ file as sibling else False.
    """
    modpath = []
    for part in parts:
        modpath.append(part)
        path = os.path.join(path, part)
        if not _has_init(path):
            return False
    return True


def _has_init(directory):
    """Check if given directory contains an __init__ file.

    Args:
        directory (str): Path to directory.

    Returns:
        bool: True if given directory contains an __init__ file.
    """
    module_or_pkg = os.path.join(directory, "__init__")
    for ext in PY_EXTS:
        if os.path.exists(module_or_pkg + ext):
            return True
    return False


def check_image(icon, normalized=True):
    """Convert the given image path to full path name.

    Args:
        icon (str): Name of the icon to check
        normalized (bool): Normalize the path to work on all OS

    Returns:
        str: Updated icon path so it's ready to be used.

    """
    icon_paths = cfg.ICON_PATHS or []

    # create a list of paths to lookup icons
    icon_folder = os.path.join(os.path.dirname(__file__), "icons")
    if icon_folder not in icon_paths:
        icon_paths.insert(0, icon_folder)

    # check for relatives path icons
    baseicon = icon
    if icon.startswith(".."):
        for each in icon_paths:
            _icon = os.path.join(each, icon[3:])
            if os.path.exists(_icon):
                icon = _icon
                break
    elif not os.path.isfile(icon):
        icon = ":/{0}".format(icon)

    # when icon file doesn't seem to exist
    if not QtCore.QFile.exists(icon):
        icon = search_icon_in_path(baseicon)
        if not icon:
            icon = "../default_icon.png"
            icon = os.path.abspath(os.path.join(icon_folder, icon[1:]))

    # normalize the path for windows
    icon = icon.replace(os.sep, "/") if normalized else icon

    return icon


def search_icon_in_path(name):
    """Search icon in XGMLANGPATH env variable."""
    paths = os.environ.get("XBMLANGPATH").split(os.pathsep)
    for each in paths:
        if not each.endswith("%B"):
            continue
        icon = each.replace("%B", name)
        if os.path.exists(icon):
            return icon
    return ""


def create_module_callback(source):
    """Set the command for each buttons.

    Args:
        source (str): Source python code to execute.

    Returns:
        function: A callable function
    """
    if not source:
        return None

    # build a python function to keep it in an isolated scope
    _source = "".join("    " + line for line in source.splitlines(True))
    command = "def _callback():\n{0}".format(_source)

    # execute the callback and extract the callable function from it
    exec(command)  # pylint: disable=exec-used
    callback = locals()["_callback"]

    # add to shared variable
    cfg.COMMAND_CALLBACK = callback

    return callback


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
        return data

    with open(path) as stream:
        data = yaml.load(stream, **kwargs)

    return data


class Loader(yaml.Loader):
    """Create a custom YAML Loader to load data in an OrderedDict."""

    def __init__(self, *args, **kwargs):
        super(Loader, self).__init__(*args, **kwargs)
        self.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            self.dict_constructor,
        )

    @staticmethod
    def dict_constructor(loader, node):
        """Create a custom constructor for yaml loader."""
        return OrderedDict(loader.construct_pairs(node))


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

    with open(path, "w") as stream:
        yaml.dump(data, stream, **kwargs)

    return path


class Dumper(yaml.Dumper):
    """Create a custom YAML Dumper to dump data from an OrderedDict."""

    def __init__(self, *args, **kwargs):
        super(Dumper, self).__init__(*args, **kwargs)
        rpz = yaml.representer.SafeRepresenter
        self.add_representer(OrderedDict, self.dict_representer)
        self.add_representer(str, rpz.represent_str)
        self.add_representer(six.string_types, rpz.represent_unicode)

    @staticmethod
    def dict_representer(dumper, data):
        """Create a custom representer for yaml dumper."""
        return dumper.represent_dict(data.iteritems())
