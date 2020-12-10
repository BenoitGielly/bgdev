"""Utility methods for rivets.

:created: 15/01/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging
import re

import bgdev.utils.decorator
import bgdev.utils.name
from maya import cmds
from maya.api import OpenMaya

LOG = logging.getLogger(__name__)


def follicle_rivet_callback():
    """Create rivets based on selection."""
    selection = cmds.ls(selection=True, flatten=True)
    for each in selection:
        follicle_rivet(vertex=each)


@bgdev.utils.decorator.UNDO_REPEAT
def follicle_rivet(vertex=None, name=None):
    """Create a rivetted locator using follicle.

    Args:
        vertex (str): Specify a vertex to attach the rivet to.
            Use selection otherwise.
        name (str): Using this name for the rivet if passed, otherwise create
            one using the mesh name.

    Returns:
        str: The rivet locator created.

    """
    # create a rivet group to parent them.
    rivet_grp = "follicle_rivet_GRP"
    if not cmds.objExists(rivet_grp):
        rivet_grp = cmds.createNode("transform", name=rivet_grp)

    # make sure the component is a vertex
    if not cmds.filterExpand(vertex, selectionMask=31):
        return LOG.error("You must select a vertex-type component!")

    vertex_id = int(re.findall(r"\d+", vertex)[-1])
    mesh = vertex.rsplit(".")[0]

    # create locator and follicle
    name = name or mesh + "_rivet"
    name = bgdev.utils.name.generate_unique_name(name)
    locator = cmds.spaceLocator(name=name)[0]
    follicle = cmds.createNode(
        "follicle", name=locator + "Follicle", parent=locator
    )

    # get uv coordinate of vertex
    node_dag = OpenMaya.MSelectionList().add(mesh).getDagPath(0)
    mfn_mesh = OpenMaya.MFnMesh(node_dag)
    point = mfn_mesh.getPoints()[vertex_id]
    uvs = mfn_mesh.getUVAtPoint(point)

    # set follicle attributes and connections
    cmds.setAttr(follicle + ".parameterU", uvs[0])
    cmds.setAttr(follicle + ".parameterV", uvs[1])
    cmds.connectAttr(mesh + ".outMesh", follicle + ".inputMesh")
    cmds.connectAttr(mesh + ".worldMatrix[0]", follicle + ".inputWorldMatrix")

    # create matrix nodes to drive the rivet locator
    mcp = cmds.createNode("composeMatrix", name=name + "_composeMatrix")
    mmlt = cmds.createNode("multMatrix", name=name + "_multMatrix")
    mdcp = cmds.createNode("decomposeMatrix", name=name + "_decomposeMatrix")

    cmds.connectAttr(follicle + ".outTranslate", mcp + ".inputTranslate")
    cmds.connectAttr(follicle + ".outRotate", mcp + ".inputRotate")
    cmds.connectAttr(mesh + ".scale", mcp + ".inputScale")
    cmds.connectAttr(mcp + ".outputMatrix", mmlt + ".matrixIn[0]")
    cmds.connectAttr(
        locator + ".parentInverseMatrix[0]", mmlt + ".matrixIn[1]"
    )
    cmds.connectAttr(mmlt + ".matrixSum", mdcp + ".inputMatrix")
    cmds.connectAttr(mdcp + ".outputTranslate", locator + ".translate")
    cmds.connectAttr(mdcp + ".outputRotate", locator + ".rotate")
    cmds.connectAttr(mdcp + ".outputScale", locator + ".scale")

    # cleanup
    cmds.parent(locator, rivet_grp)
    cmds.setAttr(locator + ".localScale", 0.1, 0.1, 0.1)

    return locator
