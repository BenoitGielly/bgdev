"""Maya Color Picker

:created: 20/02/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>"""
import pymel.core as pm


class ColorPicker(object):
    def __init__(self, name=None, index=17):
        self._node = name
        self._color = index

        if name:
            self.node = name

        if index and isinstance(index, int):
            self.color = index

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, name):
        if not pm.objExists(name):
            raise NameError("%r doesn't exists!" % name)
        self._node = pm.PyNode(name)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, index):
        self._color = index
        node = self.node
        if not node:
            return

        shapes = node.getShapes()
        if shapes:
            for shape in shapes:
                if shape.hasAttr("overrideEnabled") and shape.hasAttr(
                    "overrideColor"
                ):
                    shape.overrideEnabled.set(True)
                    shape.overrideColor.set(index)
        elif node.hasAttr("overrideEnabled") and node.hasAttr("overrideColor"):
            node.overrideEnabled.set(1)
            node.overrideColor.set(index)
