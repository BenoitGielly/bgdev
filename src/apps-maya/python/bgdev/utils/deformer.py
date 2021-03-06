"""Utility methods for deformers.

:created: 28/05/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

import bgdev.utils.decorator
from maya import cmds
from maya.api import OpenMaya

LOG = logging.getLogger(__name__)


@bgdev.utils.decorator.UNDO_REPEAT
def update_lattice_callback(add=True):
    """Call back :func:`update_lattice`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")
        return

    nodes, lattice = selection[:-1], selection[-1]
    for each in nodes:
        update_lattice(each, lattice, add=add)


def update_lattice(node, lattice, add=True):
    """Add or remove node from lattice.

    Args:
        node (str): The node to add into the existing lattice.
        lattice (str): The lattice (ffd) node.
        add (bool): True node to lattice if True, else remove it.

    """
    shape = cmds.listRelatives(lattice, shapes=True, type="lattice")
    if shape:
        ffd = cmds.listConnections(shape[0], type="ffd")
        if ffd:
            cmds.lattice(ffd[0], edit=True, geometry=node, remove=not add)


def transfer_base_weights_api(source, target, src_joint=0, tgt_joint=0):
    """Transfer weights from source to target using OpenMaya.

    Args:
        source (str): Source deformer
        target (str): Target deformer
        joint (int): Index of joint in skinCluster

    """
    weight_plug = {
        "blendShape": "{}.inputTarget[0].inputTargetGroup[0].targetWeights[{}]",
        "nonLinear": "{}.weightList[0].weights[{}]",
        "cluster": "{}.weightList[0].weights[{}]",
        "ffd": "{}.weightList[0].weights[{}]",
        "skinCluster": "{}.weightList[{}].weights[{}]",
    }

    shape = cmds.findType(source, type="mesh")[0]
    mesh = cmds.listRelatives(shape, parent=True)[0]
    source_type, target_type = cmds.nodeType(source), cmds.nodeType(target)
    mesh_sel = OpenMaya.MGlobal.getSelectionListByName(mesh)
    mesh_dag = mesh_sel.getDagPath(0)
    mesh_mfn = OpenMaya.MFnMesh(mesh_dag)
    vertices = set(mesh_mfn.getVertices()[-1])
    for i in vertices:
        plug_selection = OpenMaya.MSelectionList()
        args = [i, src_joint] if source_type == "skinCluster" else [i]
        plug_selection.add(weight_plug[source_type].format(source, *args))
        args = [i, tgt_joint] if target_type == "skinCluster" else [i]
        plug_selection.add(weight_plug[target_type].format(target, *args))
        value = plug_selection.getPlug(0).asFloat()
        plug_selection.getPlug(1).setFloat(value)


def transfer_base_weights(source, target, joint=0):
    """Transfer weights from source to target.

    Args:
        source (str): Source deformer
        target (str): Target deformer
        joint (int): Index of joint in skinCluster

    """
    weight_plugs = {
        "wire": "{}.weightList[0].weights[{}]",
        "nonLinear": "{}.weightList[0].weights[{}]",
        "skinCluster": "{}.weightList[{}].weights[{}]",
        "blendShape": "{}.inputTarget[0].baseWeights[{}]",
    }

    mesh = cmds.listConnections(source, type="mesh")[0]
    vertices = sorted(cmds.ls("{}.vtx[*]".format(mesh), flatten=True))
    for i, _ in enumerate(vertices):

        # get weights from source
        node_type = cmds.nodeType(source)
        if node_type == "skinCluster":
            attr = weight_plugs[node_type].format(source, i, joint)
        else:
            attr = weight_plugs[node_type].format(source, i)
        value = cmds.getAttr(attr)

        # set weights on target
        node_type = cmds.nodeType(target)
        if node_type == "skinCluster":
            attr = weight_plugs[node_type].format(target, i, joint)
        else:
            attr = weight_plugs[node_type].format(target, i)
        cmds.setAttr(attr, value)
