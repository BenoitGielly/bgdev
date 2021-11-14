"""
=====================================================================

edgeFlowMirror 3.4 (c) 2007 - 2016 by Thomas Bittner

(c) 2007 - 2016 by Thomas Bittner
thomasbittner@hotmail.de

This tool mirrors mainly skin weights, geometry and component selection.
Opposite mirror points are found per edge flow, and NOT via position.
This means, that only the way the edges are connected together is relevant,
and the actual positions of the vertices does not matter.
one of the inputs the tool requires, is one of the middle edges
The character can even be in a different pose and most parts of the tool will
still work.

=====================================================================

"""
import os

from PySide2 import QtCore, QtWidgets
from maya import OpenMayaUI, cmds, mel
import shiboken2


def load_plugin():
    plugin_path = os.path.join(os.path.dirname(__file__), "edgeFlowMirror.py")
    try:
        cmds.loadPlugin(plugin_path, quiet=True)
    except RuntimeError:
        cmds.loadPlugin("edgeFlowMirror", quiet=True)
    except Exception:
        raise RuntimeError("Cannot find plugin in path {}".format(plugin_path))


main_win = None


def show():
    global main_win

    load_plugin()

    if main_win is not None:
        main_win.close()

    main_win = EdgeFlowMirrorUI()
    main_win.show()
    return main_win


def get_maya_window():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    if ptr:
        try:
            ptr = long(ptr)
        except NameError:
            ptr = int(ptr)
        return shiboken2.wrapInstance(ptr, QtWidgets.QWidget)
    return None


