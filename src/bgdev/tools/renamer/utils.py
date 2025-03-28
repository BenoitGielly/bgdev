"""Utils function for the renamer.

:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import inspect
import os
from functools import partial
from functools import wraps
from traceback import print_exc

from qtpy import QtCore
from qtpy import QtGui


def _undo_me(func, args, kwargs):
    from maya import cmds

    cmds.undoInfo(openChunk=True)
    func_return = None
    try:
        func_return = func(*args, **kwargs)
    except BaseException:
        print_exc()
    finally:
        cmds.undoInfo(closeChunk=True)
    return func_return


def method_decorator(func, undo=False):  # noqa
    """Decorate a method to make it undoable."""

    @wraps(func)
    def decorator(*args, **kwargs):
        """Actual method being run."""
        if undo:
            func_return = _undo_me(func, args, kwargs)
        else:
            func_return = func(*args, **kwargs)
        return func_return

    return decorator


UNDO = partial(method_decorator, undo=True)


def check_image(icon, normalized=False, as_icon=False):
    """Convert the given image path to full path name.

    Args:
        icon (str): Name of the icon to check
        normalized (bool): Normalize the path to slash forward (works on all OS)
        as_icon (bool): Return a QIcon of the found image file.

    Returns:
        str: Updated icon path so it's ready to be used.

    """
    # create a list of paths to lookup icons
    icon_paths = []
    for each in (inspect.stack()[1][1], __file__):
        icon_folder = os.path.join(os.path.dirname(each), "icons")
        if os.path.exists(icon_folder):
            icon_paths.append(icon_folder)

    # check for relatives path icons
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
        return None

    # normalize the path for windows
    icon = icon.replace(os.sep, "/") if normalized else icon

    # return as icon
    if as_icon:
        icon = QtGui.QIcon(icon)

    return icon
