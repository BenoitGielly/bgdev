"""OpenMaya API core wrappers.

Note:
    Mostly uses API2

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya.api import OpenMaya


def obj_exists(obj):
    """Check if objExists using OpenMaya."""
    try:
        as_selection(obj)
        return True
    except RuntimeError:
        return False


def as_selection(name):
    """Get name as MSelectionList."""
    selection = OpenMaya.MSelectionList()
    selection.add(name)
    return selection


def as_obj(name):
    """Get name as MObject."""
    if hasattr(name, "node"):
        return getattr(name, "node")()
    return OpenMaya.MObject(as_selection(name).getDependNode(0))


def as_dag(dag, to_shape=False):
    """Get name as MDagPath."""
    if not isinstance(dag, OpenMaya.MDagPath):
        dag = OpenMaya.MDagPath(as_selection(dag).getDagPath(0))
    if to_shape:
        dag.extendToShape()
    return dag


def as_plug(plug):
    """Get name as MPlug."""
    if isinstance(plug, OpenMaya.MPlug):
        return plug
    return OpenMaya.MPlug(as_selection(plug).getPlug(0))


def as_node(name):
    """Get name as MFnDependencyNode."""
    return OpenMaya.MFnDependencyNode(as_obj(name))


def as_mesh(name):
    """Get name as MFnMesh."""
    return OpenMaya.MFnMesh(as_dag(name))
