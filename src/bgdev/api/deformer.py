"""API methods for blendshapes.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya.api import OpenMaya, OpenMayaAnim

from . import core


def as_filter(deformer):
    """Get deformer as GeometryFilter."""
    return OpenMayaAnim.MFnGeometryFilter(core.as_obj(deformer))


def get_output_geometry(deformer):
    """Get output geometries affected by given deformer."""
    result = []
    for each in as_filter(deformer).getOutputGeometry() or []:
        result.append(OpenMaya.MDagPath.getAPathTo(each).partialPathName())
    return result