class EdgeFlowMirrorUI(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_window()):
        super(EdgeFlowMirrorUI, self).__init__(parent)

        app = QtWidgets.QApplication.instance()
        screen = app.screens()[0]
        self.dpi_scale = screen.logicalDotsPerInch() / 100.0

        mid_edge_lyt = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        mid_edge_label = QtWidgets.QLabel("Middle Edge:", parent=self)
        self.mid_edge_line = QtWidgets.QLineEdit("", parent=self)
        self.mid_edge_line.setDisabled(True)
        self.mid_edge_btn = QtWidgets.QPushButton(
            "Set Middle Edge", parent=self
        )
        self.mid_edge_recomp_btn = QtWidgets.QPushButton(
            "Recompute", parent=self
        )
        self.mid_edge_optmz_cbox = QtWidgets.QCheckBox("Optimize", parent=self)
        self.mid_edge_optmz_cbox.setChecked(True)
        mid_edge_lyt.addWidget(mid_edge_label)
        mid_edge_lyt.addWidget(self.mid_edge_line)
        mid_edge_lyt.addWidget(self.mid_edge_btn)
        mid_edge_lyt.addWidget(self.mid_edge_recomp_btn)
        mid_edge_lyt.addWidget(self.mid_edge_optmz_cbox)

        tab_widget = QtWidgets.QTabWidget()
        skin_cluster_tab = QtWidgets.QWidget()
        geometry_tab = QtWidgets.QWidget()
        selection_tab = QtWidgets.QWidget()
        deformers_tab = QtWidgets.QWidget()
        blend_shape_tab = QtWidgets.QWidget()

        tab_widget.addTab(skin_cluster_tab, "SkinCluster")
        tab_widget.addTab(geometry_tab, "Geometry")
        tab_widget.addTab(selection_tab, "Component Selection")
        tab_widget.addTab(deformers_tab, "Deformer Weights")
        tab_widget.addTab(blend_shape_tab, "BlendShape Targets")

        self.description_label = QtWidgets.QLabel(
            "(C) 2007 - 2016 by Thomas Bittner", parent=self
        )
        self.setWindowTitle("edgeFlowMirror 3.4")

        # SkinCluster
        skin_cluster_lyt = QtWidgets.QVBoxLayout(skin_cluster_tab)
        skin_cluster_lyt.setAlignment(QtCore.Qt.AlignTop)
        skin_cluster_lyt.setSpacing(3)

        self.mirror_skin_l_to_r_btn = QtWidgets.QPushButton(
            "Left -> Right", parent=self
        )
        self.mirror_skin_r_to_l_btn = QtWidgets.QPushButton(
            "Right -> Left", parent=self
        )

        mirror_weights_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        mirror_weights_lyt.addWidget(
            self.create_fixed_label("Mirror Weights:", width=120)
        )
        mirror_weights_lyt.addWidget(self.mirror_skin_l_to_r_btn)
        mirror_weights_lyt.addWidget(self.mirror_skin_r_to_l_btn)
        skin_cluster_lyt.addLayout(mirror_weights_lyt)

        left_joints_prefix_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        left_joints_prefix_lyt.addWidget(
            self.create_fixed_label("Left tokens", width=120)
        )
        self.left_joints_prefix_line = QtWidgets.QLineEdit(
            "L_ Left left", parent=self
        )
        left_joints_prefix_lyt.addWidget(self.left_joints_prefix_line)
        skin_cluster_lyt.addLayout(left_joints_prefix_lyt)

        right_joints_prefix_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        right_joints_prefix_lyt.addWidget(
            self.create_fixed_label("Right tokens", width=120)
        )
        self.right_joints_prefix_line = QtWidgets.QLineEdit(
            "R_ Right right", parent=self
        )
        right_joints_prefix_lyt.addWidget(self.right_joints_prefix_line)
        skin_cluster_lyt.addLayout(right_joints_prefix_lyt)

        self.mirror_skin_blend_l_to_r_btn = QtWidgets.QPushButton(
            "Left -> Right", parent=self
        )
        self.mirror_skin_blend_r_to_l_btn = QtWidgets.QPushButton(
            "Right -> Left", parent=self
        )

        mirror_blend_weights_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        mirror_blend_weights_lyt.addWidget(
            self.create_fixed_label("Mirror Blend Weights:", width=120)
        )
        mirror_blend_weights_lyt.addWidget(self.mirror_skin_blend_l_to_r_btn)
        mirror_blend_weights_lyt.addWidget(self.mirror_skin_blend_r_to_l_btn)
        skin_cluster_lyt.addLayout(mirror_blend_weights_lyt)

        # Geometry
        geometry_lyt = QtWidgets.QVBoxLayout(geometry_tab)
        geometry_lyt.setAlignment(QtCore.Qt.AlignTop)
        geometry_lyt.setSpacing(3)

        self.base_mesh_line = QtWidgets.QLineEdit("", parent=self)
        self.select_base_mesh_btn = QtWidgets.QPushButton(
            "Selected", parent=self
        )
        base_mesh_lyt = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight)
        base_mesh_lyt.addWidget(self.create_fixed_label("Base Mesh:"))
        base_mesh_lyt.addWidget(self.base_mesh_line)
        base_mesh_lyt.addWidget(self.select_base_mesh_btn)
        geometry_lyt.addLayout(base_mesh_lyt)

        self.do_geometry_vertex_space = QtWidgets.QCheckBox(
            "Calculate offset in space of surrounding faces of base mesh",
            parent=self,
        )
        geometry_lyt.addWidget(self.do_geometry_vertex_space)

        mirror_mesh_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        mirror_mesh_lyt.addWidget(self.create_fixed_label("Mirror Mesh:"))

        self.mirror_mesh_l_to_r_btn = QtWidgets.QPushButton(
            "Left -> Right", parent=self
        )
        mirror_mesh_lyt.addWidget(self.mirror_mesh_l_to_r_btn)

        self.mirror_mesh_r_to_l_btn = QtWidgets.QPushButton(
            "Right -> Left", parent=self
        )
        mirror_mesh_lyt.addWidget(self.mirror_mesh_r_to_l_btn)
        geometry_lyt.addLayout(mirror_mesh_lyt)

        flip_mesh_button_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        flip_mesh_button_lyt.addWidget(self.create_fixed_label("Flip Mesh:"))
        self.flip_mesh_btn = QtWidgets.QPushButton(
            "Right <-> Left", parent=self
        )
        flip_mesh_button_lyt.addWidget(self.flip_mesh_btn)
        geometry_lyt.addLayout(flip_mesh_button_lyt)

        symmetry_separator = QtWidgets.QFrame()
        symmetry_separator.setFrameShape(QtWidgets.QFrame.HLine)
        symmetry_separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        geometry_lyt.addWidget(symmetry_separator)

        symmetry_mesh_button_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        symmetry_mesh_button_lyt.addWidget(
            self.create_fixed_label("Symmetry Mesh:")
        )
        self.symmetry_mesh_btn = QtWidgets.QPushButton(
            "Right <-> Left", parent=self
        )
        symmetry_mesh_button_lyt.addWidget(self.symmetry_mesh_btn)
        geometry_lyt.addLayout(symmetry_mesh_button_lyt)

        # selection
        selection_lyt = QtWidgets.QVBoxLayout(selection_tab)
        selection_lyt.setAlignment(QtCore.Qt.AlignTop)
        selection_lyt.setSpacing(3)

        self.flip_selection_btn = QtWidgets.QPushButton(
            "Left <-> Right", parent=self
        )
        selection_flip_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        selection_flip_lyt.addWidget(self.create_fixed_label("Flip:"))
        selection_flip_lyt.addWidget(self.flip_selection_btn)
        selection_lyt.addLayout(selection_flip_lyt)

        self.mirror_selection_btn = QtWidgets.QPushButton(
            "Left <-> Right", parent=self
        )
        selection_mirror_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        selection_mirror_lyt.addWidget(
            self.create_fixed_label("Add other sides:")
        )
        selection_mirror_lyt.addWidget(self.mirror_selection_btn)
        selection_lyt.addLayout(selection_mirror_lyt)

        mirror_selection_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        mirror_selection_lyt.addWidget(
            self.create_fixed_label("Mirror Selection:")
        )
        self.mirror_selection_l_to_r_btn = QtWidgets.QPushButton(
            "Left -> Right", parent=self
        )
        self.mirror_selection_r_to_l_btn = QtWidgets.QPushButton(
            "Right -> Left", parent=self
        )
        mirror_selection_lyt.addWidget(self.mirror_selection_l_to_r_btn)
        mirror_selection_lyt.addWidget(self.mirror_selection_r_to_l_btn)
        selection_lyt.addLayout(mirror_selection_lyt)

        self.layout = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.TopToBottom, self
        )
        self.layout.addLayout(mid_edge_lyt)
        self.layout.addWidget(tab_widget)
        self.layout.addWidget(self.description_label)

        # BlendShape
        blend_shape_lyt = QtWidgets.QVBoxLayout(blend_shape_tab)
        blend_shape_lyt.setAlignment(QtCore.Qt.AlignTop)
        blend_shape_lyt.setSpacing(3)

        self.blend_shape_line = QtWidgets.QLineEdit("", parent=self)
        self.select_blend_shape_btn = QtWidgets.QPushButton(
            "Selected", parent=self
        )
        blend_shape_node_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        blend_shape_node_lyt.addWidget(
            QtWidgets.QLabel("blendShape:", parent=self)
        )
        blend_shape_node_lyt.addWidget(self.blend_shape_line)
        blend_shape_node_lyt.addWidget(self.select_blend_shape_btn)
        blend_shape_lyt.addLayout(blend_shape_node_lyt)

        self.target_list = QtWidgets.QListWidget(parent=self)
        self.target_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        blend_shape_lyt.addWidget(self.target_list)

        mirror_blend_shape_target_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        mirror_blend_shape_target_lyt.addWidget(
            self.create_fixed_label("Mirror Marked Targets", width=130)
        )
        self.mirror_blend_shape_target_l_to_r_btn = QtWidgets.QPushButton(
            "Left -> Right", parent=self
        )
        self.mirror_blend_shape_target_r_to_l_btn = QtWidgets.QPushButton(
            "Right -> Left", parent=self
        )
        mirror_blend_shape_target_lyt.addWidget(
            self.mirror_blend_shape_target_l_to_r_btn
        )
        mirror_blend_shape_target_lyt.addWidget(
            self.mirror_blend_shape_target_r_to_l_btn
        )
        blend_shape_lyt.addLayout(mirror_blend_shape_target_lyt)

        flip_blend_shape_target_button_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        flip_blend_shape_target_button_lyt.addWidget(
            self.create_fixed_label("Flip Marked Targets:", width=130)
        )
        self.flip_blend_shape_target_btn = QtWidgets.QPushButton(
            "Right <-> Left", parent=self
        )
        flip_blend_shape_target_button_lyt.addWidget(
            self.flip_blend_shape_target_btn
        )
        blend_shape_lyt.addLayout(flip_blend_shape_target_button_lyt)

        # Deformers
        deformers_lyt = QtWidgets.QVBoxLayout(deformers_tab)
        deformers_lyt.setAlignment(QtCore.Qt.AlignTop)
        deformers_lyt.setSpacing(3)

        mirror_blend_shape_node_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        mirror_blend_shape_node_lyt.addWidget(
            self.create_fixed_label(
                "Mirror Selected Deformer Weights", width=180
            )
        )
        self.mirror_deformer_l_to_r_btn = QtWidgets.QPushButton(
            "Left -> Right", parent=self
        )
        self.mirror_deformer_r_to_l_btn = QtWidgets.QPushButton(
            "Right -> Left", parent=self
        )
        mirror_blend_shape_node_lyt.addWidget(self.mirror_deformer_l_to_r_btn)
        mirror_blend_shape_node_lyt.addWidget(self.mirror_deformer_r_to_l_btn)
        deformers_lyt.addLayout(mirror_blend_shape_node_lyt)

        flip_blend_shape_node_button_lyt = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight
        )
        flip_blend_shape_node_button_lyt.addWidget(
            self.create_fixed_label(
                "Flip Selected Deformer Weights:", width=180
            )
        )
        self.flip_blend_shape_node_btn = QtWidgets.QPushButton(
            "Right <-> Left", parent=self
        )
        flip_blend_shape_node_button_lyt.addWidget(
            self.flip_blend_shape_node_btn
        )
        deformers_lyt.addLayout(flip_blend_shape_node_button_lyt)

        # connect buttons
        self.connect(
            self.mid_edge_btn,
            QtCore.SIGNAL("clicked()"),
            self.middle_edge_button_clicked,
        )
        self.connect(
            self.mid_edge_recomp_btn,
            QtCore.SIGNAL("clicked()"),
            self.middle_edge_button_recompute_clicked,
        )
        self.connect(
            self.select_base_mesh_btn,
            QtCore.SIGNAL("clicked()"),
            self.select_base_mesh_button_clicked,
        )
        self.connect(
            self.mid_edge_optmz_cbox,
            QtCore.SIGNAL("clicked(bool)"),
            self.middle_edge_optimize_toggled,
        )

        self.connect(
            self.mirror_skin_l_to_r_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_skin_cluster(1),
        )
        self.connect(
            self.mirror_skin_r_to_l_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_skin_cluster(2),
        )
        self.connect(
            self.mirror_skin_blend_l_to_r_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_skin_cluster_blend(1),
        )
        self.connect(
            self.mirror_skin_blend_r_to_l_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_skin_cluster_blend(2),
        )

        self.connect(
            self.mirror_mesh_l_to_r_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_mesh("geometryMirror", 1),
        )
        self.connect(
            self.mirror_mesh_r_to_l_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_mesh("geometryMirror", 2),
        )
        self.connect(
            self.flip_mesh_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_mesh("geometryFlip", 1),
        )
        self.connect(
            self.symmetry_mesh_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_mesh("geometrySymmetry", 0),
        )

        self.connect(
            self.flip_selection_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.select_mirrored_components(
                1, self.mid_edge_optmz_cbox.isChecked()
            ),
        )
        self.connect(
            self.mirror_selection_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.select_mirrored_components(
                0, self.mid_edge_optmz_cbox.isChecked()
            ),
        )

        self.connect(
            self.mirror_selection_l_to_r_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.select_mirrored_components(
                2, self.mid_edge_optmz_cbox.isChecked(), 2
            ),
        )
        self.connect(
            self.mirror_selection_r_to_l_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.select_mirrored_components(
                2, self.mid_edge_optmz_cbox.isChecked(), 1
            ),
        )

        self.connect(
            self.select_blend_shape_btn,
            QtCore.SIGNAL("clicked()"),
            self.update_blend_shape_node,
        )
        self.connect(
            self.flip_blend_shape_target_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_weight_map(
                self.blend_shape_line.text(),
                "flip",
                0,
                self.list_items_to_texts(self.target_list.selectedItems()),
                self.mid_edge_line.text(),
                self.mid_edge_optmz_cbox.isChecked(),
            ),
        )
        self.connect(
            self.mirror_blend_shape_target_l_to_r_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_weight_map(
                self.blend_shape_line.text(),
                "mirror",
                1,
                self.list_items_to_texts(self.target_list.selectedItems()),
                self.mid_edge_line.text(),
                self.mid_edge_optmz_cbox.isChecked(),
            ),
        )
        self.connect(
            self.mirror_blend_shape_target_r_to_l_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_weight_map(
                self.blend_shape_line.text(),
                "mirror",
                2,
                self.list_items_to_texts(self.target_list.selectedItems()),
                self.mid_edge_line.text(),
                self.mid_edge_optmz_cbox.isChecked(),
            ),
        )

        self.connect(
            self.flip_blend_shape_node_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_weight_map(
                self.get_selected_deformer(),
                "flip",
                0,
                [],
                self.mid_edge_line.text(),
                self.mid_edge_optmz_cbox.isChecked(),
            ),
        )
        self.connect(
            self.mirror_deformer_l_to_r_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_weight_map(
                self.get_selected_deformer(),
                "mirror",
                1,
                [],
                self.mid_edge_line.text(),
                self.mid_edge_optmz_cbox.isChecked(),
            ),
        )
        self.connect(
            self.mirror_deformer_r_to_l_btn,
            QtCore.SIGNAL("clicked()"),
            lambda: self.mirror_weight_map(
                self.get_selected_deformer(),
                "mirror",
                2,
                [],
                self.mid_edge_line.text(),
                self.mid_edge_optmz_cbox.isChecked(),
            ),
        )

        self.resize(int(600 * self.dpi_scale), int(100 * self.dpi_scale))

    def create_fixed_label(self, caption, width=100):
        label = QtWidgets.QLabel(caption, parent=self)
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred
        )
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        if width is not None:
            width = int(width * self.dpi_scale)
            label.setFixedWidth(width)

        return label

    @staticmethod
    def get_selected_deformer():
        sel = cmds.ls(selection=True, objectsOnly=True)
        for obj in sel:
            if cmds.attributeQuery("weightList", node=obj, exists=True):
                return obj

    @staticmethod
    def list_items_to_texts(items):
        return [item.text() for item in items]

    def middle_edge_button_clicked(self):
        sel = cmds.ls(selection=True, flatten=True)

        if not sel or not len(sel) or ".e[" not in sel[0]:
            raise RuntimeError("select one of the middle edges of the model")

        edge = str(sel[0])

        self.mid_edge_line.setText(edge)

        if self.mid_edge_optmz_cbox.isChecked():
            cmds.select(self.get_component_tokens(edge)[0])
            cmds.edgeFlowMirror(task="compute", middleEdge=edge)

    def middle_edge_button_recompute_clicked(self):
        edge = self.mid_edge_line.text()
        cmds.select(self.get_component_tokens(edge)[0])
        cmds.edgeFlowMirror(task="compute", middleEdge=edge)

    def middle_edge_optimize_toggled(self, is_on):
        edge = self.mid_edge_line.text()

        if is_on and len(edge):
            cmds.select(self.get_component_tokens(edge)[0])
            cmds.edgeFlowMirror(task="compute", middleEdge=edge)

    def select_base_mesh_button_clicked(self):
        sel = cmds.ls(selection=True)
        self.base_mesh_line.setText(sel[0])

    def mirror_skin_cluster(self, in_direction):
        cmds.edgeFlowMirror(
            task="skinCluster",
            direction=in_direction,
            middleEdge=self.mid_edge_line.text(),
            leftJointsPrefix=self.left_joints_prefix_line.text(),
            rightJointsPrefix=self.right_joints_prefix_line.text(),
            optimize=self.mid_edge_optmz_cbox.isChecked(),
        )

    def mirror_mesh(self, in_task, in_direction):
        cmds.edgeFlowMirror(
            task=in_task,
            direction=in_direction,
            middleEdge=self.mid_edge_line.text(),
            baseObject=self.base_mesh_line.text(),
            optimize=self.mid_edge_optmz_cbox.isChecked(),
            baseVertexSpace=self.do_geometry_vertex_space.isChecked(),
        )

    def update_blend_shape_node(self):
        blend_shapes = cmds.ls(selection=True, type="blendShape")
        if not blend_shapes:
            raise RuntimeError("No blendShape nodes selected.")

        for obj in blend_shapes:
            self.blend_shape_line.setText(obj)

            self.target_list.clear()

            attrs = cmds.aliasAttr(obj, query=True)
            attr_count = len(attrs) / 2

            self.target_list.insertItem(0, "_Baseweights")
            for i in range(attr_count):
                self.target_list.insertItem(i + 1, attrs[i * 2])

    def mirror_skin_cluster_blend(self, in_direction):
        sel = cmds.ls(selection=True)
        skin_cluster = mel.eval("findRelatedSkinCluster %s" % sel[0])
        self.mirror_weight_map(
            skin_cluster,
            "mirror",
            in_direction,
            "",
            self.mid_edge_line.text(),
            self.mid_edge_optmz_cbox.isChecked(),
            overwrite_weight_map="blendWeights",
        )

    @staticmethod
    def mirror_weight_map(
        node,
        in_task,
        in_direction,
        blend_shape_targets,
        in_middle_edge,
        do_optimize,
        overwrite_weight_map="",
    ):
        if not in_middle_edge:
            raise RuntimeError("no middle edge selected")

        typ = cmds.objectType(node)
        obj = in_middle_edge.split(".")[0]
        vertex_count = cmds.polyEvaluate(obj, vertex=True)

        old_selection = cmds.ls(selection=True)

        cmds.select(obj)

        if in_task != "mirror":
            map_array = cmds.edgeFlowMirror(
                task="getMapArray",
                middleEdge=in_middle_edge,
                optimize=do_optimize,
            )
        else:
            map_array = cmds.edgeFlowMirror(
                task="getMapSideArray",
                middleEdge=in_middle_edge,
                optimize=do_optimize,
            )

        if not blend_shape_targets:
            blend_shape_targets = [""]

        for target in blend_shape_targets:
            if target == "":
                if len(overwrite_weight_map):
                    attr = "{}.{}[0:{}]".format(
                        node, overwrite_weight_map, vertex_count - 1
                    )
                elif typ == "blendShape":
                    attr = "{}.inputTarget[0].baseWeights[0:{}]".format(
                        node, vertex_count - 1
                    )
                else:
                    attr = "{}.weightList[0].weights[0:{}]".format(
                        node, vertex_count - 1
                    )
            elif target == "_Baseweights":
                attr = "{}.inputTarget[0].baseWeights[0:{}]".format(
                    node, vertex_count - 1
                )
            else:  # we are dealing with blendShape targets
                aliases = cmds.aliasAttr(node, query=True)
                target_index = 0
                for i in range(len(aliases) / 2):
                    if aliases[i * 2] == target:
                        target_index = int(
                            aliases[i * 2 + 1].split("[")[1].split("]")[0]
                        )

                attr = (
                    "{}.inputTarget[0].inputTargetGroup[{}]"
                    ".targetWeights[0:{}]".format(
                        node, target_index, vertex_count - 1
                    )
                )

            origin_weights = cmds.getAttr(attr)

            new_weights = [0] * vertex_count

            if in_task == "flip":
                for i in range(len(new_weights)):
                    new_weights[i] = origin_weights[map_array[i]]
            elif in_task == "mirror":
                if in_direction == 2:
                    for i in range(len(new_weights)):
                        if map_array[vertex_count + i] == 1:
                            new_weights[i] = origin_weights[map_array[i]]
                        else:
                            new_weights[i] = origin_weights[i]
                elif in_direction == 1:
                    for i in range(len(new_weights)):
                        if map_array[vertex_count + i] == 2:
                            new_weights[i] = origin_weights[map_array[i]]
                        else:
                            new_weights[i] = origin_weights[i]

            cmds.setAttr(attr, *new_weights)
            cmds.select(old_selection)

    @staticmethod
    def get_component_tokens(component):
        toks = component.split(".")
        toks1 = toks[1].split("[")
        toks2 = toks1[-1].split("]")
        return toks[0], toks[1], int(toks2[0])

    def select_mirrored_components(self, flip, do_optimize, direction=0):
        sel = cmds.ls(selection=True, flatten=True)

        poly_list_converted = cmds.polyListComponentConversion(
            sel, toVertex=True
        )
        cmds.select(poly_list_converted)

        map_array = cmds.edgeFlowMirror(
            task="getMapSideArray",
            middleEdge=self.mid_edge_line.text(),
            optimize=do_optimize,
        )
        vertex_count = len(map_array) / 2

        cmds.select(sel)

        sel_array = []

        for i in range(len(sel)):
            if ".vtx" in sel[i]:
                component_tokens = self.get_component_tokens(sel[i])
                index = int(component_tokens[2])
                do_this = False

                if flip != 2:
                    do_this = True
                elif map_array[vertex_count + index] == 2 and direction == 1:
                    do_this = True
                elif map_array[vertex_count + index] == 1 and direction == 2:
                    do_this = True

                if do_this:
                    sel_array.append(
                        "{}.vtx[{}]".format(
                            component_tokens[0], map_array[index]
                        )
                    )
                    if flip != 1:
                        sel_array.append(
                            "{}.vtx[{}]".format(component_tokens[0], index)
                        )
                elif flip == 2 and map_array[vertex_count + index] == 0:
                    sel_array.append(
                        "{}.vtx[{}]".format(component_tokens[0], index)
                    )

            else:  # edge or face
                if ".e" in sel[i]:
                    is_edge = True
                elif ".f" in sel[i]:
                    is_edge = False
                else:
                    continue

                verts = cmds.polyListComponentConversion(
                    sel[i],
                    fromEdge=is_edge,
                    fromFace=not is_edge,
                    toVertex=True,
                )
                verts = cmds.ls(verts, flatten=True)

                mirror_verts = []

                for k in range(len(verts)):
                    component_tokens = self.get_component_tokens(verts[k])
                    index = component_tokens[2]
                    if flip == 2:
                        if (
                            map_array[vertex_count + index] == 2
                            and direction == 2
                        ):
                            continue
                        elif (
                            map_array[vertex_count + index] == 1
                            and direction == 1
                        ):
                            continue

                    mirror_verts.append(
                        "{}.vtx[{}]".format(
                            component_tokens[0], map_array[index]
                        )
                    )
                    if flip != 1:
                        mirror_verts.append(
                            "{}.vtx[{}]".format(component_tokens[0], index)
                        )

                objs = cmds.polyListComponentConversion(
                    mirror_verts,
                    fromVertex=True,
                    toEdge=is_edge,
                    toFace=not is_edge,
                    internal=True,
                )
                for obj in objs:
                    sel_array.append(obj)

        cmds.select(sel_array)
