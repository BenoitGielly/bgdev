"""
=====================================================================

edgeFlowMirror 3.4 (c) 2007 - 2016 by Thomas Bittner

(c) 2007 - 2016 by Thomas Bittner
thomasbittner@hotmail.de

This tool mirrors mainly skinweights, geometry and component selection.
Opposite Mirror-points are found per edgeflow, and NOT via position.
This means, that only the way the edges are connected together is relevant,
and the actual positions of the vertices does not matter.
one of the inputs the tool requires, is one of the middleedges
The character can even be in a different pose and most parts of the tool will
still work.

=====================================================================

"""
import math
import sys

from maya import cmds, OpenMaya, OpenMayaAnim, OpenMayaMPx

# name our command
kPluginCmdName = "edgeFlowMirror"

kTaskFlag = "-t"
kTaskFlagLong = "-task"
kDirectionFlag = "-d"
kDirectionFlagLong = "-direction"
kMiddleEdgeFlag = "-me"
kMiddleEdgeFlagLong = "-middleEdge"
kBaseObjectFlag = "-bo"
kBaseObjectFlagLong = "-baseObject"
kBaseVertexSpaceFlag = "-bv"
kBaseVertexSpaceFlagLong = "-baseVertexSpace"
kLeftJointsPrefixFlag = "-ljp"
kLeftJointsPrefixFlagLong = "-leftJointsPrefix"
kRightJointsPrefixFlag = "-rjp"
kRightJointsPrefixFlagLong = "-rightJointsPrefix"
kOptimizeFlag = "-o"
kOptimizeFlagLong = "-optimize"

edgeFlowMirrorSavedMapArray = []
edgeFlowMirrorSavedSideArray = []
edgeFlowMirrorNewBaseObjectName = ""


