"""Random scripts and tools (needs to be sorted...).

:author: Benoit GIELLY <benoit.gielly@gmail.com>

"""
from functools import partial
import logging
from math import sin, sqrt

from PySide2 import QtWidgets
from maya import cmds
from maya.api import OpenMaya

LOG = logging.getLogger(__name__)


def snap(**kwargs):
    """Snap an obj on a target."""
    srt = kwargs.get("snap", kwargs.get("sn", "rt")).lower()
    obj = kwargs.get("object", kwargs.get("obj", None))
    tgt = kwargs.get("target", kwargs.get("tgt", None))
    pivot = kwargs.get("pivot", kwargs.get("pv", None))

    try:
        if not obj:
            obj = cmds.ls(selection=True)[0]
        if not tgt:
            tgt = cmds.ls(selection=True)[1]
    except IndexError:
        cmds.warning(
            "Select 'source' then 'target' or use the command's flags"
        )

    if "t" in srt:
        if pivot:
            pos = cmds.xform(
                tgt + ".rp", query=True, translation=True, worldSpace=True
            )
            cmds.move(pos[0], pos[1], pos[2], rotatePivotRelative=True)
        else:
            pos = cmds.xform(
                tgt, query=True, translation=True, worldSpace=True
            )
            cmds.xform(obj, translation=pos, worldSpace=True)

    if "r" in srt:
        rot = cmds.xform(tgt, query=True, rotation=True, worldSpace=True)
        cmds.xform(obj, rotation=rot, worldSpace=True)

    if "s" in srt:
        scl = cmds.getAttr(tgt + ".scale")[0]
        cmds.setAttr(obj + ".scale", scl[0], scl[1], scl[2], type="double3")


def toggle_side_select(toggle=True):  # pylint: disable=too-many-statements
    """Toggle selection."""
    node_list = cmds.ls(selection=True, flatten=True)
    new_list = []

    # if vertex, use symmetry table to find the opposite
    if ".vtx" in node_list[0]:
        for each in node_list:
            index = int(each.rpartition("[")[-1].rpartition("]")[0])
            if cmds.objExists(each + ".sym"):
                mirror_index = cmds.getAttr(
                    each.rpartition(".vtx")[0] + ".sym"
                )[index][1:]
                mirror = each.replace("[%s]" % index, "[%s]" % mirror_index)
                new_list.append(mirror)

    # else, toggle the prefixes
    else:
        for each in node_list:
            namespace = each.rpartition(":")[0]
            namespace = "%s:" % namespace if namespace else namespace
            clean_name = each.replace(namespace, "")

            # split to find the short name
            short_name = clean_name.rpartition("|")[-1]
            if short_name.lower().startswith("c"):
                new_list.append(each)
                continue

            if short_name.startswith("l_"):
                pfx = ["l_", "r_"]
            elif short_name.startswith("r_"):
                pfx = ["r_", "l_"]
            elif short_name.startswith("l"):
                pfx = ["l", "r"]
            elif short_name.startswith("r"):
                pfx = ["r", "l"]
            elif short_name.startswith("L_"):
                pfx = ["L_", "R_"]
            elif short_name.startswith("R_"):
                pfx = ["R_", "L_"]
            elif short_name.startswith("L"):
                pfx = ["L", "R"]
            elif short_name.startswith("R"):
                pfx = ["R", "L"]
            elif short_name.startswith("LB_"):
                pfx = ["LB_", "RB_"]
            elif short_name.startswith("LF_"):
                pfx = ["LF_", "RF_"]
            elif short_name.startswith("RB_"):
                pfx = ["RB_", "LB_"]
            elif short_name.startswith("RF_"):
                pfx = ["RF_", "LF_"]
            elif "Left" in short_name:
                pfx = ["Left", "Right"]
            elif "Right" in short_name:
                pfx = ["Right", "Left"]
            elif "left" in short_name:
                pfx = ["left", "right"]
            elif "right" in short_name:
                pfx = ["right", "left"]
            else:
                new_list.append(each)
                continue

            flipped_name = []
            size = len(pfx[0])
            for short_name in clean_name.split("|"):
                if short_name.startswith(pfx[0]):
                    name = (
                        short_name[:size].replace(pfx[0], pfx[1], 1)
                        + short_name[size:]
                    )
                    flipped_name.append(name)
                else:
                    flipped_name.append(short_name)

            flipped_node = "{namespace}{name}".format(
                namespace=namespace, name="|".join(flipped_name)
            )

            if cmds.objExists(flipped_node):
                new_list.append(flipped_node)
            else:
                cmds.warning("{} doesn't exists".format(flipped_node))
                new_list.append(each)

    if toggle:
        cmds.select(new_list, replace=True)
    else:
        cmds.select(new_list, add=True)


