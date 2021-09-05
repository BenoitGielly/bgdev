"""Utility methods to help dealing with vectors.

:created: 10/10/2016
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import math
from math import sin, sqrt

from maya import cmds, mel
from maya.api.OpenMaya import MMatrix, MVector
import pymel.core as pm


def get_matrix_from_transforms(position, normal, tangent):
    """Construct an MMatrix from position, normal and tangent.

    Args:
        position (list): XYZ position.
        normal (list): The normal vector used to compute rotation.
        tangent (list): The tangent vector used to compute rotation.

    Returns:
        MMatrix: The MMatrix array.

    """
    nor = MVector(normal).normal()
    tan = MVector(tangent).normal()
    ort = nor ^ tan
    pos = MVector(position)

    matrix = MMatrix()
    for row, vector in enumerate([nor, tan, ort, pos]):
        for column, value in enumerate(vector):
            matrix.setElement(row, column, value)

    return matrix


def get_matrix_from_nodes(
    nodes, middle=True, aim_vector=(1, 0, 0), up_vector=(0, 1, 0)
):
    # pylint: disable=too-many-locals
    """Return a matrix based on given nodes.

    If passed nodes are 1 or more than 3, it simply return the manipulator
    position as a matrix. Otherwise, it'll use the second node as the aim axis
    and the third as up.

    Args:
        nodes (list): list of nodes to get matrix
        middle (bool): snap in between nodes 1 and 2 if True, else on first.
        aim_vector (tuple): default aim vector for the aimConstraint.
        up_vector (tuple): default up vector for the aimConstraint.

    Returns:
        list: matrix array.

    """
    # query manipMove position if 1 or more than 3 selected
    if len(nodes) == 1 or len(nodes) > 3:
        return get_manipulator_xforms(as_matrix=True)

    # else, use vectors and matrix to determine position and aim_vector
    if len(nodes) == 2:
        pt_a, pt_b = get_vectors(nodes)
    else:
        pt_a, pt_b, pt_c = get_vectors(nodes)

    # get vectors from each points
    pos = (pt_a + pt_b) / 2 if middle else pt_a
    x_vec = (pt_b - pos).normal()
    y_vec = MVector(up_vector) if len(nodes) == 2 else (pt_c - pos).normal()
    z_vec = x_vec ^ y_vec.normal()
    y_vec = z_vec ^ x_vec.normal()

    # build vectors and vector_array
    vector1, vector2 = MVector(aim_vector), MVector(up_vector)
    vector3 = vector1 ^ vector2

    vector_array = [[], [], []]
    for each, vect in zip([vector1, vector2, vector3], [x_vec, y_vec, z_vec]):
        j = [list(each).index(i) for i in each if i != 0][0]
        vector_array[j] = list(each[j] * vect) + [0]

    # flattens vector_array into one simple list and add position to it
    return [y for _ in vector_array for y in _] + list(pos) + [1]


def get_manipulator_xforms(as_matrix=False):
    """Query the manipulator position and orientation.

    Args:
        as_matrix (bool): if True, returns a as_matrix built from manip xforms.

    Returns:
        list: list of "XYZ" position and rotation values
            or matrix array if `as_matrix` is True.

    """
    # forces the move manipulator
    mel.eval("setToolTo $gMove;")
    position = cmds.manipMoveContext("Move", query=True, position=True)
    rotation = cmds.manipPivot(query=True, orientation=True)[0]

    if as_matrix:
        return from_euler(rotation, translate=position)
    return [position, rotation]


def get_vectors(nodes, mode="xform"):
    """Generate world position vectors of each given nodes.

    Args:
        nodes (list): list of nodes to return position as vector.
        mode (str): choose between default "xform" or "pivot" to get world position.

    Yields:
        maya.api.OpenMaya.MVector: MVector of the node's world position

    """
    for each in nodes:
        position = (0, 0, 0)

        if mode == "xform":
            position = cmds.xform(
                each,
                query=True,
                translation=True,
                worldSpace=True,
            )

        elif mode == "pivot":
            position = cmds.xform(
                each,
                query=True,
                translation=True,
                rotatePivot=True,
                worldSpace=True,
            )

        # when using xform on component like faces or edge, the returned value
        # will be a list of each vertices position, so we need to average that
        if len(position) > 3:
            vectors = [
                MVector(position[i : i + 3])
                for i in range(0, len(position), 3)
            ]
            result = MVector()
            for vector in vectors:
                result += vector
            position = result / len(vectors)

        yield MVector(position)


def from_euler(rotation, translate=(0, 0, 0), radians=False):
    # pylint: disable=too-many-locals
    """Convert euler rotation into 3-axis matrix.

    Args:
        rotation (tuple): Rotation values to add to the matrix table.
        translate (tuple): Translation values to add to the matrix table.
        radians (bool): If True, converts degrees to radians.

    Returns:
        list: Matrix of given euler rotates, with translate if given.

    """
    x_value, y_value, z_value = rotation

    # convert to radians if degrees are passed
    if radians is False:
        x_value, y_value, z_value = map(
            math.radians,
            (x_value, y_value, z_value),
        )

    cos_x, sin_x = math.cos(x_value), math.sin(x_value)
    cos_y, sin_y = math.cos(y_value), math.sin(y_value)
    cos_z, sin_z = math.cos(z_value), math.sin(z_value)

    x_vector = (
        cos_y * cos_z,
        cos_y * sin_z,
        -sin_y,
        0.0,
    )

    y_vector = (
        sin_x * sin_y * cos_z - cos_x * sin_z,
        sin_x * sin_y * sin_z + cos_x * cos_z,
        sin_x * cos_y,
        0.0,
    )

    z_vector = (
        cos_x * sin_y * cos_z + sin_x * sin_z,
        cos_x * sin_y * sin_z - sin_x * cos_z,
        cos_x * cos_y,
        0.0,
    )

    t_vector = (translate[0], translate[1], translate[2], 1.0)

    return x_vector + y_vector + z_vector + t_vector


def get_closest_point(source, targets, furthest=False):
    """Find the closest node to the source of each targets.

    Args:
        source (str): source node to use as starting point for distance calculation.
        targets (list): each nodes to process.
        furthest (bool): If True, gets the furthest node instead.

    Returns:
        str: the target node that's the closest to the source.

    """
    distance = float("inf") if not furthest else 0
    position = cmds.xform(
        source, query=True, translation=True, worldSpace=True
    )
    closest_node = None
    for node in targets:
        node_pos = cmds.xform(
            node, query=True, translation=True, worldSpace=True
        )
        node_distance = (MVector(node_pos) - MVector(position)).length()
        is_different = (
            node_distance < distance
            if not furthest
            else node_distance > distance
        )
        if is_different:
            closest_node = node
            distance = node_distance

    return closest_node


def get_distance_between(
    node1,
    node2,
    distance_between=False,
    bounding_box=False,
    rotate_pivot=False,
):
    """Get the distance between two objects.

    Args:
        node1 (str): Node that determines start position
        node2 (str): Node that determines end position
        distance_between (bool): If True, creates a distance_between node,
            query its value and delete it.
        bounding_box (bool): If True, creates a distance_between node,
        rotate_pivot (bool): If True, creates a distance_between node,

    Returns:
        float: distance between two given nodes.

    """
    if distance_between:
        dist = cmds.createNode("distanceBetween")
        cmds.connectAttr(node1 + ".worldMatrix[0]", dist + ".inMatrix1")
        cmds.connectAttr(node2 + ".worldMatrix[0]", dist + ".inMatrix2")
        value = cmds.getAttr(dist + ".distance")
        cmds.delete(dist)
        return value

    if bounding_box:
        node1 = cmds.xform(
            node1, query=True, bounding_box=True, worldSpace=True
        )
        node2 = cmds.xform(
            node2, query=True, bounding_box=True, worldSpace=True
        )

    elif rotate_pivot:
        node1 = cmds.xform(
            node1, query=True, worldSpace=True, rotate_pivot=True
        )
        node2 = cmds.xform(
            node2, query=True, worldSpace=True, rotate_pivot=True
        )

    else:
        node1 = cmds.xform(
            node1, query=True, translation=True, worldSpace=True
        )
        node2 = cmds.xform(
            node2, query=True, translation=True, worldSpace=True
        )

    value = (
        (node1[0] - node2[0]) ** 2
        + (node1[1] - node2[1]) ** 2
        + (node1[2] - node2[2]) ** 2
    ) ** 0.5

    return value


def aim_in_plane(positions, aim_vector=(1, 0, 0), up_vector=(0, 1, 0)):
    """Align selected locators based on plane made of the first and last."""
    # pylint: disable=too-many-locals

    # create nulls and snap them to given positions
    nulls = []
    for pos in positions:
        null = pm.createNode("transform")
        pm.xform(null, translation=pos, worldSpace=True)
        nulls.append(null)

    locator = pm.spaceLocator()
    locator.setMatrix(nulls[0].getMatrix(worldSpace=True))

    # reverse vectors if we're on the right side (YZ plane)
    x_axis = locator.getTranslation(space="world")[0]
    if x_axis < 0:
        aim_vector = [-1 * x for x in aim_vector]
        up_vector = [-1 * x for x in up_vector]

    # aim to nulls[2]
    pm.delete(
        pm.aimConstraint(
            nulls[-1],
            locator,
            maintainOffset=False,
            aimVector=aim_vector,
            upVector=up_vector,
            worldUpObject=nulls[1],
            worldUpType="object",
        ),
    )

    # find AH distance
    index = len(nulls) // 2
    pt_a = pm.datatypes.Point(nulls[0].getTranslation(space="world"))
    pt_b = pm.datatypes.Point(nulls[index].getTranslation(space="world"))
    pt_c = pm.datatypes.Point(nulls[-1].getTranslation(space="world"))

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
            nulls[index],
            locator,
            maintainOffset=False,
            aimVector=aim_vector,
            upVector=up_vector,
            worldUpObject=nulls[0],
            worldUpType="object",
        ),
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
    for i, each in enumerate(nulls, 1):
        if i < len(nulls):
            tmp = pm.spaceLocator()
            tmp.setMatrix(each.getMatrix(worldSpace=True))
            aim = pm.aimConstraint(
                nulls[i],
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
            pm.parent(tmp, nulls[-2])
            tmp.resetFromRestPosition()
            orientation = pm.xform(
                tmp, query=True, worldSpace=True, rotation=True
            )
            pm.xform(each, rotation=orientation, worldSpace=True)
            pm.delete(tmp)

    # cleanup and return
    matrices = [
        cmds.xform(x.name(), query=True, matrix=True, worldSpace=True)
        for x in nulls
    ]
    pm.delete(locator, nulls)

    return matrices