class EdgeFlowMirrorCommand(OpenMayaMPx.MPxCommand):

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)
        self.old_target_points = OpenMaya.MFloatVectorArray()
        self.new_target_points = OpenMaya.MFloatVectorArray()
        self.target_obj = OpenMaya.MDagPath()

        self.weight_array = OpenMaya.MDoubleArray()
        self.old_weight_array = OpenMaya.MDoubleArray()
        self.inf_count = 0
        self.vtx_components = OpenMaya.MObject()
        self.skin_cluster = OpenMaya.MObject()

        self.task = None

    def manipulate_object(self, redo):
        if self.task.startswith("geometry"):

            target_point_array = OpenMaya.MPointArray()
            target_object_dag_path = OpenMaya.MDagPath()

            fn_target_mesh = OpenMaya.MFnMesh(self.target_obj)
            OpenMaya.MFnDagNode(self.target_obj).getPath(target_object_dag_path)
            fn_target_mesh.getPoints(target_point_array)
            point_index = 0
            if redo:
                for i in range(target_point_array.length()):
                    target_point_array.set(
                        i,
                        self.new_target_points[point_index].x,
                        self.new_target_points[point_index].y,
                        self.new_target_points[point_index].z,
                    )
                    point_index += 1

            else:
                for i in range(target_point_array.length()):
                    target_point_array.set(
                        i,
                        self.old_target_points[point_index].x,
                        self.old_target_points[point_index].y,
                        self.old_target_points[point_index].z,
                    )
                    point_index += 1

            fn_target_mesh.setPoints(target_point_array, OpenMaya.MSpace.kObject)
            fn_target_mesh.updateSurface()

        if self.task == "skinCluster":
            fn_skin_cluster = OpenMayaAnim.MFnSkinCluster(self.skin_cluster)
            skin_path = OpenMaya.MDagPath()
            fn_skin_cluster.getPathAtIndex(0, skin_path)

            influence_indices = OpenMaya.MIntArray()
            for i in range(self.inf_count):
                influence_indices.append(i)

            if redo:
                fn_skin_cluster.setWeights(
                    skin_path,
                    self.vtx_components,
                    influence_indices,
                    self.weight_array,
                    0
                )
            else:
                fn_skin_cluster.setWeights(
                    skin_path,
                    self.vtx_components,
                    influence_indices,
                    self.old_weight_array,
                    0
                )

    def doIt(self, args):
        direction = 1
        search_string = "L_ Left left"
        replace_string = "R_ Right right"
        middle_edge = ""
        self.task = ""

        # geometry
        base_object_name = ""

        syntax = OpenMaya.MSyntax()
        syntax.addFlag(
            kTaskFlag, kTaskFlagLong, OpenMaya.MSyntax.kString
        )
        syntax.addFlag(
            kDirectionFlag, kDirectionFlagLong, OpenMaya.MSyntax.kDouble
        )
        syntax.addFlag(
            kMiddleEdgeFlag, kMiddleEdgeFlagLong, OpenMaya.MSyntax.kString
        )
        syntax.addFlag(
            kBaseObjectFlag, kBaseObjectFlagLong, OpenMaya.MSyntax.kString
        )
        syntax.addFlag(
            kBaseVertexSpaceFlag, kBaseVertexSpaceFlagLong, OpenMaya.MSyntax.kBoolean
        )
        syntax.addFlag(
            kLeftJointsPrefixFlag, kLeftJointsPrefixFlagLong, OpenMaya.MSyntax.kString
        )
        syntax.addFlag(
            kRightJointsPrefixFlag, kRightJointsPrefixFlagLong, OpenMaya.MSyntax.kString
        )
        syntax.addFlag(
            kOptimizeFlag, kOptimizeFlagLong, OpenMaya.MSyntax.kBoolean
        )
        arg_data = OpenMaya.MArgDatabase(syntax, args)

        do_vertex_space = False

        if arg_data.isFlagSet(kTaskFlag):
            self.task = arg_data.flagArgumentString(kTaskFlag, 0)

        if arg_data.isFlagSet(kDirectionFlag):
            direction = arg_data.flagArgumentDouble(kDirectionFlag, 0)

        if arg_data.isFlagSet(kMiddleEdgeFlag):
            middle_edge = arg_data.flagArgumentString(kMiddleEdgeFlag, 0)

        if arg_data.isFlagSet(kBaseObjectFlag):
            base_object_name = arg_data.flagArgumentString(kBaseObjectFlag, 0)

        if arg_data.isFlagSet(kBaseVertexSpaceFlag):
            do_vertex_space = arg_data.flagArgumentBool(kBaseVertexSpaceFlag, 0)

        if arg_data.isFlagSet(kLeftJointsPrefixFlag):
            search_string = arg_data.flagArgumentString(kLeftJointsPrefixFlag, 0)

        if arg_data.isFlagSet(kRightJointsPrefixFlag):
            replace_string = arg_data.flagArgumentString(kRightJointsPrefixFlag, 0)

        if arg_data.isFlagSet(kOptimizeFlag):
            do_optimize = arg_data.flagArgumentString(kOptimizeFlag, 0)
        else:
            do_optimize = False

        selection = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList(selection)
        dag_path_sel_shape = OpenMaya.MDagPath()
        component = OpenMaya.MObject()

        iterate = OpenMaya.MItSelectionList(selection)
        if iterate.isDone():
            print("Please select some vertices.")
            return

        iterate.getDagPath(dag_path_sel_shape, component)
        selected_points = OpenMaya.MItMeshVertex(dag_path_sel_shape, component)
        point_count = OpenMaya.MFnMesh(dag_path_sel_shape).numVertices()
        object_name = OpenMaya.MFnMesh(dag_path_sel_shape).partialPathName()
        if point_count == 0:
            print("point count is 0")
            return

        if not len(middle_edge):
            print("Please specify a middle edge.")
            return

        global edgeFlowMirrorSavedMapArray
        global edgeFlowMirrorSavedSideArray
        global edgeFlowMirrorNewBaseObjectName

        if do_optimize and len(edgeFlowMirrorSavedMapArray) and self.task != "compute":
            map_array = edgeFlowMirrorSavedMapArray
            side_array = edgeFlowMirrorSavedSideArray
            new_base_object_name = edgeFlowMirrorNewBaseObjectName
        else:
            map_array, side_array, new_base_object_name = self.analyze_topology(middle_edge)
            edgeFlowMirrorSavedMapArray = map_array
            edgeFlowMirrorSavedSideArray = side_array
            edgeFlowMirrorNewBaseObjectName = new_base_object_name

        if self.task == "getMapArray":
            self.setResult(map_array)
            return

        if self.task == "getSideArray":
            self.setResult(side_array)
            return

        if self.task == "getMapSideArray":
            self.setResult(map_array + side_array)
            return

        if self.task == "compute":
            return

        if self.task == "geometrySymmetry" and len(new_base_object_name):
            base_object_name = new_base_object_name

        both_indexes = OpenMaya.MIntArray()
        all_points_array = OpenMaya.MIntArray()
        for i in range(point_count):
            all_points_array.append(-1)

        counter = 0
        selected_points.reset()

        while not selected_points.isDone():
            index = selected_points.index()
            if map_array[index] != -1:
                both_indexes.append(index)

            all_points_array[index] = counter
            counter += 1
            if side_array[index] != 0 and side_array[index] != -1:
                both_indexes.append(map_array[index])
                all_points_array[map_array[index]] = counter
                counter += 1

            selected_points.next()

        # reorder both_indexes
        both_indexes.clear()
        for i in range(point_count):
            if all_points_array[i] != -1:
                both_indexes.append(i)

        # reorder all_points_array
        all_points_array.clear()
        for i in range(point_count):
            all_points_array.append(-1)
        for i in range(both_indexes.length()):
            all_points_array[both_indexes[i]] = i

        fn_vtx_comp = OpenMaya.MFnSingleIndexedComponent()
        self.vtx_components = fn_vtx_comp.create(OpenMaya.MFn.kMeshVertComponent)
        vertex_indices = []
        skin_path = OpenMaya.MDagPath()

        for i in range(len(both_indexes)):
            fn_vtx_comp.addElement(both_indexes[i])
            vertex_indices.append(both_indexes[i])

        if self.task == "skinCluster":
            found_skin = False

            it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kSkinClusterFilter)
            while not it.isDone():
                fn_skin_cluster = OpenMayaAnim.MFnSkinCluster(it.item())
                fn_skin_cluster.getPathAtIndex(0, skin_path)
                if OpenMaya.MFnDagNode(skin_path.node()).partialPathName() == object_name:
                    self.skin_cluster = it.item()
                it.next()

            if self.skin_cluster.hasFn(OpenMaya.MFn.kSkinClusterFilter):
                found_skin = True

            if not found_skin:
                print("No skinCluster found on geometry.")
                return OpenMaya.MStatus.kFailure

            joint_names = []

            skin_path = OpenMaya.MDagPath()
            influence_array = OpenMaya.MDagPathArray()
            joint_map_array = OpenMaya.MIntArray()

            fn_skin_cluster = OpenMayaAnim.MFnSkinCluster(self.skin_cluster)

            fn_skin_cluster.getPathAtIndex(
                fn_skin_cluster.indexForOutputConnection(0), skin_path
            )
            fn_skin_cluster.influenceObjects(influence_array)

            for i in range(influence_array.length()):
                joint_names.append(
                    OpenMaya.MFnDagNode(influence_array[i]).name()
                )

            self.inf_count = len(joint_names)
            for i in range(self.inf_count):
                joint_map_array.append(i)

            for i, source in enumerate(joint_names):
                if joint_map_array[i] != i:
                    continue

                namespace = ""
                if ":" in source:
                    namespace = source.split(":")[0] + ":"

                joint_short = source.split(":")[-1]
                destination = joint_short

                search_tokens = search_string.split()
                replace_tokens = replace_string.split()
                zipped_tokens = zip(search_tokens, replace_tokens)
                for search_token, replace_token in zipped_tokens:
                    destination = destination.replace(
                        search_token, replace_token
                    )

                destination = namespace + destination

                if destination in joint_names and destination != source:
                    dest_index = joint_names.index(destination)
                    joint_map_array[i] = dest_index
                    joint_map_array[dest_index] = i

            self.weight_array.clear()
            script_util = OpenMaya.MScriptUtil()
            inf_count_ptr = script_util.asUintPtr()
            fn_skin_cluster.getWeights(
                skin_path,
                self.vtx_components,
                self.weight_array,
                inf_count_ptr,
            )

            self.old_weight_array.copy(self.weight_array)

            # mirroring weight array
            average_weights = OpenMaya.MDoubleArray()
            for l in range(self.inf_count):
                average_weights.append(0)

            for i in range(both_indexes.length()):
                index = both_indexes[i]
                start_index_b = i * self.inf_count

                # not middle
                if side_array[index] == direction and map_array[index] != index:
                    opposite_index = all_points_array[map_array[both_indexes[i]]]
                    start_index_a = opposite_index * self.inf_count

                    for k in range(self.inf_count):
                        self.weight_array[start_index_a + k] = self.weight_array[
                            start_index_b + joint_map_array[k]]

                # middle one
                elif map_array[index] == index:
                    for k in range(self.inf_count):
                        average_weights[k] = (
                            self.weight_array[start_index_b + k]
                            + self.weight_array[start_index_b + joint_map_array[k]]
                        ) * 0.5
                    for k in range(self.inf_count):
                        self.weight_array[start_index_b + k] = average_weights[k]

            print("[edgeFlowMirror] skinCluster mirroring complete.")

        if self.task in ("geometryFlip", "geometryMirror", "geometrySymmetry"):
            mirror_int = 0
            if self.task == "geometryMirror":
                mirror_int = 1
            if self.task == "geometrySymmetry":
                mirror_int = 2

            base_sel = OpenMaya.MSelectionList()
            base_sel.add(base_object_name)
            base_obj = OpenMaya.MDagPath()

            base_sel.getDagPath(0, base_obj, component)
            vertex_count = OpenMaya.MFnMesh(base_obj).numVertices()
            if vertex_count == 0:
                print("No vertices found.")
                return OpenMaya.MStatus.kFailure

            self.target_obj = dag_path_sel_shape

            fn_base_mesh = OpenMaya.MFnMesh(base_obj)
            base_points = OpenMaya.MPointArray()
            fn_base_mesh.getPoints(base_points)

            self.old_target_points.clear()
            self.new_target_points.clear()

            fn_target_mesh = OpenMaya.MFnMesh(self.target_obj)

            target_object_dag_path = OpenMaya.MDagPath()
            OpenMaya.MFnDagNode(self.target_obj).getPath(target_object_dag_path)

            target_points = OpenMaya.MPointArray()
            fn_target_mesh.getPoints(target_points, OpenMaya.MSpace.kObject)

            for i in range(target_points.length()):
                self.old_target_points.append(
                    OpenMaya.MFloatVector(
                        target_points[i].x,
                        target_points[i].y,
                        target_points[i].z,
                    )
                )
                self.new_target_points.append(
                    OpenMaya.MFloatVector(
                        target_points[i].x,
                        target_points[i].y,
                        target_points[i].z,
                    )
                )

            if mirror_int != 2:  # if it's not create symmetry shape
                if not do_vertex_space:
                    for i in range(len(both_indexes)):
                        opp_index = both_indexes[i]

                        if mirror_int == 0 or direction == side_array[opp_index]:
                            opp_map = map_array[opp_index]
                            offset = (
                                target_points[opp_index] - base_points[opp_index]
                            )

                            self.new_target_points.set(
                                OpenMaya.MFloatVector(
                                    base_points[opp_map].x - offset.x,
                                    base_points[opp_map].y + offset.y,
                                    base_points[opp_map].z + offset.z
                                ),
                                opp_map
                            )

                elif do_vertex_space:
                    vert_count = fn_base_mesh.numVertices()
                    face_count = fn_base_mesh.numPolygons()
                    connected_vertices = OpenMaya.MIntArray()
                    connected_faces = OpenMaya.MIntArray()
                    script_util = OpenMaya.MScriptUtil()
                    ptr = script_util.asIntPtr()

                    con_verts = [None] * vert_count
                    con_faces = [None] * vert_count
                    base_normals = [None] * vert_count
                    target_normals = [None] * vert_count

                    vertex_iter = OpenMaya.MItMeshVertex(base_obj)
                    for i in range(vert_count):
                        vertex_iter.setIndex(i, ptr)
                        vertex_iter.getConnectedVertices(connected_vertices)
                        vertex_iter.getConnectedFaces(connected_faces)
                        con_verts[i] = intArrayToList(connected_vertices)
                        con_faces[i] = intArrayToList(connected_faces)
                        vec = OpenMaya.MVector()

                        vertex_iter.getNormal(vec)
                        vec.normalize()
                        base_normals[i] = OpenMaya.MVector(vec)

                    target_vertex_iter = OpenMaya.MItMeshVertex(self.target_obj)
                    for i in range(vert_count):
                        vec = OpenMaya.MVector()
                        target_vertex_iter.getNormal(vec)
                        vec.normalize()
                        target_normals[i] = OpenMaya.MVector(vec)

                    face_iter = OpenMaya.MItMeshPolygon(base_obj)
                    verts_on_faces = [None] * face_count
                    for i in range(face_count):
                        face_iter.setIndex(i, ptr)
                        face_iter.getVertices(connected_vertices)
                        verts_on_faces[i] = intArrayToList(connected_vertices)

                    skips = [False] * vert_count
                    x_ids = [None] * vert_count
                    z_ids = [None] * vert_count
                    x_negs = [None] * vert_count
                    z_negs = [None] * vert_count

                    skips_counter = 0

                    # create matrices for one side
                    for i in range(len(both_indexes)):
                        b_index = both_indexes[i]
                        side_index = side_array[b_index]

                        # Don't do the right ones yet, they'll get mirrored.
                        if side_index == 1:
                            continue

                        do_skip_this_one = False

                        points_threshold = (
                            base_points[b_index] - target_points[b_index]
                        ).length()

                        map_threshold = (
                            base_points[map_array[b_index]]
                            - target_points[map_array[b_index]]
                        ).length()

                        if points_threshold < 0.00001 and map_threshold < 0.00001:
                            do_skip_this_one = True

                        if do_skip_this_one:
                            skips[b_index] = True
                            skips_counter += 1
                            continue

                        x_id = []
                        z_id = []
                        x_neg = []
                        z_neg = []

                        # get the average
                        #
                        average_pos = OpenMaya.MPoint(0, 0, 0)
                        for vertId in con_verts[b_index]:
                            average_pos.x += base_points[vertId].x
                            average_pos.y += base_points[vertId].y
                            average_pos.z += base_points[vertId].z

                        average_pos /= len(con_verts[b_index])

                        for f, face in enumerate(con_faces[b_index]):
                            two_dots = [-1, -1]
                            two_vecs = [None, None]

                            for vert in verts_on_faces[face]:
                                if vert != b_index and vert in con_verts[b_index]:
                                    for d in range(2):
                                        if two_dots[d] == -1:
                                            two_dots[d] = vert
                                            two_vecs[d] = OpenMaya.MVector(
                                                base_points[vert] - average_pos)
                                            break

                            # skip face if it's from middle vertex and not along middle edges
                            #
                            dot_0, dot_1 = two_dots
                            if not side_index and side_array[dot_0] and side_array[dot_1]:
                                continue

                            if f == 0:
                                first_vecs = list(two_vecs)

                                x_id.append(dot_0)
                                z_id.append(dot_1)
                                x_neg.append(False)
                                z_neg.append(False)

                            if f > 0:
                                # compare current 2 dots with first dot from first face
                                angle_0 = two_vecs[0].angle(first_vecs[0])
                                angle_1 = two_vecs[1].angle(first_vecs[0])
                                angle_0_neg = False
                                angle_1_neg = False

                                if angle_0 > math.pi * 0.5:
                                    angle_0 = math.pi - angle_0
                                    angle_0_neg = True
                                if angle_1 > math.pi * 0.5:
                                    angle_1 = math.pi - angle_1
                                    angle_1_neg = True

                                if angle_0 < angle_1:
                                    x_id.append(dot_0)
                                    z_id.append(dot_1)
                                    x_neg.append(angle_0_neg)
                                    z_neg.append(two_vecs[1].angle(first_vecs[1]) > math.pi * 0.5)

                                else:
                                    x_id.append(dot_1)
                                    z_id.append(dot_0)
                                    x_neg.append(angle_1_neg)
                                    z_neg.append(two_vecs[0].angle(first_vecs[1]) > math.pi * 0.5)

                        x_ids[b_index] = x_id
                        z_ids[b_index] = z_id

                        x_negs[b_index] = x_neg
                        z_negs[b_index] = z_neg

                    # now create the other ones by mirroring
                    #
                    for i in range(len(both_indexes)):
                        b_index = both_indexes[i]

                        if side_index != 1:
                            continue

                        if skips[map_array[b_index]]:
                            skips_counter += 1
                            skips[b_index] = True
                            continue

                        x_id = list(x_ids[map_array[b_index]])
                        z_id = list(z_ids[map_array[b_index]])

                        for k in range(len(x_id)):
                            x_id[k] = map_array[x_id[k]]
                            z_id[k] = map_array[z_id[k]]

                        x_ids[b_index] = x_id
                        z_ids[b_index] = z_id

                        x_negs[b_index] = x_negs[map_array[b_index]]
                        z_negs[b_index] = z_negs[map_array[b_index]]

                    for i in range(both_indexes.length()):

                        if map_array[both_indexes[i]] != -2:

                            b_index = both_indexes[i]

                            if skips[b_index]:
                                continue

                            if mirror_int == 0 or side_index in [direction, 0]:
                                ids_count = len(x_ids[b_index])
                                base_x = OpenMaya.MVector(0, 0, 0)
                                base_z = OpenMaya.MVector(0, 0, 0)

                                for k in range(ids_count):
                                    if x_negs[b_index][k]:
                                        x_mult = -1
                                    else:
                                        x_mult = 1
                                    if z_negs[b_index][k]:
                                        z_mult = -1
                                    else:
                                        z_mult = 1

                                    base_x += (
                                        OpenMaya.MVector(
                                            base_points[x_ids[b_index][k]]
                                            - base_points[b_index]
                                        )
                                    ) * x_mult

                                    base_z += (
                                        OpenMaya.MVector(
                                            base_points[z_ids[b_index][k]]
                                            - base_points[b_index]
                                        )
                                    ) * z_mult

                                base_x /= ids_count
                                base_z /= ids_count
                                base_x.normalize()
                                base_z.normalize()

                                base_mat = create_matrix_from_list(
                                    [
                                        base_x.x, base_x.y, base_x.z,
                                        0,
                                        base_normals[b_index].x,
                                        base_normals[b_index].y,
                                        base_normals[b_index].z,
                                        0,
                                        base_z.x,
                                        base_z.y,
                                        base_z.z,
                                        0,
                                        base_points[b_index].x,
                                        base_points[b_index].y,
                                        base_points[b_index].z,
                                        1,
                                    ]
                                )
                                change_world = create_matrix_from_pos(
                                    target_points[b_index]
                                )
                                change_local = change_world * base_mat.inverse()

                                if side_index == 0:  # middle vertex

                                    middle_id = -1
                                    for nId in x_ids[b_index] + z_ids[b_index]:
                                        if side_array[nId] == 0:
                                            middle_id = nId
                                            continue

                                    # check which angle is closer
                                    #
                                    middle_id_vect = OpenMaya.MVector(
                                        base_points[middle_id] - base_points[b_index]
                                    )
                                    angle_x = middle_id_vect.angle(base_x)
                                    angle_z = middle_id_vect.angle(base_z)
                                    if angle_x > math.pi * 0.5:
                                        angle_x = math.pi - angle_x
                                    if angle_z > math.pi * 0.5:
                                        angle_z = math.pi - angle_z

                                    if angle_x < angle_z:
                                        centered_local = create_matrix_from_pos(
                                            OpenMaya.MPoint(
                                                change_local(3, 0),
                                                change_local(3, 1),
                                                -change_local(3, 2)
                                            )
                                        )
                                    else:
                                        centered_local = create_matrix_from_pos(
                                            OpenMaya.MPoint(
                                                -change_local(3, 0),
                                                change_local(3, 1),
                                                change_local(3, 2)
                                            )
                                        )

                                    change_target = centered_local * base_mat
                                    mapped_b_index = b_index

                                elif side_index != 0:  # not middle vertex
                                    mapped_b_index = map_array[b_index]

                                    target_x = OpenMaya.MVector(0, 0, 0)
                                    target_z = OpenMaya.MVector(0, 0, 0)

                                    ids_count = len(x_ids[mapped_b_index])

                                    for k in range(ids_count):
                                        if x_negs[mapped_b_index][k]:
                                            x_mult = -1
                                        else:
                                            x_mult = 1
                                        if z_negs[mapped_b_index][k]:
                                            z_mult = -1
                                        else:
                                            z_mult = 1

                                        target_x += (
                                            OpenMaya.MVector(
                                                base_points[x_ids[mapped_b_index][k]]
                                                - base_points[mapped_b_index]
                                            )
                                        ) * x_mult

                                        target_z += (
                                            OpenMaya.MVector(
                                                base_points[z_ids[mapped_b_index][k]]
                                                - base_points[mapped_b_index]
                                            )
                                        ) * z_mult

                                    target_x /= ids_count
                                    target_z /= ids_count

                                    target_x.normalize()
                                    target_z.normalize()

                                    target_mat = create_matrix_from_list(
                                        [
                                            target_x.x,
                                            target_x.y,
                                            target_x.z,
                                            0,
                                            base_normals[mapped_b_index].x,
                                            base_normals[mapped_b_index].y,
                                            base_normals[mapped_b_index].z,
                                            0,
                                            target_z.x,
                                            target_z.y,
                                            target_z.z,
                                            0,
                                            base_points[mapped_b_index].x,
                                            base_points[mapped_b_index].y,
                                            base_points[mapped_b_index].z,
                                            1
                                        ]
                                    )
                                    change_target = change_local * target_mat

                                self.new_target_points.set(
                                    OpenMaya.MFloatVector(
                                        change_target(3, 0),
                                        change_target(3, 1),
                                        change_target(3, 2)
                                    ),
                                    mapped_b_index,
                                )

            elif mirror_int == 2:  # create symmetry shape
                for i in range(both_indexes.length()):
                    target_vector = target_points[both_indexes[i]]
                    map_index = map_array[both_indexes[i]]
                    if side_array[both_indexes[i]] == 1 and map_index != -1:
                        target_vector.x = target_vector.x * -1

                for i in range(both_indexes.length()):
                    target_vector = target_points[both_indexes[i]]
                    map_index = map_array[both_indexes[i]]
                    if map_index != -1:

                        x = (target_vector.x + target_points[map_index].x) * 0.5
                        y = (target_vector.y + target_points[map_index].y) * 0.5
                        z = (target_vector.z + target_points[map_index].z) * 0.5
                        target_vector.x = x
                        target_vector.y = y
                        target_vector.z = z
                        target_points[map_index].x = x
                        target_points[map_index].y = y
                        target_points[map_index].z = z

                        if map_index == both_indexes[i]:  # middlePoint
                            target_vector.x = 0

                for i in range(both_indexes.length()):
                    target_vector = target_points[both_indexes[i]]
                    map_index = map_array[both_indexes[i]]
                    if map_index != -1:
                        if side_array[both_indexes[i]] == 1:  # middle
                            target_vector.x = target_vector.x * -1

                        self.new_target_points.set(
                            OpenMaya.MFloatVector(
                                target_vector.x,
                                target_vector.y,
                                target_vector.z
                            ),
                            both_indexes[i],
                        )

                # selecting wrong points:
                fn_vtx_comp = OpenMaya.MFnSingleIndexedComponent()
                self.vtx_components = fn_vtx_comp.create(OpenMaya.MFn.kMeshVertComponent)
                select_points = OpenMaya.MSelectionList()

                missing_points = False
                selected_points.reset()
                while not selected_points.isDone():
                    index = selected_points.index()
                    if map_array[index] == -1:  # if no mirrorPoint found
                        fn_vtx_comp.addElement(index)
                        missing_points = True

                    selected_points.next()

                if missing_points:
                    select_points.clear()
                    select_points.add(dag_path_sel_shape, self.vtx_components)
                    print("Some points couldn't be mirrored (see selection)")
                    OpenMaya.MGlobal.setActiveSelectionList(select_points)

                else:
                    print("Found mirrorPoint for each selected point")

        return self.redoIt()

    def redoIt(self):
        self.manipulate_object(True)

    def undoIt(self):
        self.manipulate_object(False)

    def isUndoable(self):
        return True

    def analyze_topology(self, edge):
        selection = OpenMaya.MSelectionList()
        selection.add(edge)
        dag_path_sel_shape = OpenMaya.MDagPath()
        component = OpenMaya.MObject()
        iterator = OpenMaya.MItSelectionList(selection)
        iterator.getDagPath(dag_path_sel_shape, component)
        selected_edges = OpenMaya.MItMeshEdge(dag_path_sel_shape, component)

        fn_mesh = OpenMaya.MFnMesh(dag_path_sel_shape)
        point_count = fn_mesh.numVertices()
        edge_count = fn_mesh.numEdges()
        poly_count = fn_mesh.numPolygons()

        base_object_name = fn_mesh.name()

        selected_edges.reset()
        first_edge = selected_edges.index()
        map_array = OpenMaya.MIntArray()
        side_array = OpenMaya.MIntArray()

        checked_v = OpenMaya.MIntArray()
        side_v = OpenMaya.MIntArray()
        checked_p = OpenMaya.MIntArray()
        checked_e = OpenMaya.MIntArray()
        for x in range(point_count):
            checked_v.append(-1)
            side_v.append(-1)

        for x in range(edge_count):
            checked_e.append(-1)

        for x in range(poly_count):
            checked_p.append(-1)

        l_face_list = OpenMaya.MIntArray()
        r_face_list = OpenMaya.MIntArray()

        l_current_p = 0
        r_current_p = 0
        poly_iter = OpenMaya.MItMeshPolygon(dag_path_sel_shape)
        edge_iter = OpenMaya.MItMeshEdge(dag_path_sel_shape)

        l_edge_queue = OpenMaya.MIntArray()
        r_edge_queue = OpenMaya.MIntArray()

        l_edge_queue.append(first_edge)
        r_edge_queue.append(first_edge)

        script_util = OpenMaya.MScriptUtil()
        ptr = script_util.asIntPtr()
        l_edge_vertices = script_util.asInt2Ptr()
        r_edge_vertices = script_util.asInt2Ptr()
        l_if_checked_vertices = script_util.asInt2Ptr()
        r_face_edge_vertices = script_util.asInt2Ptr()

        l_face_edges = []
        r_face_edges = []

        # create statusbar
        #
        status_window = cmds.window(title="Finding Opposite Vertices")
        cmds.columnLayout()

        progress_control = cmds.progressBar(maxValue=10, width=300)

        cmds.showWindow(status_window)
        steps_count = 100
        cmds.progressBar(
            progress_control,
            edit=True,
            beginProgress=True,
            isInterruptable=True,
            status="Finding Mirrored Vertices",
            maxValue=steps_count
        )

        step_size = (edge_count / 2) / 100
        step_increment = 0

        # get connected Edges from Faces
        num_polys = fn_mesh.numPolygons()
        connected_edges_per_faces = [None] * num_polys
        edges = OpenMaya.MIntArray()

        for i in range(num_polys):
            poly_iter.setIndex(i, ptr)
            poly_iter.getEdges(edges)
            connected_edges_per_faces[i] = list(edges)

        while True:
            if l_edge_queue.length() == 0:
                cmds.progressBar(progress_control, edit=True, endProgress=True)
                cmds.deleteUI(status_window, window=True)
                break

            # progressbar
            #
            step_increment += 1
            if step_increment >= step_size:
                cmds.progressBar(progress_control, edit=True, step=1)
                step_increment = 0

            l_current_e = l_edge_queue[0]
            r_current_e = r_edge_queue[0]

            l_edge_queue.remove(0)
            r_edge_queue.remove(0)

            checked_e[l_current_e] = r_current_e
            checked_e[r_current_e] = l_current_e

            if l_current_e == r_current_e and l_current_e != first_edge:
                continue

            # get the left face
            edge_iter.setIndex(l_current_e, ptr)
            edge_iter.getConnectedFaces(l_face_list)
            if len(l_face_list) == 1:
                l_current_p = l_face_list[0]
            elif checked_p[l_face_list[0]] == -1 and checked_p[l_face_list[1]] != -1:
                l_current_p = l_face_list[0]
            elif checked_p[l_face_list[1]] == -1 and checked_p[l_face_list[0]] != -1:
                l_current_p = l_face_list[1]
            elif checked_p[l_face_list[0]] == -1 and checked_p[l_face_list[1]] == -1:
                l_current_p = l_face_list[0]
                checked_p[l_current_p] = -2

            # get the right face
            edge_iter.setIndex(r_current_e, ptr)
            edge_iter.getConnectedFaces(r_face_list)
            if len(r_face_list) == 1:
                r_current_p = r_face_list[0]
            elif checked_p[r_face_list[0]] == -1 and checked_p[r_face_list[1]] != -1:
                r_current_p = r_face_list[0]
            elif checked_p[r_face_list[1]] == -1 and checked_p[r_face_list[0]] != -1:
                r_current_p = r_face_list[1]
            elif checked_p[r_face_list[1]] == -1 and checked_p[r_face_list[0]] == -1:
                return OpenMaya.MStatus.kFailure
            elif checked_p[r_face_list[1]] != -1 and checked_p[r_face_list[0]] != -1:
                continue

            checked_p[r_current_p] = l_current_p
            checked_p[l_current_p] = r_current_p

            fn_mesh.getEdgeVertices(l_current_e, l_edge_vertices)
            l_edge_vertices_0 = script_util.getInt2ArrayItem(l_edge_vertices, 0, 0)
            l_edge_vertices_1 = script_util.getInt2ArrayItem(l_edge_vertices, 0, 1)

            fn_mesh.getEdgeVertices(r_current_e, r_edge_vertices)
            r_edge_vertices_0 = script_util.getInt2ArrayItem(r_edge_vertices, 0, 0)
            r_edge_vertices_1 = script_util.getInt2ArrayItem(r_edge_vertices, 0, 1)

            if l_current_e == first_edge:
                r_edge_vertices_0 = script_util.getInt2ArrayItem(r_edge_vertices, 0, 0)
                r_edge_vertices_1 = script_util.getInt2ArrayItem(r_edge_vertices, 0, 1)
                l_edge_vertices_0 = script_util.getInt2ArrayItem(l_edge_vertices, 0, 0)
                l_edge_vertices_1 = script_util.getInt2ArrayItem(l_edge_vertices, 0, 1)

                checked_v[l_edge_vertices_0] = r_edge_vertices_0
                checked_v[l_edge_vertices_1] = r_edge_vertices_1
                checked_v[r_edge_vertices_0] = l_edge_vertices_0
                checked_v[r_edge_vertices_1] = l_edge_vertices_1
            else:
                if checked_v[l_edge_vertices_0] == -1 and checked_v[r_edge_vertices_0] == -1:
                    checked_v[l_edge_vertices_0] = r_edge_vertices_0
                    checked_v[r_edge_vertices_0] = l_edge_vertices_0
                if checked_v[l_edge_vertices_1] == -1 and checked_v[r_edge_vertices_1] == -1:
                    checked_v[l_edge_vertices_1] = r_edge_vertices_1
                    checked_v[r_edge_vertices_1] = l_edge_vertices_1
                if checked_v[l_edge_vertices_0] == -1 and checked_v[r_edge_vertices_1] == -1:
                    checked_v[l_edge_vertices_0] = r_edge_vertices_1
                    checked_v[r_edge_vertices_1] = l_edge_vertices_0
                if checked_v[l_edge_vertices_1] == -1 and checked_v[r_edge_vertices_0] == -1:
                    checked_v[l_edge_vertices_1] = r_edge_vertices_0
                    checked_v[r_edge_vertices_0] = l_edge_vertices_1

            side_v[l_edge_vertices_0] = 2
            side_v[l_edge_vertices_1] = 2
            side_v[r_edge_vertices_0] = 1
            side_v[r_edge_vertices_1] = 1

            r_face_edges_count = 0
            for edge in connected_edges_per_faces[r_current_p]:
                if len(r_face_edges) > r_face_edges_count:
                    r_face_edges[r_face_edges_count] = edge
                else:
                    r_face_edges.append(edge)
                r_face_edges_count += 1

            l_face_edges_count = 0
            for edge in connected_edges_per_faces[l_current_p]:
                if len(l_face_edges) > l_face_edges_count:
                    l_face_edges[l_face_edges_count] = edge
                else:
                    l_face_edges.append(edge)
                l_face_edges_count += 1

            for i in range(l_face_edges_count):

                if checked_e[l_face_edges[i]] == -1:

                    edge_iter.setIndex(l_current_e, ptr)

                    if edge_iter.connectedToEdge(l_face_edges[i]) \
                            and l_current_e != l_face_edges[i]:

                        fn_mesh.getEdgeVertices(
                            l_face_edges[i], l_if_checked_vertices
                        )
                        l_if_checked_vertex_0 = script_util.getInt2ArrayItem(
                            l_if_checked_vertices, 0, 0
                        )
                        l_if_checked_vertex_1 = script_util.getInt2ArrayItem(
                            l_if_checked_vertices, 0, 1
                        )

                        if l_if_checked_vertex_0 == l_edge_vertices_0 \
                                or l_if_checked_vertex_0 == l_edge_vertices_1:

                            l_checked_vertex = l_if_checked_vertex_0
                            l_non_checked_vertex = l_if_checked_vertex_1

                        elif l_if_checked_vertex_1 == l_edge_vertices_0 \
                                or l_if_checked_vertex_1 == l_edge_vertices_1:

                            l_checked_vertex = l_if_checked_vertex_1
                            l_non_checked_vertex = l_if_checked_vertex_0

                        else:
                            continue

                        for k in range(r_face_edges_count):
                            edge_iter.setIndex(r_current_e, ptr)
                            if edge_iter.connectedToEdge(r_face_edges[k]) \
                                    and r_current_e != r_face_edges[k]:
                                fn_mesh.getEdgeVertices(
                                    r_face_edges[k], r_face_edge_vertices
                                )
                                r_face_edge_vertex_0 = script_util.getInt2ArrayItem(
                                    r_face_edge_vertices, 0, 0
                                )
                                r_face_edge_vertex_1 = script_util.getInt2ArrayItem(
                                    r_face_edge_vertices, 0, 1
                                )

                                if r_face_edge_vertex_0 == checked_v[l_checked_vertex]:
                                    checked_v[l_non_checked_vertex] = r_face_edge_vertex_1
                                    checked_v[r_face_edge_vertex_1] = l_non_checked_vertex
                                    side_v[l_non_checked_vertex] = 2
                                    side_v[r_face_edge_vertex_1] = 1
                                    l_edge_queue.append(l_face_edges[i])
                                    r_edge_queue.append(r_face_edges[k])

                                if r_face_edge_vertex_1 == checked_v[l_checked_vertex]:
                                    checked_v[l_non_checked_vertex] = r_face_edge_vertex_0
                                    checked_v[r_face_edge_vertex_0] = l_non_checked_vertex
                                    side_v[l_non_checked_vertex] = 2
                                    side_v[r_face_edge_vertex_0] = 1
                                    l_edge_queue.append(l_face_edges[i])
                                    r_edge_queue.append(r_face_edges[k])

        x_average_2 = 0
        x_average_1 = 0
        check_pos_point = OpenMaya.MPoint()
        for i in range(point_count):
            if checked_v[i] != i and checked_v[i] != -1:
                fn_mesh.getPoint(checked_v[i], check_pos_point)
                if side_v[i] == 2:
                    x_average_2 += check_pos_point.x
                if side_v[i] == 1:
                    x_average_1 += check_pos_point.x

        switch_side = x_average_2 < x_average_1

        for i in range(point_count):
            map_array.append(checked_v[i])
            if checked_v[i] != i:
                if not switch_side:
                    side_array.append(side_v[i])
                else:
                    if side_v[i] == 2:
                        side_array.append(1)
                    else:
                        side_array.append(2)
            else:
                side_array.append(0)

        for i in range(len(map_array)):
            if map_array[i] == -1:
                map_array[i] = i

        return map_array, side_array, base_object_name


