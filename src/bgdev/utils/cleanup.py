"""Cleanup utilites.

:created: 05/01/2023
:author: Benoit GIELLY <bgielly@stimstudio.com>
"""
import logging

from maya import cmds, mel

LOG = logging.getLogger(__name__)


def cleanup(delete_unused=False):
    """Cleanup the scene from unknown nodes and plugins."""
    # remove unknown nodes
    for each in cmds.ls(type="unknown") or []:
        if cmds.objExists(each):
            cmds.lockNode(each, lock=False)
            cmds.delete(each)
            LOG.info("Deleted unknown node: %s", each)

    # remove unknown plugins
    for each in cmds.unknownPlugin(query=True, list=True) or []:
        cmds.unknownPlugin(each, remove=True)
        LOG.info("Unloading unknown plugin: %s", each)

    if delete_unused:
        mel.eval("MLdeleteUnused;")

    LOG.warning("Scene clean !")


def delete_unused_nodes():
    """Remove unused nodes after cleanup."""
    cleanup(delete_unused=True)


def list_namespaces():
    """List all namespaces in current scene."""
    namespaces = []
    for each in cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True):
        if each not in ["UI", "shared"]:
            namespaces.append(each)
    return reversed(namespaces)


def remove_namespaces():
    """Remove all namespaces from current scene."""
    namespaces = list_namespaces()
    for each in namespaces:
        if cmds.namespace(exists=each):
            cmds.namespace(removeNamespace=each, mergeNamespaceWithRoot=True)
