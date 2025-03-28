"""Custom FlowLayout.

:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from qtpy import QtCore
from qtpy import QtWidgets


class FlowLayout(QtWidgets.QLayout):
    """Custom resizable widget."""

    def __init__(self, parent=None):
        super(FlowLayout, self).__init__(parent)
        self.__items = []

    def itemAt(self, index):
        """Return the item at the given index."""
        try:
            return self.__items[index]
        except IndexError:
            return None

    def takeAt(self, index):
        """Remove and return the item at the given index."""
        try:
            return self.__items.pop(index)
        except IndexError:
            return None

    def count(self):
        """Return the number of item in the layout."""
        return len(self.__items)

    def addItem(self, item):
        """Add an item to the layout."""
        self.__items.append(item)

    def minimumSize(self):
        """Find the minimum size of the layout."""
        size = QtCore.QSize(0, 0)
        for item in self.__items:
            size = size.expandedTo(item.minimumSize())
        size += QtCore.QSize(
            self.contentsMargins().left() + self.contentsMargins().right(),
            self.contentsMargins().top() + self.contentsMargins().bottom(),
        )
        return size

    def sizeHint(self):
        """The prefered size of the layout."""
        return self.minimumSize()

    def hasHeightForWidth(self):
        """Tell Qt that the height of the layout is depending of its width."""
        return True

    def heightForWidth(self, width):
        """Calculare the hieght needed base on the layout width."""
        return self.__do_layout(QtCore.QRect(0, 0, width, 0), move=False)

    def setGeometry(self, rect):
        """Place all the item in the space allocated to the layout."""
        self.__do_layout(rect, move=True)

    def __do_layout(self, rect, move=False):
        current_x = self.contentsMargins().left()
        current_y = self.contentsMargins().top()
        next_x = current_x
        next_y = current_y
        for item in self.__items:
            next_x = current_x + item.sizeHint().width() + self.spacing()
            if next_x + self.contentsMargins().right() >= rect.width():
                current_x = self.contentsMargins().left()
                current_y = next_y + self.spacing()
                next_x = current_x + item.sizeHint().width() + self.spacing()
            if move:
                point = QtCore.QPoint(current_x, current_y)
                item.setGeometry(QtCore.QRect(point, item.sizeHint()))
            current_x = next_x
            next_y = max(next_y, current_y + item.sizeHint().height())
        return next_y + self.contentsMargins().bottom()


# Not working with M22+
# or it does, but it triggers a popup of Maya.exe after closing which is
# not possible to kill unless through task manager
class FlowLayout2(QtWidgets.QLayout):
    # pylint: disable=invalid-name, missing-docstring, no-self-use

    def __init__(self, parent=None, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        self.setSpacing(spacing)
        self.itemList = []
        self._offset = 0
        self._line_offset = 0

    def set_style_offsets(self, offset, line):
        self._offset = offset
        self._line_offset = line

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height + self._offset + self.getContentsMargins()[-1]

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QtCore.QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )
        return size

    def doLayout(self, rect, testOnly):
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect.adjusted(left, top + 1, -right, -bottom)
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0
        for item in self.itemList:
            widget = item.widget()
            spaceX = self.spacing() + widget.style().layoutSpacing(
                QtWidgets.QSizePolicy.PushButton,
                QtWidgets.QSizePolicy.PushButton,
                QtCore.Qt.Horizontal,
            )
            spaceY = self.spacing() + widget.style().layoutSpacing(
                QtWidgets.QSizePolicy.PushButton,
                QtWidgets.QSizePolicy.PushButton,
                QtCore.Qt.Vertical,
            )
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effectiveRect.right() and lineHeight > 0:
                x = effectiveRect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(
                    QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint())
                )
            x = nextX - self._offset
            lineHeight = (
                max(lineHeight, item.sizeHint().height()) - self._line_offset
            )

        return y + lineHeight - rect.y()
