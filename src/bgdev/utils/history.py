"""Utility methods to deal with history on nodes.

:created: 11/12/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from maya import cmds, mel


def delete_history(nodes=None, mode=None):
    """Delete history on selection.

    Args:
        nodes (list): List of nodes. If none given, use selection.
        mode (str): Can be "pre-deform" or "non-deform".
            If None, simply delete all history on selection.
    """
    nodes = nodes or cmds.ls(selection=True)

    if mode == "pre-deform":
        cmds.bakePartialHistory(nodes, preDeformers=True)
    elif mode == "non-deform":
        cmds.bakePartialHistory(nodes, prePostDeformers=True)
    else:
        cmds.delete(nodes, constructionHistory=True)


def freeze_transforms(nodes=None, transforms="trsp", history=False):
    """Freeze transforms on given nodes.

    Args:
        nodes (list): List of nodes. If none given, use selection.
        transforms (str): Transforms to freeze. e.g. "trs".
        history (bool): Also delete history if True. Default is False.

    """
    selection = cmds.ls(selection=True) or []
    nodes = nodes or selection

    cmds.select(nodes)
    cmds.makeIdentity(
        apply=True,
        translate="t" in transforms,
        rotate="r" in transforms,
        scale="s" in transforms,
    )
    cmds.select(selection)

    if "p" in transforms:
        for each in nodes:
            cmds.setAttr(each + ".rotatePivot", 0, 0, 0)
            cmds.setAttr(each + ".scalePivot", 0, 0, 0)

    if history:
        cmds.delete(nodes, constructionHistory=True)


def delete_unused():
    """Delete unused nodes in the scene."""
    mel.eval("MLdeleteUnused;")
