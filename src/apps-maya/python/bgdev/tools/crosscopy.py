"""Create a crosscopy tool to transfer data from DCC to another.

:author: Benoit Gielly <benoit.gielly@gmail.com>
:created: 25/01/2021
"""
import abc
import logging
import os
import pkgutil
import tempfile

from PySide2 import QtWidgets
import six

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BaseCrossCopy(object):
    """Base class for the crosscopy tool."""

    def __init__(self):  # noqa: D107
        self.local = True
        self.local_path = self.get_local_path()

    @staticmethod
    def get_local_path():
        """Get a local path to the temp folder (multi-platform)."""
        path = os.path.join(tempfile.gettempdir(), "crosscopy")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @abc.abstractmethod
    def get_path(self):
        """Generate a file name for the current DDC."""
        pass

    @abc.abstractmethod
    def copy(self):
        """Implement the copy method in the current DCC."""
        pass

    @abc.abstractmethod
    def paste(self):
        """Implement the paste method in the current DCC."""
        pass


class MayaCrossCopy(BaseCrossCopy):
    """Maya implementation of CrossCopy."""

    def get_path(self):
        """Generate Maya specific filepath name."""
        name = "mayaCrossCopy{}.ma".format("_local" if self.local else "")
        return os.path.join(self.get_local_path(), name)

    def copy(self):
        """Copy selection to system."""
        from maya import cmds

        selection = cmds.ls(selection=True)
        if not selection:
            LOG.warning(">>> xCopy: Please, select something first!")
            return

        filepath = self.get_path()
        cmds.file(
            filepath,
            force=True,
            options="v=0",
            type="mayaAscii",
            preserveReferences=True,
            exportSelected=True,
        )
        LOG.info(">>> xCopy: selection successfully exported in %r", filepath)

    def paste(self):
        """Import file from system."""
        from maya import cmds

        filepath = self.get_path()
        if not os.path.exists(filepath):
            LOG.warning(">>> xPaste: No file found to paste!")
            return

        # import from file and ignore version...
        cmds.file(
            filepath,
            i=True,
            force=True,
            options="v=0",
            type="mayaAscii",
            defaultNamespace=True,
            preserveReferences=True,
            ignoreVersion=True,
        )
        LOG.info(">>> xPaste: scene successfully imported from %r", filepath)


class HoudiniCrossCopy(BaseCrossCopy):
    """Houdini implementation of CrossCopy."""

    def get_path(self):
        pass

    def copy(self):
        pass

    def paste(self):
        pass


class NukeCrossCopy(BaseCrossCopy):
    """Nuke implementation of CrossCopy."""

    def get_path(self):
        pass

    def copy(self):
        pass

    def paste(self):
        pass


class SystemCrossCopy(BaseCrossCopy):
    """Default implementation of CrossCopy."""

    def get_path(self):
        pass

    def copy(self):
        pass

    def paste(self):
        pass


def get_crosscopy_api():
    """Get current DCC's cross copy API."""
    api = SystemCrossCopy
    if pkgutil.find_loader("maya"):  # DCC = Maya
        api = MayaCrossCopy
    if pkgutil.find_loader("hou"):  # DCC = Houdini
        api = HoudiniCrossCopy
    if pkgutil.find_loader("nuke"):  # DCC = Nuke
        api = NukeCrossCopy

    return api()


class CrossCopyUI(QtWidgets.QWidget):
    """User interface for crosscopy."""

    def __init__(self, *args, **kwargs):  # noqa: D107
        super(CrossCopyUI, self).__init__(*args, **kwargs)
        self.setup_ui()
        self.api = get_crosscopy_api()

    def setup_ui(self):
        """Create widgets."""
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        copy_btn = QtWidgets.QPushButton("xCopy", self)
        copy_btn.clicked.connect(self.run_copy)
        main_layout.addWidget(copy_btn)

        paste_btn = QtWidgets.QPushButton("xPaste", self)
        paste_btn.clicked.connect(self.run_paste)
        main_layout.addWidget(paste_btn)

    def run_copy(self):
        """Execute API's copy method."""
        self.api.copy()

    def run_paste(self):
        """Execute API's paste method."""
        self.api.paste()
