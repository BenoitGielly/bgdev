"""Utility methods for skinclusters.

:created: 26/02/2017
:author: Benoit Gielly <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

from maya import cmds, mel

import bgdev.utils.decorator
import bgdev.utils.shape

LOG = logging.getLogger(__name__)

SKINCLUSTER_SETTINGS = {
    "toSelectedBones": True,
    "bindMethod": 0,
    "skinMethod": 2,
    "normalizeWeights": 1,
    "weightDistribution": 1,
    "maximumInfluences": 3,
    "obeyMaxInfluences": True,
    "dropoffRate": 4.0,
    "removeUnusedInfluence": False,
}


def get_skincluster(node):
    """Return the skincluster of given node.

    If the passed node already is a skincluster, just return it.

    Args:
        node (str): Can be either the skincluster or the bound node.

    Raises:
        RuntimeError: If the skincluster cannot be found.

    Returns:
        str: The skincluster bound to the node.

    """
    skincluster = None
    if cmds.nodeType(node) != "skinCluster":
        skincluster = mel.eval("findRelatedSkinCluster {0}".format(node))

    if not skincluster:
        skinclusters = set()
        for each in cmds.ls(node, dagObjects=True):
            connections = cmds.listConnections(each, type="skinCluster") or []
            skinclusters.update(connections)
        if skinclusters:
            skincluster = sorted(skinclusters)[0]

    if skincluster and cmds.nodeType(skincluster) == "skinCluster":
        return skincluster
    return None


def get_influences(node, weighted=False):
    """Get influences of given skincluster.

    Args:
        node (str): Can be either the skincluster or the bound node.
        weighted (bool): If True, returns only weighted influences.

    Returns:
        list: List of influences.

    Raises:
        RuntimeError: If the skincluster cannot be found.
    """
    skc = get_skincluster(node)
    if not skc:
        raise RuntimeError("Couldn't find a skincluster.")

    flags = {"influence": True}
    if weighted:
        flags = {"weightedInfluence": True}
    influences = cmds.skinCluster(skc, query=True, **flags) or []

    return influences


@bgdev.utils.decorator.UNDO_REPEAT
def add_influences_callback():
    """Call back :func:`add_influences`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")
        return

    joints, node = selection[:-1], selection[-1]
    add_influences(node, joints)
    cmds.select(selection)


def add_influences(node, joints):
    """Add given joints to the skincluster.

    Args:
        node (str): Can be either the skincluster or the bound node.
        joints (list): List of joints/influences to add.

    Raises:
        RuntimeError: If the skincluster cannot be found.
    """
    # add each targets to the skincluster
    skincluster = get_skincluster(node)
    if not skincluster:
        raise RuntimeError("Couldn't find a skincluster.")

    influences = get_influences(skincluster)
    for each in joints:
        if each not in influences:
            cmds.skinCluster(
                skincluster, edit=True, addInfluence=each, weight=0
            )


@bgdev.utils.decorator.UNDO_REPEAT
def remove_influences_callback(unused=False):
    """Call back :func:`remove_influences`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 1 node!")
        return

    if unused:
        for node in selection:
            remove_influences(node, unused=True)
    else:
        joints, node = selection[:-1], selection[-1]
        remove_influences(node, joints)


def remove_influences(node, joints=None, unused=False, disconnect=False):
    """Remove given joints from the skincluster.

    Args:
        node (str): Can be either the skincluster or the bound node.
        joints (list): List of joints/influences to add.
        unused (bool): Removed all unused influences found.
            This flag ignores `joints` when used.

    Raises:
        RuntimeError: If the skincluster cannot be found.
    """
    # add each targets to the skincluster
    skc = get_skincluster(node)
    if not skc:
        LOG.warning("Couldn't find a skincluster onto %s.", node)
        return

    influences = get_influences(skc)
    if unused:
        weighted = get_influences(skc, weighted=True)
        joints = list(set(influences) - set(weighted))
        LOG.info("Found %s influences to remove in %s", len(joints), skc)

    for each in joints:
        if each not in influences:
            continue
        if disconnect:
            index = influences.index(each)
            plug = "{}.matrix[{}]".format(skc, index)
            value = cmds.getAttr(plug)
            cmds.disconnectAttr(each + ".worldMatrix", plug)
            cmds.setAttr(plug, value, type="matrix")
            continue
        cmds.skinCluster(skc, edit=True, removeInfluence=each)


@bgdev.utils.decorator.UNDO_REPEAT
def select_influences_callback():
    """Call back :func:`select_influences`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 1 node!")
        return

    influences = []
    for each in selection:
        influences.extend(get_influences(each))
    cmds.select(influences)


