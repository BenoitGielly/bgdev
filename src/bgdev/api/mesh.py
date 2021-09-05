"""API methods for meshes.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya import cmds
from maya.api import OpenMaya

from . import core


def duplicate_mesh(geometry, name="temp"):
    """Duplicate given geometry using Maya API."""
    root = cmds.createNode("transform", name=name)
    mesh = core.as_mesh(geometry)
    mesh.copy(mesh.object(), core.as_obj(root))
    mesh.setName(name + "Shape")
    return root


def get_point_array(mesh):
    """Get all vertices position of given mesh."""
    return core.as_mesh(mesh).getPoints()


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
