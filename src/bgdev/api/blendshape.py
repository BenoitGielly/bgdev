"""API methods for blendshapes.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from maya import cmds
from maya.api import OpenMaya

from . import attribute, core, deformer, mesh


def reconnect_blendshape(blendshape, geometry):
    """Reconnect blendshape node to given geometry.

    Args:
        blendshape (str): Name of blendshape node.
        geometry (str): Geometry to apply blendshape to (same topology).
    """
    dummy_geo = mesh.duplicate_mesh(geometry)
    dummy_bs = cmds.blendShape(dummy_geo, geometry)[0]

    # connect the groupParts to the blendshape.
    modifier = OpenMaya.MDGModifier()
    src_plug = dummy_bs + ".input[0].inputGeometry"
    src_plug = core.as_plug(src_plug).source()
    plug = core.as_plug(blendshape + ".input[0].inputGeometry")
    modifier.connect(src_plug, plug)
    modifier.renameNode(src_plug.node(), blendshape + "GroupParts")
    modifier.doIt()

    # Connect the groupId to the blendshape.
    src_plug = dummy_bs + ".input[0].groupId"
    src_plug = core.as_plug(src_plug).source()
    plug = core.as_plug(blendshape + ".input[0].groupId")
    modifier.connect(src_plug, plug)
    modifier.renameNode(src_plug.node(), blendshape + "GroupId")
    modifier.doIt()

    # Connect the message and rename the set.
    deformset = core.as_filter(dummy_bs).deformerSet
    node = core.as_node(deformset)
    plug = node.findPlug("usedBy", 0)
    plug.selectAncestorLogicalIndex(0)
    modifier.disconnect(plug.source(), plug)
    msg_plug = core.as_plug(blendshape + ".message")
    modifier.connect(msg_plug, plug)
    modifier.renameNode(plug.node(), blendshape + "Set")
    modifier.doIt()

    # Connect the blendshape output to the geometry.
    dag = core.as_dag(geometry, to_shape=True)
    node = core.as_node(dag)
    name = "create" if node.typeName == "nurbsCurve" else "inMesh"
    plug = node.findPlug(name, 0)
    modifier.disconnect(plug.source(), plug)
    outplug = core.as_plug(blendshape + ".outputGeometry[0]")
    modifier.connect(outplug, plug)
    modifier.doIt()

    # delete nodes (using modifier.deleteNode is unstable)
    cmds.delete(dummy_geo, dummy_bs)


def fix_target_names(blendshape):
    """Fix target names of given blendshapes based on the input targets."""
    src_plug = (
        "{}.inputTarget[0].inputTargetGroup[{}]"
        ".inputTargetItem[6000].inputGeomTarget"
    )
    targets = attribute.get_node_aliases(blendshape, indices=True)
    for alias, index in targets.items():
        input_ = cmds.listConnections(
            src_plug.format(blendshape, index),
            source=True,
            destination=False,
        )
        if input_ and alias != input_[0]:
            plug = "{}.weight[{}]".format(blendshape, index)
            attribute.set_alias(plug, input_[0])


def copy_target_weights(source, destination):
    """Copy a blendshape's target weights to another target.

    Args:
        source (str): Name of the blendshape's source plug
        destination (str): Name of the blendshape's destination plug
    """
    handle = core.as_plug(source).asMDataHandle()
    plug = core.as_plug(destination)
    plug.setMDataHandle(handle)
    plug.destructHandle(handle)


def reset_target_delta(blendshape, shape, targets=None):
    """Reset given shape delta in the blendshape node."""
    targets = targets or attribute.get_node_aliases(blendshape, indices=True)
    if not isinstance(targets, dict):
        targets = attribute.get_node_aliases(blendshape, indices=True)
    index = targets.get(shape)
    if index:
        cmds.blendShape(blendshape, edit=True, resetTargetDelta=[0, index])


def add_blendshape_targets(blendshape, shape, alias=None):
    """Add and update targets on the given blendShape."""
    alias = alias or shape

    # check that shape exists
    if not core.obj_exists(shape):
        raise RuntimeError("Shape to add doesn't exists: {}".format(shape))

    # get blendshape index
    targets = attribute.get_node_aliases(blendshape, indices=True) or {}
    plug = "{}.weight".format(blendshape)
    index = targets.get(shape) or attribute.get_next_index(plug)

    # add shape and update targets dict
    geometry = deformer.get_output_geometry(blendshape)[0]
    cmds.blendShape(blendshape, edit=True, target=(geometry, index, shape, 1))
    disconnect_target(blendshape, shape)

    plug = core.as_plug("{}.weight[{}]".format(blendshape, index))
    if attribute.get_alias(plug) != alias:
        attribute.set_alias(plug, alias)
    if attribute.is_free(plug):
        plug.setFloat(0.0)


def disconnect_target(blendshape, shape):
    """Disconnect given shape from blendshape node."""
    modifier = OpenMaya.MDGModifier()
    shape_dag = core.as_dag(shape, to_shape=True)
    for plug in core.as_filter(blendshape).getConnections():
        source = plug.source()
        if plug.isDestination and source.node() == shape_dag.node():
            modifier.disconnect(source, plug)
    modifier.doIt()


def delete_blendshape_target(blendshape, index):
    """Delete given target index on blendshape node."""
    node = core.as_node(blendshape)
    modifier = OpenMaya.MDGModifier()

    # clear the weight attribute
    plug = core.as_plug("{}.weight[{}]".format(blendshape, index))
    alias = plug.partialName(useLongNames=True)
    node.setAlias("", alias, plug, add=False)
    modifier.removeMultiInstance(plug, True)

    it_plug = node.findPlug("inputTarget", 0)
    for i in it_plug.getExistingArrayAttributeIndices():
        itg_plug = node.findPlug("inputTargetGroup", 0)
        itg_plug.selectAncestorLogicalIndex(i, it_plug.attribute())
        itg_plug.selectAncestorLogicalIndex(index)

        # remove inbetweens
        iti_plug = node.findPlug("inputTargetItem", 0)
        iti_plug.selectAncestorLogicalIndex(i, it_plug.attribute())
        iti_plug.selectAncestorLogicalIndex(index, itg_plug.attribute())
        for j in iti_plug.getExistingArrayAttributeIndices():
            iti_plug.selectAncestorLogicalIndex(j)
            modifier.removeMultiInstance(iti_plug, True)

        # remove target weights
        tw_plug = node.findPlug("targetWeights", 0)
        tw_plug.selectAncestorLogicalIndex(i, it_plug.attribute())
        tw_plug.selectAncestorLogicalIndex(index, itg_plug.attribute())
        modifier.removeMultiInstance(tw_plug, True)

        # remove target group
        modifier.removeMultiInstance(itg_plug, True)

    modifier.doIt()


def disable_target_weights(blendshape):
    """Disable all weights on blendshape node."""
    restore_data = {}
    modifier = OpenMaya.MDagModifier()
    for each in attribute.get_node_aliases(blendshape) or []:
        info = {}
        info["plug"] = plug = core.as_plug("{}.{}".format(blendshape, each))
        info["value"] = plug.asFloat()
        info["locked"] = plug.isLocked
        if plug.isConnected:
            info["source"] = source = plug.source()
            modifier.disconnect(source, plug)
        plug.isLocked = False
        modifier.newPlugValueFloat(plug, 0)
        restore_data[each] = info
    modifier.doIt()
    return restore_data


def restore_target_weights(restore_data):
    """Restore blendshape weights based on previous data."""
    modifier = OpenMaya.MDagModifier()
    for info in restore_data.values():
        plug = info["plug"]
        source = info.get("source")
        if source:
            modifier.connect(source, plug)
        else:
            modifier.newPlugValueFloat(plug, info["value"])
    modifier.doIt()
    for info in restore_data.values():
        info["plug"].isLocked = info["locked"]
