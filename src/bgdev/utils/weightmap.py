"""Utility method to deal with weightmaps.

:created: 13/12/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import json
import logging
import os

from maya import cmds

import bgdev.utils.decorator
import bgdev.utils.skincluster

LOG = logging.getLogger(__name__)
DEFAULT_PATH = os.path.join(os.environ.get("MAYA_APP_DIR", ""), "weights")


def check_libraries():
    """Check if ngSkinTools package is available.

    Returns:
        dict: A mapping dict with the required ngSkinTool modules.

    Raises:
        ImportError: If the package can't be imported.
        RuntimeError: If the package can't be imported.

    """
    try:

        if not cmds.pluginInfo("ngSkinTools", query=True, loaded=True):
            cmds.loadPlugin("ngSkinTools", quiet=True)

        import ngSkinTools.importExport
        import ngSkinTools.mllInterface
        import ngSkinTools.ui.initTransferWindow

        modules = {
            "importExport": ngSkinTools.importExport,
            "mllInterface": ngSkinTools.mllInterface,
            "initTransferWindow": ngSkinTools.ui.initTransferWindow,
        }
        return modules

    except (RuntimeError, ImportError):
        msg = (
            "ngSkinTools libraries not found. "
            "Can't use the skinweights import/export methods. "
            "Contact the pipeline team to get it installed!"
        )
        LOG.error(msg)
        raise


def export_multiple_skinweights(nodes, path=DEFAULT_PATH):
    """Export multiple skinweights into a single file.

    Args:
        nodes (str): List of nodes to export their skinweights.
        path (str): File path to export weights.

    """
    data = {}
    for each in sorted(nodes):
        weights = export_skinweights(each)
        if weights:
            data[each] = weights

    # create parent folder if doesn't exists
    parent = os.path.dirname(path)
    if not os.path.exists(parent):
        os.makedirs(parent)

    # export combined weights data
    with open(path, "w") as stream:
        json.dump(data, stream, indent=4)
    LOG.info("Weights successfully exported!")


@bgdev.utils.decorator.REPEAT
def export_skinweights_callback():
    """Call back :func:`export_skinweights`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")
        return

    selection = cmds.ls(selection=True)
    for each in sorted(selection):
        export_skinweights(each)
    LOG.info("Weights successfully exported!")


def export_skinweights(node, path=DEFAULT_PATH, export=True):
    """Export the weights of the given skincluster node.

    Args:
        node (str): Name of the skinned node to export its weights.
        path (str): File path to export the weights.
        export (bool): Export weights into a file.
            Defaults to True. Use False when you only want the weights data.

    Returns:
        dict: The weights data.

    """
    json_data = {}

    # return here if node doesn't have a skincluster
    if not bgdev.utils.skincluster.get_skincluster(node):
        return json_data

    modules = check_libraries()

    # create the folder if doesn't exist
    if not os.path.exists(path):
        os.makedirs(path)

    # export skinweights
    init_layers = initialize_layers(node)
    ng_data = modules["importExport"].LayerData()
    ng_data.loadFrom(node)

    # convert longName to short (for hierarchy changes)
    for each in ng_data.influences:
        each.path = each.path.rpartition("|")[-1]

    for layer in ng_data.layers:
        for each in layer.influences:
            each.influenceName = each.influenceName.rpartition("|")[-1]

    exporter = modules["importExport"].JsonExporter()
    json_data = exporter.process(ng_data)
    if export:
        export_layer_data(node, json_data, path)
        LOG.info("Saving %r weights...", str(node))

    if init_layers:
        remove_layers(node)

    return json_data


def export_layer_data(node, data, path):
    """Export ngLayerData into JSON file.

    Args:
        node (str): Name of the mesh. Used as filename.
        data (dict): The ngLayer dictionary to export.
        path (str): The parent folder where the file will be saved into.
    """
    nice_name = node.rsplit("|")[-1].rsplit(":")[-1]
    weight_file = os.path.join(path, "{0}.json".format(nice_name))
    with open(weight_file, "w") as stream:
        stream.write(data)


