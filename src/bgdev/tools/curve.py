"""Custom tools with curves.

:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""


def curve_from_nodes(degree=2):
    """Create a curve and snap each CVs on each selected nodes.

    Args:
        degree (int): The curve degree.

    Returns:
        str: The created curve node.
    """
    import pymel.core as pm

    selection = pm.selected()

    points = []
    for each in selection:
        points.append(
            pm.xform(each, query=True, translation=True, worldSpace=True)
        )
    curve = pm.curve(point=points, degree=degree)
    pm.select(selection, curve)

    return curve


def get_closest_point(point, node_list):
    """Get the closest point to each nodes in the list.

    Args:
        point (str): Node to evaluate the distance to.
        node_list (list): List of nodes to search for the closest to the point.

    Returns:
        str: The closest node.
    """
    import pymel.core as pm

    compare = float("inf")
    flags = {}
    flags.update(query=True, translation=True, worldSpace=True)
    pos = pm.xform(point, **flags)
    closest = None
    for node in node_list:
        node_pos = pm.xform(node, **flags)
        vector1 = pm.datatypes.Vector(pos)
        vector2 = pm.datatypes.Vector(node_pos)
        distance = vector1.distanceTo(vector2)
        if distance < compare:
            closest = node
            compare = distance
    return closest


def attach_nodes_to_curve():
    """Attach selected nodes to selected curve."""
    import pymel.core as pm

    selection = pm.selected()
    curve = None
    nodes = []

    # find nodes and curve
    for each in selection:
        shape = each.getShape()
        if shape and shape.type() == "nurbsCurve":
            curve = each
            continue
        nodes.append(each)

    # create locators if no nodes were found
    if not nodes:
        for i, point in enumerate(curve.getShape().getCVs()):
            name = "{}_{:02d}_locator".format(curve, i + 1)
            locator = pm.spaceLocator(name)
            pm.xform(locator, translation=point, worldSpace=True)
            nodes.append(locator)

    # connect nodes to curve's CVs
    for i, each in enumerate(curve.comp("cv")):
        node = get_closest_point(each, nodes)
        if hasattr(node, "worldPosition[0]"):
            node.worldPosition[0].connect(curve.controlPoints[i])
        else:
            name = node + "_decomposeMatrix"
            mdcp = pm.createNode("decomposeMatrix", name=name)
            node.worldMatrix[0].connect(mdcp.inputMatrix)
            mdcp.outputTranslate.connect(curve.controlPoints[i])
