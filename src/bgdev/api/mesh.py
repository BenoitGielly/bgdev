"""API methods for meshes.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya import cmds
from maya.api import OpenMaya

from . import core


def duplicate_mesh(geometry, name="temp", parent=None, material=False):
    """Duplicate given geometry using Maya API."""
    flags = {"parent": parent} if parent else {}
    root = cmds.createNode("transform", name=name, **flags)
    mesh = core.as_mesh(geometry)
    mesh.copy(mesh.object(), core.as_obj(root))
    mesh.setName(name + "Shape")
    if material:
        cmds.sets(name, edit=True, forceElement="initialShadingGroup")
    return root


def get_point_array(mesh):
    """Get all vertices position of given mesh."""
    return core.as_mesh(mesh).getPoints()


def get_point_deltas(array1, array2):
    """Return the delta of each point from the first to the second array.

    Args:
        array1 (OpenMaya.MPointArray): The points array of the first mesh.
        array2 (OpenMaya.MPointArray): The points array of the second mesh.

    Returns:
        list: Every delta for each points.
    """
    return [abs(i.distanceTo(j)) for i, j in zip(array1, array2)]


def calculate_delta(base, shape, minus):
    """Find new point position by calculating deltas.

    Args:
        base (str): Name of the base/reference mesh. (Usually shapeOrig)
        shape (str): Name of shape whose points will be added onto the base.
        minus (str): Name of shape whose points will be subbed from the base.

    Returns:
        OpenMaya.MPointArray: The new MPointArray after delta are applied.

    """
    # pylint: disable=invalid-name
    base_array = OpenMaya.MVectorArray(get_point_array(base))
    shape_array = OpenMaya.MVectorArray(get_point_array(shape))
    minus_array = OpenMaya.MVectorArray(get_point_array(minus))
    delta = OpenMaya.MPointArray()
    for A, B, C in zip(base_array, shape_array, minus_array):
        delta.append(A + (B - A) - (C - A))
    return delta
