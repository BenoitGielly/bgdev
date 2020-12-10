"""Utility methods used to sort nodes and graphs.

:created: 20/11/2020
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

from maya import cmds, mel
from maya.api import OpenMaya

LOG = logging.getLogger(__name__)


class Symmetry(object):
    """Generates a symmetry table for selected mesh."""

    def __init__(self):
        self.table = {}
        self.edge = None
        self.mesh = None
        self.update()

    @property
    def center(self):
        """Get center vertices."""
        return self.get_side_vertices("center")

    @property
    def left(self):
        """Get left side vertices."""
        return self.get_side_vertices("left")

    @property
    def right(self):
        """Get right side vertices."""
        return self.get_side_vertices("right")

    @staticmethod
    def get_vertex_id(vertex):
        """Get vertex index from name.

        Args:
            vertex (str): Full vertex name (eg. "mesh.vtx[15]")

        Return:
            int: Index of the vertex as integer.
        """
        return int(vertex.rsplit("[")[-1].rsplit("]")[0])

    def get_vertex_name(self, index):
        """Get vertex name from index.

        Args:
            index (int): Index of the vertex.

        Return:
            str: Full vertex name (eg. "mesh.vtx[15]")
        """
        return "{}.vtx[{}]".format(self.mesh, index)

    def get_side_vertices(self, side):
        """Get all components of given side.

        Args:
            side (str): Side of the table to query.
                Either "left", "center" or "right".

        Returns:
            list: List of side-vertices.
        """
        return [self.get_vertex_name(i) for i in self.table.get(side)]

    def mirror_selection(self, add=False):
        """Mirror selected vertices.

        Args:
            add (bool): Add to existing selection when True.
        """
        selection = cmds.ls(selection=True, flatten=True)
        vertices = self.mirror(selection)
        cmds.select(vertices, add=add)

    def mirror(self, vertices):
        """Mirror vertices.

        Args:
            vertices (list): List of vertices to mirror.

        Yields:
            str: The next vertex full name in the given list.
        """
        for each in vertices:
            index = self.get_vertex_id(each)
            yield self.get_vertex_name(self.table[index])

    def update(self):
        """Generate a symmetry table."""
        # get selected edge, mesh name and all vertices
        self.edge = (cmds.ls(selection=True) or [None])[0]
        self.mesh = self.edge.rpartition(".")[0]

        # populate the table using maya topology symmetry (ergh...)
        try:
            cmds.symmetricModelling(self.edge, topoSymmetry=True)
            self.populate_table()
        except Exception:
            raise
        else:
            mel.eval("reflectionSetMode none;")

    def populate_table(self):
        """Populate the symmetry table with vertices.

        Notes:
            Maya topology symmetry must be activated.
        """
        self.table.clear()

        cmds.select(self.mesh + ".vtx[*]", symmetry=True)
        rich_selection = OpenMaya.MGlobal.getRichSelection()
        cmds.select(clear=True)

        clean_list = rich_selection.getSymmetry()
        clean_sel_iter = OpenMaya.MItSelectionList(clean_list)
        while not clean_sel_iter.isDone():
            clean_dag, clean_obj = clean_sel_iter.getComponent()
            clean_vtx_iter = OpenMaya.MItMeshVertex(clean_dag, clean_obj)
            while not clean_vtx_iter.isDone():
                clean_index = int(clean_vtx_iter.index())
                clean_vtx = "%s.vtx[%s]" % (self.mesh, clean_index)

                # TODO: Figure something to speed this up...
                cmds.select(clean_vtx, symmetry=True)

                sym_rich_sel = OpenMaya.MGlobal.getRichSelection()
                sym_list = sym_rich_sel.getSelection()
                sym_sel_iter = OpenMaya.MItSelectionList(sym_list)
                sym_dag, sym_obj = sym_sel_iter.getComponent()
                sym_vtx_iter = OpenMaya.MItMeshVertex(sym_dag, sym_obj)
                sym_index = int(sym_vtx_iter.index())
                self.table[clean_index] = sym_index
                self.table.setdefault("left", set()).add(clean_index)
                self.table[sym_index] = clean_index
                self.table.setdefault("right", set()).add(sym_index)
                clean_vtx_iter.next()
            clean_sel_iter.next()

        # add center vertices
        clean_sel_iter = OpenMaya.MItSelectionList(clean_list)
        mesh_dag, _ = clean_sel_iter.getComponent()
        points = OpenMaya.MFnMesh(mesh_dag).getPoints()
        for i in range(len(points)):
            if i not in self.table.keys() + self.table.values():
                self.table[i] = i
                self.table.setdefault("center", set()).add(i)

    @staticmethod
    def get_sides_from_rich(vertices):
        """Get resulting sides of a RichSelection in symmetry.

        Args:
            vertices (list): Vertices to select for symmetry.

        Returns:
            tuple: Two `OpenMaya.MSelectionList`, being the result of the
                MRichSelection.getSelection and MRichSelection.getSymmetry
                methods.
        """
        cmds.select(vertices, symmetry=True)
        rich_selection = OpenMaya.MGlobal.getRichSelection()
        selection = rich_selection.getSelection()
        symmetry = rich_selection.getSymmetry()
        cmds.select(clear=True)

        return selection, symmetry