def simple_snap(srt=None):
    """Snap quickly."""
    selection = cmds.ls(selection=True)
    pos = cmds.xform(
        selection[-1], query=True, worldSpace=True, rotatePivot=True
    )
    rot = cmds.xform(selection[-1], query=True, worldSpace=True, rotation=True)
    scl = cmds.xform(selection[-1], query=True, worldSpace=True, scale=True)
    for each in selection[:-1]:
        if "s" in srt:
            cmds.xform(each, scale=scl, worldSpace=True)
        if "r" in srt:
            cmds.xform(each, rotation=rot, worldSpace=True)
        if "t" in srt:
            cmds.xform(each, translation=pos, worldSpace=True)


def mirror_position(selected=False):
    """Mirror selected along world Z+."""
    selection = cmds.ls(selection=True)

    for each in selection:
        matrix = cmds.xform(each, query=True, matrix=True, worldSpace=True)
        inverse = OpenMaya.MMatrix(
            [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        )
        result = OpenMaya.MMatrix(matrix) * inverse
        node = each if selected else cmds.spaceLocator(name=each + "_loc")[0]
        cmds.xform(node, matrix=result, worldSpace=True)


def quick_distance():
    """Get distance between two nodes."""
    attributes = ["startPoint", "endPoint"]

    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        return cmds.warning("Select 2 nodes")

    points = {}
    for each, key in zip(selection, attributes):
        points[key] = cmds.xform(
            each, query=True, rotatePivot=True, worldSpace=True
        )
    distance = cmds.distanceDimension(**points)
    for each, attr in zip(selection, attributes):
        target = cmds.listConnections("{}.{}".format(distance, attr))[0]
        if each != target:
            cmds.parentConstraint(each, target, maintainOffset=True)


def show_joint_orient(value=True):
    """Display jointOrient attributes in channel box."""
    for each in cmds.ls(type="joint"):
        for plug in [each + ".jo" + x for x in "xyz"]:
            cmds.setAttr(plug, channelBox=value)


def find_bad_meshes():
    """Find meshes with incorrect amount of vertices."""
    bad_meshes = []
    sel_list = OpenMaya.MGlobal.getSelectionListByName("*_geo")
    sel_iter = OpenMaya.MItSelectionList(sel_list)
    while not sel_iter.isDone():
        mesh = OpenMaya.MFnMesh(sel_iter.getComponent()[0])
        num_vertices = mesh.numVertices
        num_faces = mesh.numPolygons
        if num_vertices > num_faces * 4:
            bad_meshes.append(mesh.fullPathName())
        sel_iter.next()

    if bad_meshes:
        cmds.sets(bad_meshes, name="BAD_MESHES")
        cmds.error("BAD MESHES FOUND!")
    else:
        cmds.warning("Scene seems clean, well done!")


def get_vectors_dialog():
    """Query aim and up vectors using a LayoutPromptDialog."""
    import pymel.core as pm

    # get the dialog's formLayout.
    form = pm.setParent(query=True)

    # build widgets
    aim_field = pm.intFieldGrp(
        numberOfFields=3, label="Aim Vector", value1=1, value2=0, value3=0
    )

    up_field = pm.intFieldGrp(
        numberOfFields=3, label="Up Vector", value1=0, value2=1, value3=0
    )

    def get_fields(aim_field, up_field, _):
        """Query fields values when button is clicked."""
        aim_value = [int(x) for x in aim_field.getValue()]
        up_value = [int(x) for x in up_field.getValue()]
        value = aim_value, up_value
        pm.layoutDialog(dismiss=str(value))

    with pm.horizontalLayout():
        pm.button(label="OK", command=partial(get_fields, aim_field, up_field))
        pm.button(label="Cancel", command='pm.layoutDialog(dismiss="Cancel")')

    form.redistribute()


def align_fingers(
    nodes=None, aim_vector=(1, 0, 0), up_vector=(0, 1, 0), gui=False
):
    """Align selection based on first and last plane (use for fingers)."""
    import pymel.core as pm
    import pymel.core.datatypes as dt

    # pylint: disable=too-many-locals, eval-used
    if gui is True:
        value = pm.layoutDialog(uiScript=get_vectors_dialog)
        if value == "Cancel":
            return
        aim_vector, up_vector = eval(value)

    # create locator and snap to selection[0]
    selection = nodes or pm.selected()
    selection = [pm.PyNode(x) for x in selection]
    locator = pm.spaceLocator()
    locator.setMatrix(selection[0].getMatrix(worldSpace=True))

    # reverse vectors if we're on the right side (YZ plane)
    x_axis = locator.getTranslation(space="world")[0]
    if x_axis < 0:
        aim_vector = [-1 * x for x in aim_vector]
        up_vector = [-1 * x for x in up_vector]

    # aim to selection[2]
    pm.delete(
        pm.aimConstraint(
            selection[-1],
            locator,
            maintainOffset=False,
            aimVector=aim_vector,
            upVector=up_vector,
            worldUpObject=selection[1],
            worldUpType="object",
        )
    )

    # find AH distance
    index = len(selection) // 2
    pt_a = dt.Point(selection[0].getTranslation(space="world"))
    pt_b = dt.Point(selection[index].getTranslation(space="world"))
    pt_c = dt.Point(selection[-1].getTranslation(space="world"))

    c_side = pt_b - pt_a
    b_side = pt_c - pt_a
    height = sin(c_side.angle(b_side)) * c_side.length()
    ah_dist = sqrt(pow(c_side.length(), 2) - pow(height, 2))

    # offset by ah_dist along aim axis
    ah_values = [ah_dist * x for x in aim_vector]
    pm.move(
        locator,
        *ah_values,
        relative=True,
        objectSpace=True,
        worldSpaceDistance=True
    )

    # re-orient properly
    pm.delete(
        pm.aimConstraint(
            selection[index],
            locator,
            maintainOffset=False,
            aimVector=aim_vector,
            upVector=up_vector,
            worldUpObject=selection[0],
            worldUpType="object",
        )
    )

    # move forward by half of AC
    ac_values = [b_side.length() * x for x in aim_vector]
    pm.move(
        locator,
        *ac_values,
        relative=True,
        objectSpace=True,
        worldSpaceDistance=True
    )

    # orient the base locator
    for i, each in enumerate(selection, 1):
        if i < len(selection):
            tmp = pm.spaceLocator()
            tmp.setMatrix(each.getMatrix(worldSpace=True))
            aim = pm.aimConstraint(
                selection[i],
                tmp,
                maintainOffset=False,
                aimVector=aim_vector,
                upVector=up_vector,
                worldUpObject=locator,
                worldUpType="object",
            )
            orientation = pm.xform(
                tmp, query=True, worldSpace=True, rotation=True
            )
            pm.delete(aim, tmp)
            pm.xform(each, rotation=orientation, worldSpace=True)
        else:
            tmp = pm.spaceLocator()
            pm.parent(tmp, selection[-2])
            tmp.resetFromRestPosition()
            orientation = pm.xform(
                tmp, query=True, worldSpace=True, rotation=True
            )
            pm.xform(each, rotation=orientation, worldSpace=True)
            pm.delete(tmp)

    # cleanup
    pm.delete(locator)


def show_cam_clip_planes():
    """Turn nearClip and farClip planes visible in the CB for all cameras."""
    for camera in cmds.ls(type="camera"):
        cmds.setAttr(camera + ".nearClipPlane", channelBox=True)
        cmds.setAttr(camera + ".farClipPlane", channelBox=True)

    # select the perspCamera
    if cmds.objExists("persp"):
        cmds.select("persp")


def set_default_clip_plane():
    """Set camera clipPlanes to default values."""
    values = [
        cmds.optionVar(query="defaultCameraNearClipValue"),
        cmds.optionVar(query="defaultCameraFarClipValue"),
    ]
    for camera in cmds.ls(type="camera"):
        for attr in ["nearClipPlane", "farClipPlane"]:
            plug = "{}.{}".format(camera, attr)
            value = values[0] if "near" in attr else values[-1]
            if cmds.getAttr(plug, settable=True):
                cmds.setAttr(plug, value)

    show_cam_clip_planes()


def change_default_clip_plane():
    """Create a quick GUI to change the camera clipPlane values option vars."""
    import pymel.core as pm

    # methods
    def set_values(widget, near, far):
        """Set the near and far clip values."""
        cmds.optionVar(floatValue=["defaultCameraNearClipValue", near.value()])
        cmds.optionVar(floatValue=["defaultCameraFarClipValue", far.value()])
        widget.close()

    def create_intfield(layout, name):
        """Create the near/far label and intfield combo."""
        hbox = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(name + " Clip:")
        label.setMinimumWidth(60)
        field = QtWidgets.QDoubleSpinBox()
        if name == "Near":
            field.setMinimum(0.0000000001)
            field.setDecimals(4)
        else:
            field.setMaximum(10000000000)
            field.setDecimals(0)
        field.setValue(
            cmds.optionVar(query="defaultCamera{}ClipValue".format(name))
        )
        hbox.addWidget(label)
        hbox.addWidget(field)
        hbox.setStretch(1, 1)
        layout.addLayout(hbox)
        return field

    # widgets
    maya = pm.toQtWindow("MayaWindow")
    widget = QtWidgets.QDialog(maya)
    widget.setWindowTitle("Set default camera clipPlane")
    widget.setMinimumWidth(300)

    layout = QtWidgets.QVBoxLayout(widget)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(2)

    near_field = create_intfield(layout, "Near")
    far_field = create_intfield(layout, "Far")

    btn_hbox = QtWidgets.QHBoxLayout()
    ok_btn = QtWidgets.QPushButton("OK")
    cl_btn = QtWidgets.QPushButton("Cancel")
    btn_hbox.addWidget(ok_btn)
    btn_hbox.addWidget(cl_btn)
    layout.addLayout(btn_hbox)

    # signals
    ok_btn.clicked.connect(partial(set_values, widget, near_field, far_field))
    cl_btn.clicked.connect(widget.close)
    widget.show()
