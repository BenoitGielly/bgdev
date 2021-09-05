"""Renamer tool for maya.

:created: 06/04/2016
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging

from maya import cmds

from .ui import RenamerUi
from .utils import UNDO

LOG = logging.getLogger(__name__)


def show(parent=None):
    """Show widget."""
    cls = Renamer(parent)
    cls.show()
    return cls


class Renamer(RenamerUi):
    """Core renamer class."""

    def __init__(self, parent=None):
        super(Renamer, self).__init__(parent=parent)
        self.conflict_detected = False
        self.setFocus()

    @staticmethod
    def get_uuid(node):
        """Get the given node's uuid."""
        return str(cmds.ls(node, uuid=True)[0])

    @staticmethod
    def get_node(uuid):
        """Get the node name from given uuid."""
        return cmds.ls(uuid)[0]

    def get_selection(self, as_name=False):
        """Get selection."""
        selection = cmds.ls(selection=True)
        if not selection:
            raise RuntimeError("Please, select something!")
        uuids = [self.get_uuid(x) for x in selection]
        return selection if as_name else uuids

    def check_conflict(self, name):
        """Check name conflicts."""
        if cmds.ls(name):
            if not self.conflict_detected:
                LOG.warning("Careful, name conflict detected: %s", name)
            self.conflict_detected = True

    @UNDO
    def hash_rename(self, text=None, start=None, letters=None):
        # pylint: disable=too-many-locals
        """Rename given text by replacing ###.

        Args:
            text (str): Text to rename. Must contains at least one "#".
            start (int): Value to start when replacing "#" with numbers
            letters (bool): Using letter instead of numbers when True.

        """
        # gather informations from UI (or from kwargs)
        text = text or self.hash_text.text()
        start = start or self.hash_spinbox.value()
        letters = letters or self.hash_letters_radio.isChecked()
        pad = text.count("#")

        # get selection and size
        uuids = self.get_selection()
        size = len(uuids)

        # set conflict var and cleanup script edit
        self.conflict_detected = False

        # return if not text or selection
        if not text:
            LOG.warning("Please, type something in textField")
            return
        elif not pad:
            LOG.warning("Couldn't find any '#'...")
            return

        # cleanup new name
        if " " in text:
            text = text.replace(" ", "_")

        # check the padding
        selection_pad = len(str(size + start - 1))
        padding = pad
        if selection_pad > pad:
            padding = selection_pad

        # replace hashes and format name
        if letters:
            alpha = start / 27
            new_name = text.replace("#" * pad, "{0}")
        else:
            new_name = text.replace("#" * pad, "{0:0%dd}" % padding)

        # temp rename to avoid bad names
        orig_name_dict = {}
        for i, uuid in enumerate(uuids):
            node = self.get_node(uuid)
            orig_name_dict[i] = node
            cmds.rename(node, "HASH_rename_%02d_TMP" % i)

        # rename each elements
        for i, uuid in enumerate(uuids):
            name = i + start
            if letters:
                # check padding
                if size + start > 27:
                    letter_a = [chr(65 + j) for j in range(26)][alpha]
                    letter_b = [chr(65 + j) for j in range(26)][name % 26 - 1]
                    if name % 26 == 0 and i > 0:
                        alpha += 1
                    nice_name = new_name.format(letter_a + letter_b)
                else:
                    nice_name = new_name.format(chr(64 + name))
            else:
                nice_name = new_name.format(name)

            # rename command
            self.check_conflict(nice_name)
            cmds.rename(self.get_node(uuid), nice_name)

    @UNDO
    def search_replace(self, search=None, replace=None, hierarchy=None):
        """Replace the 'search' text with the 'replace' text.

        Args:
            search (str): String to search within text.
            replace (str): String used to replaced if match is found.
            hierarchy (bool): Rename every nodes below if True.

        """
        search = search or self.search_text.text()
        replace = replace or self.replace_text.text()
        hierarchy = hierarchy or self.hierarchy_radio.isChecked()

        # get selection and size
        uuids = self.get_selection()

        # check hierarchy
        if hierarchy:
            nodes = [self.get_node(x) for x in uuids]
            nodes = cmds.ls(nodes, dagObjects=True)
            uuids = [self.get_uuid(x) for x in nodes]

        # set conflict var
        self.conflict_detected = False

        # return if not text or selection
        if not search:
            LOG.warning("Please, type something in the 'Search' field")
            return

        # rename each elements
        for uuid in uuids:
            node = self.get_node(uuid)
            base_name = node.rsplit("|")[-1]
            new_name = base_name.replace(search, replace)
            if new_name != base_name:
                self.check_conflict(new_name)
                cmds.rename(node, new_name)

    @UNDO
    def prefix_suffix(self, prefix=None, suffix=None, mode=None):
        """Add, remove, or replace prefixes and/or suffixes.

        Args:
            prefix (bool): True if you want to update the prefix.
            suffix (bool): True if you want to update the suffix.
            mode (str): The mode to use.
                Must be "add", "replace", or "remove"

        """
        _prefix = None
        if prefix is True and mode in ["add", "replace"]:
            _prefix = self.prefix_text.text()
        elif prefix is not None:
            _prefix = prefix

        _suffix = None
        if suffix is True and mode in ["add", "replace"]:
            _suffix = self.suffix_text.text()
        elif suffix is not None:
            _suffix = suffix

        # get selection and size
        uuids = self.get_selection()

        # set conflict var
        self.conflict_detected = False

        # rename each elements
        for uuid in uuids:
            node = self.get_node(uuid)
            base_name = node.rsplit("|")[-1]
            split_name = base_name.rsplit("_")
            if _prefix:
                if mode == "add":
                    new_name = _prefix + "_" + base_name
                elif mode == "remove":
                    split_name.pop(0)
                    new_name = "_".join(split_name)
                elif mode == "replace":
                    split_name.pop(0)
                    new_name = "_".join([_prefix] + split_name)
            elif _suffix:
                if mode == "add":
                    new_name = base_name + "_" + _suffix
                elif mode == "remove":
                    split_name.pop(-1)
                    new_name = "_".join(split_name)
                elif mode == "replace":
                    split_name.pop(-1)
                    new_name = "_".join(split_name + [_suffix])
            else:
                if _prefix is None:
                    LOG.warning("Please, type something in the 'Suffix' field")
                elif _suffix is None:
                    LOG.warning("Please, type something in the 'Prefix' field")
                LOG.warning(
                    "Please, type something in the 'Prefix' or 'Suffix' field"
                )
                return
            cmds.rename(node, new_name)
        return
