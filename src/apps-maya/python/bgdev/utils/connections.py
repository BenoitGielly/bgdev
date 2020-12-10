"""
:created: 2017-03-10
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import print_function

from maya import cmds
import pymel.core as pm


def quick_connections():
    """Quickly connect transforms."""
    selection = cmds.ls(sl=1)
    msg = "Type the attribute names you want to quickly connect together :"
    result = cmds.promptDialog(title="Quick connections", message=msg)
    if result:
        trs = cmds.promptDialog(q=1, tx=1)
        for each in selection[1:]:
            if "t" in trs:
                if "x" in trs:
                    cmds.connectAttr(selection[0] + ".tx", each + ".tx")
                if "y" in trs:
                    cmds.connectAttr(selection[0] + ".ty", each + ".ty")
                if "z" in trs:
                    cmds.connectAttr(selection[0] + ".tz", each + ".tz")
                if not ("x" in trs or "y" in trs or "z" in trs):
                    cmds.connectAttr(selection[0] + ".t", each + ".t")

            if "r" in trs:
                if "x" in trs:
                    cmds.connectAttr(selection[0] + ".rx", each + ".rx")
                if "y" in trs:
                    cmds.connectAttr(selection[0] + ".ry", each + ".ry")
                if "z" in trs:
                    cmds.connectAttr(selection[0] + ".rz", each + ".rz")
                if not ("x" in trs or "y" in trs or "z" in trs):
                    cmds.connectAttr(selection[0] + ".r", each + ".r")

            if "s" in trs:
                if "x" in trs:
                    cmds.connectAttr(selection[0] + ".sx", each + ".sx")
                if "y" in trs:
                    cmds.connectAttr(selection[0] + ".sy", each + ".sy")
                if "z" in trs:
                    cmds.connectAttr(selection[0] + ".sz", each + ".sz")
                if not ("x" in trs or "y" in trs or "z" in trs):
                    cmds.connectAttr(selection[0] + ".s", each + ".s")

            if "j" in trs:
                cmds.connectAttr(selection[0] + ".jo", each + ".jo")

            if "v" in trs:
                cmds.connectAttr(selection[0] + ".v", each + ".v")


def pairblend_three_nodes():
    """Create pairblend between three nodes."""
    # make sure selection order is active
    pref = pm.selectPref(query=True, trackSelectionOrder=True)
    if not pref:
        pm.selectPref(trackSelectionOrder=True)
        msg = "Turning on 'Selection-Order Tracking' option."
        msg += "You need to re-do your selection !"
        pm.error(msg)

    # get selection in order
    selection = pm.ls(os=1)

    # create pairBlend
    name = (
        selection[-1].name().rpartition("|")[-1].rpartition("_")[0]
        or selection[-1].rpartition("|")[-1]
    )
    pblend = pm.createNode("pairBlend", name=name + "_pairBlend")

    # pylint: disable=pointless-statement
    # connect pairBlend
    selection[0].translate >> pblend.inTranslate1
    selection[1].translate >> pblend.inTranslate2
    pblend.outTranslate >> selection[2].translate

    selection[0].rotate >> pblend.inRotate1
    selection[1].rotate >> pblend.inRotate2
    pblend.outRotate >> selection[2].rotate

    # create weight attribute
    if not selection[-1].hasAttr("weight"):
        selection[-1].addAttr(
            "weight", at="double", min=0, max=1, keyable=True
        )
    selection[-1].weight >> pb.weight

    pm.select(selection)