def cmdCreator():
    return OpenMayaMPx.asMPxPtr(EdgeFlowMirrorCommand())


def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Thomas Bittner", "3.3", "Any")
    try:
        mplugin.registerCommand(kPluginCmdName, cmdCreator)
    except:
        sys.stderr.write("Failed to register command: %s\n" % kPluginCmdName)
        raise


def uninitializePlugin(mobject):
    m_plugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        m_plugin.deregisterCommand(kPluginCmdName)
    except Exception:
        sys.stderr.write("Failed to unregister command: %s\n" % kPluginCmdName)
        raise


def getDagPath(name):
    sel = OpenMaya.MSelectionList()
    sel.add(name)
    obj = OpenMaya.MDagPath()
    component = OpenMaya.MObject()
    sel.getDagPath(0, obj, component)
    return obj


def intArrayToList(array):
    new_list = [0] * len(array)
    for i in range(len(array)):
        new_list[i] = array[i]
    return new_list


def create_matrix_from_pos(pos):
    mat = OpenMaya.MMatrix()
    OpenMaya.MScriptUtil.createMatrixFromList(
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, pos.x, pos.y, pos.z, 1], mat
    )
    return mat


def create_matrix_from_list(mat_list):
    mat = OpenMaya.MMatrix()
    OpenMaya.MScriptUtil.createMatrixFromList(mat_list, mat)
    return mat
