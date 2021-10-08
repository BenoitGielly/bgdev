"""Convert a blendshape target into a cluster.

:author: Benoit Gielly <benoit.gielly@gmail.com>
:created: 19/09/2021
"""
from collections import OrderedDict
import logging

from maya import cmds
from maya.api import OpenMaya, OpenMayaAnim

LOG = logging.getLogger(__name__)


def convert_target_to_cluster(blendshape, shape, deform, mode=None):
    """Convert blendshape target to cluster.

    Args:
        blendshape (str): Name of the blendshape node.
        shape (str): Name of the target.
        deform (str): Name of the mesh to receive the cluster.
        mode (str): Position option for the cluster handle.
            None would just snap the locator to the original vertex location.
            "aim" will snap at orig and aim along the delta vector.
            "snap" will orient and move at the end of the delta vector.

    Example: ::

        convert_target_to_cluster("blendShape", "target", "mesh")
        convert_target_to_cluster("blendShape", "target", "mesh", mode="aim")
        convert_target_to_cluster("blendShape", "target", "mesh", mode="snap")


    """
    geometry = (get_input_geometry(blendshape) or [None])[0]
    orig_points = get_point_array(geometry)
    targets = get_node_aliases(blendshape, indices=True)
    index = targets.get(shape)
    plugname = (
        blendshape
        + ".inputTarget[0].inputTargetGroup[{}].inputTargetItem[6000]"
    )

    # get deltas values
    plug = plugname.format(index) + ".inputPointsTarget"
    deltas = cmds.getAttr(plug) or []

    # find vertices with deltas
    components = []
    plug = plugname.format(index) + ".inputComponentsTarget"
    for each in cmds.getAttr(plug) or []:
        parsed = each.rsplit("[")[-1].rsplit("]")[0]
        if ":" not in parsed:
            components.append(int(parsed))
            continue
        result = [int(x) for x in parsed.split(":")]
        components.extend(range(result[0], result[-1] + 1))

    # build deltas info list
    delta_info = {}
    weightmap = [0.0] * len(orig_points)
    for i, value in zip(components, deltas):
        orig_pos = OpenMaya.MVector(orig_points[i])
        delta_vec = OpenMaya.MVector(value[:-1])
        delta_pos = orig_pos + delta_vec
        delta_pnt = OpenMaya.MPoint(delta_pos)
        weight = orig_points[i].distanceTo(delta_pnt)
        delta_info[i] = [i, delta_pos, delta_vec, weight]
        weightmap[i] = weight

    # normalize weights
    max_weight = float(max(weightmap))
    normal_weightmap = [float(i) / max_weight for i in weightmap]

    # create cluster and deform mesh if non exist
    if not obj_exists(deform):
        deform = duplicate_mesh(geometry, name=deform, material=True)
    name = "{}{}_cluster".format(shape, "_" + mode if mode else "")
    cluster, cls_handle = cmds.cluster(deform, name=name)

    # set the weightmap on cluster
    weightplug = as_plug(cluster + ".weightList[0].weights")
    for i, value in enumerate(normal_weightmap):
        weightplug.selectAncestorLogicalIndex(i)
        weightplug.setFloat(value)

    # create locator and aim toward delta direction
    idx, pos, vec, _ = max(delta_info.values(), key=lambda x: x[-1])
    mover = cmds.spaceLocator(name=cluster + "_handle")[0]
    orig_pos = list(orig_points[idx])[:-1]
    flags = {"translation": orig_pos}
    if mode == "aim":
        flags = {"matrix": matrix_from_vector_and_position(vec, orig_pos)}
    elif mode == "snap":
        flags = {"matrix": matrix_from_vector_and_position(vec, pos)}
    cmds.xform(mover, worldSpace=True, **flags)
    cmds.cluster(
        cls_handle, edit=True, bindState=True, weightedNode=[mover, mover]
    )
    cmds.delete(cls_handle)


# UTILS
def as_selection(name):
    """Get name as MSelectionList."""
    selection = OpenMaya.MSelectionList()
    selection.add(name)
    return selection


def as_obj(name):
    """Get name as MObject."""
    if hasattr(name, "node"):
        return getattr(name, "node")()
    return OpenMaya.MObject(as_selection(name).getDependNode(0))


def as_dag(dag, to_shape=False):
    """Get name as MDagPath."""
    if not isinstance(dag, OpenMaya.MDagPath):
        dag = OpenMaya.MDagPath(as_selection(dag).getDagPath(0))
    if to_shape:
        dag.extendToShape()
    return dag


def as_plug(plug):
    """Get name as MPlug."""
    if isinstance(plug, OpenMaya.MPlug):
        return plug
    return OpenMaya.MPlug(as_selection(plug).getPlug(0))


def as_node(name):
    """Get name as MFnDependencyNode."""
    return OpenMaya.MFnDependencyNode(as_obj(name))


def as_mesh(name):
    """Get name as MFnMesh."""
    return OpenMaya.MFnMesh(as_dag(name))


def as_filter(deformer):
    """Get deformer as GeometryFilter."""
    return OpenMayaAnim.MFnGeometryFilter(as_obj(deformer))


def obj_exists(obj):
    """Check if objExists using OpenMaya."""
    try:
        return as_selection(obj)
    except RuntimeError:
        return False


def get_alias_list(node):
    """Get all alias attribute in pair from given node."""
    return as_node(node).getAliasList()


def get_node_aliases(node, attr="weight", indices=False):
    """List all alises on given node and attribute.

    Args:
        node (str): Name of the node (usually blendshape).
        attr (str): Name of the attribute to query aliases.
        indices (bool): Returns an OrderedDict whose values are the indices.

    Returns:
        list or OrderedDict: List of aliases.
    """

    def get_index(name):
        """Extract index from name."""
        return int(name.rsplit("[")[-1].split("]")[0])

    pair_data = {y: get_index(x) for y, x in get_alias_list(node) if attr in x}
    targets = sorted(pair_data, key=pair_data.get)
    if indices:
        return OrderedDict((x, pair_data.get(x)) for x in targets)
    return targets


def duplicate_mesh(geometry, name="temp", parent=None, material=False):
    """Duplicate given geometry using Maya API."""
    flags = {"parent": parent} if parent else {}
    root = cmds.createNode("transform", name=name, **flags)
    mesh = as_mesh(geometry)
    mesh.copy(mesh.object(), as_obj(root))
    mesh.setName(name + "Shape")
    if material:
        cmds.sets(name, edit=True, forceElement="initialShadingGroup")
    return root


def get_point_array(mesh):
    """Get all vertices position of given mesh."""
    return as_mesh(mesh).getPoints()


def get_input_geometry(deformer):
    """Get input geometries affected by given deformer."""
    return [
        OpenMaya.MDagPath.getAPathTo(each).partialPathName()
        for each in as_filter(deformer).getInputGeometry() or []
    ]


def matrix_from_vector_and_position(vector, position):
    """Create an MMatrix from given vector and postion.

    Args:
        vector (list or MVector): Vector which gives the aim direction.
        position (list): Point to use as the default coordinate.

    Returns:
        MMatrix: The matrix reprensenting the transforms.
    """
    vector_x = OpenMaya.MVector(vector).normal()
    vector_y = OpenMaya.MVector(0, 1, 0)
    vector_z = OpenMaya.MVector(vector_x ^ vector_y).normal()
    vector_y = OpenMaya.MVector(vector_z ^ vector_x).normal()
    matrix = OpenMaya.MMatrix()
    for row, each in enumerate([vector_x, vector_y, vector_z, position]):
        for column, value in enumerate(each):
            matrix.setElement(row, column, value)
    return matrix