@bgdev.utils.decorator.UNDO_REPEAT
def bind_skincluster_callback():
    """Call back :func:`bind_skincluster`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 1 node!")
        return

    joints = {_ for _ in selection if cmds.nodeType(_) == "joint"}
    nodes = set(selection) - joints
    for each in nodes:
        bind_skincluster(each, list(joints))

    cmds.select(selection)


def bind_skincluster(mesh=None, bones=None):
    """Create a new skincluster with preset options.

    Args:
        mesh (str): Name of the geometry to bind.
        bones (list): List of bones/influences.

    Returns:
        str: The created skincluster.
    """
    shapes = []

    # create a default dictionnary to store the best settings for a skincluster
    default_settings = dict(SKINCLUSTER_SETTINGS)

    # if a mesh is given, rename the skincluster accordingly
    if mesh:
        default_settings["name"] = "{0}_skinCluster".format(mesh)

    # bind the mesh to the skincluster
    if mesh and bones:
        skc = cmds.skinCluster(bones, mesh, **default_settings)[0]
    else:
        # assumes that only one geometry is selected (errors otherwise)
        skc = cmds.skinCluster(**default_settings)[0]

        # retrieve the shape and its transform used to bind
        shapes = cmds.skinCluster(skc, query=True, geometry=True)
        mesh = cmds.listRelatives(shapes, parent=True)[0]
        skc = cmds.rename(skc, "{0}_skinCluster".format(mesh))

    # rename tweak
    shapes = shapes or bgdev.utils.shape.get_shapes(mesh)
    if shapes:
        tweak = cmds.listConnections(shapes[0], source=True, type="tweak")
        if tweak:
            cmds.rename(tweak, "{0}_tweak".format(mesh))

    return skc


@bgdev.utils.decorator.UNDO_REPEAT
def copy_skincluster_callback(method="closestPoint"):
    """Call back :func:`copy_skincluster`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")
        return

    source, targets = selection[0], selection[1:]
    for target in targets:
        copy_skincluster(source, target, method)

    cmds.select(selection)


