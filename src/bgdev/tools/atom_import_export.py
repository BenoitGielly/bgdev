"""Use ATOM to import or export animation.

:created: 31/01/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from maya import cmds
from qtpy import QtWidgets

import bgdev.utils.controler

LOG = logging.getLogger(__name__)

cmds.loadPlugin("atomImportExport", quiet=True)


def export_dialog():
    """Open up a file dialog to get the atom file to export."""
    selection = cmds.ls(selection=True)
    nodes = bgdev.utils.controler.get_rig_controls()
    path, _ = QtWidgets.QFileDialog().getSaveFileName(filter="*.atom")
    if not path:
        return

    if not path.endswith(".atom"):
        path += ".atom"

    cmds.select(nodes)
    atom_export(path, nodes)
    cmds.select(selection)


def import_dialog():
    """Open up a file dialog to get the atom file to import."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please, select any node from a rig!")
        return
    path, _ = QtWidgets.QFileDialog().getOpenFileName(filter="*.atom")

    nodes = bgdev.utils.controler.get_rig_controls()
    atom_import(path, nodes)
    cmds.select(selection)


def atom_export(path, nodes):
    """Export selected controlers into atom file.

    Args:
        path (str): The atom file path.
        nodes (list): List of controlers to export animation from.

    """
    # check namespaces
    namespaces = list({x.rpartition(":")[0] for x in nodes})
    if len(namespaces) > 1:
        LOG.warning(
            "Multiple namespaces detected, please provide"
            " a list of nodes sharing the same one!"
        )
        return

    export_options = (
        "precision=8;"
        "statics=1;"
        "baked=1;"
        "sdk=0;"
        "constraint=0;"
        "animLayers=0;"
        "selected=selectedOnly;"
        "whichRange=1;"
        "range=1:10;"
        "hierarchy=none;"
        "controlPoints=0;"
        "useChannelBox=1;"
        "options=keys;"
        "copyKeyCmd=-animation objects "
        "-option keys "
        "-hierarchy none "
        "-controlPoints 0 "
    )

    cmds.select(nodes)
    cmds.file(
        path,
        force=True,
        options=export_options,
        type="atomExport",
        exportSelected=True,
    )
    LOG.info("ATOM animation exported to %r", path)

    # if a namespace is found, remove it from the exported atom file
    if not namespaces[0]:
        return

    with open(path, "r") as stream:
        content = stream.read()

    for each in nodes:
        clean = each.replace(namespaces[0] + ":", "")
        content = content.replace(each, clean)

    with open(path, "w") as stream:
        stream.write(content)


def atom_import(path, nodes):
    """Import animation curves from atom file.

    Args:
        path (str): The atom file path.
        nodes (list): List of controlers to import animation onto.

    """
    namespaces = list({x.rpartition(":")[0] for x in nodes})
    for each in namespaces:
        namespace = each + ":" if each else ""
        import_options = (
            ";;targetTime=3;"
            "option=scaleReplace;"
            "match=string;;"
            "selected=selectedOnly;"
            "search=;"
            "replace=;"
            "prefix={0};"
            "suffix=;"
            "mapFile=;"
        ).format(namespace)
        cmds.select(nodes)
        cmds.file(path, i=True, options=import_options, type="atomImport")
