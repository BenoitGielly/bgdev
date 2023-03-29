"""Cleanup utilites.

:created: 05/01/2023
:author: Benoit GIELLY <bgielly@stimstudio.com>
"""
import logging

from maya import cmds, mel

LOG = logging.getLogger(__name__)


def cleanup(unused_nodes=False, unknown_nodes=True, unknown_plugins=True):
    """Cleanup the scene from unused and unknown nodes and plugins."""
    if unknown_nodes:
        delete_unknown_nodes()
    if unknown_plugins:
        delete_unknown_plugins()
    if unused_nodes:
        delete_unused_nodes()
    LOG.warning("Scene clean !")


def delete_unknown_nodes():
    """Delete unknown nodes from scene."""
    for each in cmds.ls(type="unknown") or []:
        if not cmds.objExists(each):
            continue
        cmds.lockNode(each, lock=False)
        cmds.delete(each)
        LOG.info("Removed unknown node: %s", each)


def delete_unknown_plugins():
    """Delete unknown plugins from scene."""
    for each in cmds.unknownPlugin(query=True, list=True) or []:
        cmds.unknownPlugin(each, remove=True)
        LOG.info("Removed unknown plugin: %s", each)


def delete_unused_nodes():
    """Remove unused nodes."""
    mel.eval("MLdeleteUnused;")
    LOG.info("Removed unused nodes!")


def list_namespaces():
    """List all namespaces in current scene."""
    namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
    namespaces = [x for x in namespaces if not x in ("shared", "UI")]
    namespaces.sort(key=lambda x: x.count(":"), reverse=True)
    return namespaces


def remove_namespaces():
    """Remove all namespaces from current scene."""
    cmds.namespace(setNamespace=":")
    namespaces = list_namespaces()
    for each in namespaces:
        if cmds.namespace(exists=each):
            cmds.namespace(removeNamespace=each, mergeNamespaceWithRoot=True)