def copy_skincluster(source, target, method="closestPoint"):
    """Copy source skincluster onto target and keep same weights.

    Args:
        source (str): source mesh to copy skincluster form
        target (str): target mesh to paste skincluster to
        method (str): influence association method. Default is closestPoint.

    Raises:
        RuntimeError: If the source skincluster cannot be found.
    """
    copy_settings = {
        # "influenceAssociation": ["oneToOne", "closestJoint", "closestBone"],
        "influenceAssociation": ["closestJoint", "closestBone", "oneToOne"],
        "sampleSpace": 0,
        "noMirror": True,
        "smooth": True,
    }

    # get skinclusters and influences
    source_skc = get_skincluster(source)
    if not source_skc:
        raise RuntimeError("Couldn't find a source skincluster.")

    source_infs = cmds.skinCluster(source_skc, query=True, influence=True)
    infs_objects = [_ for _ in source_infs if cmds.nodeType(_) != "joint"]
    source_infs = [_ for _ in source_infs if _ not in infs_objects]

    # add influences if skincluster already exists
    target_infs = None
    target_skc = get_skincluster(target)
    if target_skc:
        target_infs = cmds.skinCluster(target_skc, query=True, influence=True)
        diff_influences = set(source_infs + infs_objects) - set(target_infs)
        if diff_influences:
            cmds.skinCluster(
                target_skc, edit=True, addInfluence=list(diff_influences)
            )

    # create skincluster otherwise
    else:
        name = "{}_skinCluster".format(target).rsplit("|")[-1]
        name = name + "#" if cmds.objExists(name) else name
        skc_settings = dict(bgdev.utils.skincluster.SKINCLUSTER_SETTINGS)
        skc_settings["skinMethod"] = cmds.skinCluster(
            source_skc, query=True, skinMethod=True
        )
        skc_settings["normalizeWeights"] = cmds.skinCluster(
            source_skc, query=True, normalizeWeights=True
        )
        target_skc = cmds.skinCluster(
            source_infs, target, name=name, **skc_settings
        )[0]

        if infs_objects:
            cmds.skinCluster(target_skc, edit=True, addInfluence=infs_objects)

    # copy skincluster weights
    if method == "uv":
        copy_settings["uvSpace"] = ["map1", "map1"]
    else:
        copy_settings["surfaceAssociation"] = method

    cmds.copySkinWeights(
        sourceSkin=source_skc, destinationSkin=target_skc, **copy_settings
    )


@bgdev.utils.decorator.UNDO_REPEAT
def reset_skincluster_callback():
    """Call back :func:`reset_skincluster`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 1 node!")
        return

    for each in selection:
        reset_skincluster(each)


def reset_skincluster(node):
    """Reset the skin cluster in place.

    Args:
        node (str): SkinCluster node or the geometry bound to it.

    """
    # get skinclusters
    skincluster = node
    if cmds.nodeType(node) != "skinCluster":
        skincluster = mel.eval("findRelatedSkinCluster {0}".format(node))

    # detach skinclusters
    influences = cmds.skinCluster(skincluster, query=True, influence=True)
    for i, influence in enumerate(influences):

        # reset bindPreMatrix for each joints
        matrix = cmds.getAttr(influence + ".worldInverseMatrix")
        cmds.setAttr(
            "{0}.bindPreMatrix[{1}]".format(skincluster, i),
            matrix,
            type="matrix",
        )
        cmds.skinCluster(skincluster, edit=True, recacheBindMatrices=True)

        # reset dagPose
        dag_poses = cmds.listConnections(
            skincluster, source=True, type="dagPose"
        )
        for each in dag_poses:
            cmds.dagPose(influence, reset=True, name=each)


@bgdev.utils.decorator.UNDO_REPEAT
def detach_skincluster_callback(clean=False):
    """Call back :func:`detach_skincluster`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 1 node!")
        return

    for each in selection:
        detach_skincluster(each, clean)


def detach_skincluster(node, clean=False):
    """Detach the skin cluster attached to given node.

    Args:
        node (str): Name of the node to unbind.
        clean (bool): If True, remove shapeOrigs and unlock transforms.

    """
    # detach skincluster
    if get_skincluster(node):
        cmds.skinCluster(node, edit=True, unbind=True)
        cmds.refresh()

    if not clean:
        return

    # make sure there's no other deformers before cleaning up
    for each in cmds.listHistory(node, levels=1):
        if "geometryFilter" in cmds.nodeType(each, inherited=True):
            LOG.info(
                "Other deformers than skincluster found. Skipping cleanup..."
            )
            return

    # delete shapeOrig
    shapes = bgdev.utils.shape.get_shapes(node, True, True)
    if shapes:
        cmds.delete(shapes)

    # unlock transforms (if detach skincluster didn't do it)
    for attr in [x + y for x in "trs" for y in "xyz"]:
        cmds.setAttr("{0}.{1}".format(node, attr), lock=False)
