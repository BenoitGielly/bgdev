"""API methods for blendshapes.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya.api import OpenMaya

from . import core


def get_input_geometry(deformer):
    """Get input geometries affected by given deformer."""
    result = []
    filter_ = core.as_filter(deformer)
    for each in filter_.getInputGeometry() or []:
        result.append(OpenMaya.MDagPath.getAPathTo(each).partialPathName())
    return result


def get_output_geometry(deformer):
    """Get output geometries affected by given deformer."""
    result = []
    filter_ = core.as_filter(deformer)
    for each in filter_.getOutputGeometry() or []:
        result.append(OpenMaya.MDagPath.getAPathTo(each).partialPathName())
    return result
