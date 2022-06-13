"""Utility methods for meshes.

:created: 05/03/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

import bgdev.utils.decorator
from maya import cmds
from maya.api import OpenMaya

LOG = logging.getLogger(__name__)


def mesh_combine_and_keep(nodes, name, visible=True):
    """Combine meshes and keep the original."""
    combined, unite = cmds.polyUnite(nodes, constructionHistory=True)
    combined = cmds.rename(combined, name + "_combined")
    unite = cmds.rename(unite, name + "_polyUnite")

    # turn shapes back on and parent them under their original transform
    for each in nodes:
        transform = cmds.listRelatives(each, children=True)[0]
        shape = cmds.listRelatives(transform, shapes=True)[0]
        cmds.parent(shape, each, relative=True, shape=True)
        cmds.setAttr(shape + ".intermediateObject", False)
        cmds.delete(transform)
        cmds.setAttr(shape + ".visibility", visible)

    return combined


@bgdev.utils.decorator.UNDO
def mesh_reorder_callback():
    """Reorder or remap vertices of selected mesh(es)."""
    cmds.loadPlugin("meshReorder", quiet=True)

    if not cmds.selectPref(query=True, trackSelectionOrder=True):
        cmds.selectPref(trackSelectionOrder=True)
        cmds.select(clear=True)
        LOG.warning(
            'Turning on the "Track selection order" option. '
            "Please, select your vertices again!"
        )
        return

    vertice = cmds.ls(orderedSelection=True, flatten=True)
    if len(vertice) == 3:
        cmds.meshReorder(*vertice)
    elif len(vertice) == 6:
        cmds.meshRemap(*vertice)
    else:
        LOG.error("Please, select 3 vertices of one or each meshes")


@bgdev.utils.decorator.UNDO
def find_phantom_vertices(fix=False):
    """Find meshes with incorrect amount of vertices.

    Args:
        fix (bool): Apply a fix to remove phantom vertices when True.

    """
    if cmds.objExists("PHANTOM_VERTICES_SET"):
        cmds.delete("PHANTOM_VERTICES_SET")

    bad_meshes = []
    it_meshes = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kMesh)
    while not it_meshes.isDone():
        dag = OpenMaya.MDagPath.getAPathTo(it_meshes.thisNode())
        it_vertice = OpenMaya.MItMeshVertex(dag)
        while not it_vertice.isDone():
            if not it_vertice.getConnectedEdges():
                bad_meshes.append(dag.fullPathName())
            it_vertice.next()
        it_meshes.next()

    if not bad_meshes:
        LOG.info("Scene seems clean, well done!")
        return

    if not fix:
        cmds.sets(bad_meshes, name="PHANTOM_VERTICES_SET")
        LOG.info("Phantom vertices found, adding the meshes to a set!")
        return

    # a "safe" way to cleanup the phantom vertices is to extrude one edge
    # and removing the face it has created.
    for each in bad_meshes:
        cmds.polyExtrudeEdge(
            "{0}.e[1]".format(each),
            translateZ=True,
            constructionHistory=False,
        )

        face_id = cmds.polyEvaluate(each, face=True) - 1
        cmds.delete(
            "{}.f[{}]".format(each, face_id), constructionHistory=False
        )
