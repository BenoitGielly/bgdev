"""Utility methods used to sort nodes and graphs.

:created: 20/11/2020
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

from maya import cmds, mel

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
        """Get vertex index from name."""
        return int(vertex.rsplit("[")[-1].rsplit("]")[0])

    def get_vertex_name(self, index):
        """Get vertex name from index."""
        return "{}.vtx[{}]".format(self.mesh, index)

    def get_side_vertices(self, side):
        """Get all components of given side."""
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
            Maya topology symmetry must be already activated.
        """
        self.table.clear()

        vertices = cmds.ls(self.mesh + ".vtx[*]", flatten=True)
        for i, vtx in enumerate(vertices):
            if i in self.table:
                continue

            # select and find symmetrical vertices
            cmds.select(vtx, symmetry=True)
            selected = cmds.ls(selection=True, flatten=True)

            # if selection length is one, its a center vertex
            if len(selected) == 1:
                self.table[i] = i
                self.table.setdefault("center", []).append(i)
                continue

            # find opposite vertex index and add them to table
            opposite = [x for x in selected if x != vtx][0]
            j = self.get_vertex_id(opposite)
            self.table[i], self.table[j] = j, i

            # find which are left and right
            xpos = cmds.xform(
                selected,
                query=True,
                translation=True,
                worldSpace=True,
            )[0::3]
            min_id = xpos.index(min(xpos))
            left = i if vtx != selected[min_id] else j
            self.table.setdefault("left", []).append(left)
            right = i if vtx == selected[min_id] else j
            self.table.setdefault("right", []).append(right)