def import_multiple_skinweights(path, layers=True):
    """Import multiple skinweights into a single file.

    Args:
        path (str): File path to export weights.
        layers (bool): Keep ngSkinTools layers or not.

    """
    if not os.path.exists(path):
        LOG.info("%r not found.", path)
        return

    with open(path, "r") as stream:
        data = json.load(stream)

    # check if given path' data is multi or ng_data
    if "layers" in data and "influences" in data:
        msg = (
            "Can't parse data properly. "
            "It was probably exported from ngSkinTools directly. Please, "
            "use its API to import your weights back."
        )
        LOG.warning(msg)
        return

    for node, ng_data in sorted(data.items()):
        if cmds.objExists(node):
            import_skinweights(node, data=ng_data, layers=layers)

    LOG.info("Weights successfully imported!")


@bgdev.utils.decorator.REPEAT
def import_skinweights_callback():
    """Call back :func:`import_skinweights`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")
        return

    selection = cmds.ls(selection=True)
    for each in sorted(selection):
        import_skinweights(each)
    LOG.info("Weights successfully imported!")

    cmds.select(selection)


def import_skinweights(  # pylint: disable=too-many-locals
    node, path=DEFAULT_PATH, data=None, layers=True, mode="vertexID"
):
    """Export the weights of the given skincluster node.

    Args:
        node (str): Name of the skinned node to export its weights.
        path (str): File path to export the weights.
        data (dict): Use this data directly instead of reading if from file.
        layers (bool) : Keep ngSkinTools layers or not.
        mode (str) : Can be "vertexID", "UV" or "closestPoint".
            Defaults to "vertexID".

    """
    modules = check_libraries()
    mode_remap = {"closestPoint": 0, "UV": 1, "vertexID": 2}

    # get weights data from json file
    ng_data = data or import_layer_data(node, path)
    data = json.loads(ng_data)
    if not data:
        return

    # get influence in weight file
    influences = []
    for each in data.get("influences", {}).values():
        short = each.get("path", "").rsplit("|")[-1]
        if cmds.objExists(short):
            influences.append(short)

    if not influences:
        return

    # check if skincluster already exists
    skc = bgdev.utils.skincluster.get_skincluster(node)
    if skc:
        bgdev.utils.skincluster.add_influences(skc, influences)
    else:
        skc = bgdev.utils.skincluster.bind_skincluster(node, influences)

    # import weights
    remove_layers(node)
    LOG.info("Importing %r weights...", str(node))
    io_format = modules["importExport"].Formats.getJsonFormat()
    importer = io_format.importerClass()
    processed_data = importer.process(ng_data)
    window = modules["initTransferWindow"].TransferWeightsWindow.getInstance()
    window.content.dataModel.setSourceData(processed_data)
    window.content.dataModel.setDestinationMesh(node)
    window.content.controls.transferMode.setValue(mode_remap.get(mode, 2))
    window.content.dataModel.execute()

    # if node didn't have layers before import, remove them
    if layers and len(processed_data.layers) > 1:
        LOG.debug("Found layers on %r, keeping them...", str(node))
    else:
        remove_layers(node)


def import_layer_data(node, path):
    """Import ngLayerData from JSON file.

    Args:
        node (str): Name of the mesh. Used to find the JSON file.
        path (str): The parent folder where the file is saved.

    Returns:
        str: The raw ngLayer data (somehow, this is a string!)
    """
    nice_name = node.rsplit("|")[-1].rsplit(":")[-1]
    weight_file = os.path.join(path, "{0}.json".format(nice_name))

    if not os.path.exists(weight_file):
        LOG.info("%r not found.", weight_file)
        return None

    with open(weight_file, "r") as stream:
        ng_data = stream.read()

    return ng_data


def initialize_layers(node):
    """Remove ngSkinTools layers.

    Args:
        node (str): Name of the mesh with a skinCluster attached.

    Returns:
        bool: True if layers were created, false otherwise.

    """
    modules = check_libraries()

    mll = modules["mllInterface"].MllInterface()
    mll.setCurrentMesh(node)
    if not mll.getLayersAvailable():
        mll.initLayers()
        mll.createLayer("Base Weights")
        return True

    return False


def remove_layers(node):
    """Remove ngSkinTools layers.

    Args:
        node (str): Name of the mesh with a skinCluster attached.

    """
    skincluster = bgdev.utils.skincluster.get_skincluster(node)
    history = cmds.listHistory(node)
    history.extend(cmds.listHistory(skincluster, future=True, levels=1))
    types = ("ngSkinLayerDisplay", "ngSkinLayerData")
    delete_nodes = [x for x in history if cmds.nodeType(x) in types]
    if delete_nodes:
        cmds.delete(delete_nodes)
