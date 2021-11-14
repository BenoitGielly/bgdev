"""Utility fonctions for UI.

:created: 8/02/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>

"""
import importlib
import inspect
import os
import pkgutil
import sys

from PySide2 import QtCore, QtGui, QtWidgets
import shiboken2


def main_window():
    """Return the QMainWindow for the current application."""
    # case: Maya
    if pkgutil.find_loader("maya"):
        for obj in QtWidgets.QApplication.topLevelWidgets():
            if obj.objectName() == "MayaWindow":
                return obj

    # case: Houdini
    if pkgutil.find_loader("hou"):
        module = importlib.import_module("hou")
        return getattr(module.qt, "mainWindow")()

    # case: Nuke
    if pkgutil.find_loader("nuke"):
        for obj in QtWidgets.QApplication.topLevelWidgets():
            cls_name = obj.metaObject().className()
            inherits = obj.inherits("QMainWindow")
            if inherits and cls_name == "Foundry::UI::DockMainWindow":
                return obj

    return None


def in_maya():
    """Check if we are in Maya or not.

    Return:
        bool: True if in maya else False
    """
    return "maya.bin" in sys.argv[0]


def maya_window():
    """Get Maya MainWindow as Qt.

    Returns:
        QtWidgets.QWidget: Maya main window as QtObject

    """
    return to_qwidget("MayaWindow")


def to_qwidget(ctrl):
    """Convert a Maya widget to a PySide2 QWidget.

    Args:
        ctrl (str): Name of the maya widget as a string.

    Returns:
        QtWidgets.QWidget: QWidget instance object of the given widget.
    """
    from maya import OpenMayaUI

    for method in ["findControl", "findLayout", "findMenuItem"]:
        ptr = getattr(OpenMayaUI.MQtUtil, method)(ctrl)
        if ptr:
            try:
                ptr = long(ptr)
            except NameError:
                ptr = int(ptr)
            return shiboken2.wrapInstance(ptr, QtWidgets.QWidget)
    return None


def generate_qrc(path, name="resources", prefix="icons"):
    """Generate .qrc file based on given folder.

    Args:
        path (str): Path to icons folder.
        name (str): Name of the qrc file to generate. Default is "resources".
        prefix (str): Name of the icon prefix. Default is "icons".

    Returns:
        str: Path to the generated [qrc].py file.
    """
    qrc = '<RCC>\n\t<qresource prefix="{}">\n'.format(prefix)
    for each in sorted(os.listdir(path)):
        qrc += "\t\t<file>{0}</file>\n".format(each)
    qrc += "\t</qresource>\n</RCC>\n"

    qrc_file = os.path.join(path, name + ".qrc")
    with open(qrc_file, "w") as stream:
        stream.write(qrc)

    return qrc_file


def check_image(icon, normalized=True, as_icon=False):
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
