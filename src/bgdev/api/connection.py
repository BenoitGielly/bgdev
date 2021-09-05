"""API methods for dis/connecting attributes.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya.api import OpenMaya

from . import core


def disconnect_all_plugs(name, source=True, destination=True):
    """Disconnect all inputs and/or outputs of given node."""
    modifier = OpenMaya.MDagModifier()
    for plug in core.as_node(name).getConnections():
        if source and plug.isDestination:
            modifier.disconnect(plug.source(), plug)
        if destination and plug.isSource:
            for each in plug.destinations():
                modifier.disconnect(plug, each)
    modifier.doIt()
