"""ProgressBar class to use in Maya.

ToDo:
    Convert to PySide and move to :mod:`bgdev.ui.widget`

:created: 23/05/2018
:author: Benoit Gielly <benoit.gielly@gmail.com>

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from maya import cmds
from maya import mel
from qtpy import QtCore
from qtpy import QtWidgets

from . import utils


class ProgressBar2(object):
    """ProgressBar class."""

    def __init__(self):
        """Constructor."""
        parent = utils.main_window()
        self.progress_bar = QtWidgets.QProgressDialog(parent=parent)
        self.progress_bar.close()

    @property
    def status(self):
        """str: Update the status of the progressBar."""
        return self.progress_bar.labelText()

    @status.setter
    def status(self, text):
        self.progress_bar.setLabelText(text)

    def start(self, status="Begin operation...", maximum=100):
        """Start the process."""
        self.progress_bar.reset()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setLabelText(status)
        self.progress_bar.show()
        self.progress_bar.setWindowModality(QtCore.Qt.WindowModal)

    def step(self):
        """Increase progress step by one."""
        QtCore.QCoreApplication.processEvents()
        if self.progress_bar.wasCanceled():
            raise RuntimeError("Operation cancelled by user")
        value = self.progress_bar.value() + 1
        if value <= self.progress_bar.maximum():
            self.progress_bar.setValue(value)

    def end(self):
        """Finish the process."""
        self.progress_bar.close()


class ProgressBar(object):
    """ProgressBar class."""

    def __init__(self):
        """Constructor."""
        self.progress_bar = self._create()
        self._status = ""

    @staticmethod
    def _create():
        """Create the progressBar widget."""
        try:
            progress_bar = mel.eval("$tmp = $gMainProgressBar")
            if not cmds.control(progress_bar, exists=True):
                progress_bar = None
        except RuntimeError:
            progress_bar = None

        return progress_bar

    @property
    def status(self):
        """str: Update the status of the progressBar."""
        return self._status

    @status.setter
    def status(self, status):
        self._status = status
        if self.progress_bar:
            cmds.progressBar(self.progress_bar, edit=True, status=self._status)

    def start(self, status="Begin operation...", value=100):
        """Start the process."""
        if self.progress_bar:
            self.status = status
            cmds.progressBar(
                self.progress_bar,
                edit=True,
                beginProgress=True,
                isInterruptable=True,
                status=self.status,
                maxValue=value,
            )

    def step(self, step=1):
        """Increase progress step by one."""
        if self.progress_bar:
            self.is_cancelled()
            cmds.progressBar(self.progress_bar, edit=True, step=step)

    def is_cancelled(self):
        """Check if progress was cancelled (esc. key pressed)."""
        if self.progress_bar:
            is_cancelled = cmds.progressBar(
                self.progress_bar,
                query=True,
                isCancelled=True,
            )
            if is_cancelled:
                raise RuntimeError("Operation cancelled by user")

    def end(self):
        """Finish the process."""
        if self.progress_bar:
            cmds.progressBar(self.progress_bar, edit=True, endProgress=True)
