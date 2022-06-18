"""Easily create custom hotkey.

:created: 11/02/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging

import yaml
from maya import cmds

LOG = logging.getLogger(__name__)


def valid_keyset():
    """Make sure the current hotkey set is valid."""
    if cmds.hotkeySet(query=True, current=True) == "Maya_Default":
        msg = (
            "You are using the default hotkey set. Please, go in the hotkey "
            "editor to create a new one and run this script again"
        )
        LOG.warning(msg)
        return False
    return True


def create_hotkeys_from_yaml(path=None):
    """Quickly re-create custom hotkeys from a yaml file."""
    if not valid_keyset():
        return

    hotkey_file = path or __file__.rsplit(".")[0] + ".yaml"
    with open(hotkey_file, "r") as stream:
        data = yaml.safe_load(stream)

    for name, flags in data.items():
        command = flags.pop("command", None)
        keys = flags.pop("keys", None)
        if (command and keys) or flags.get("remove"):
            create_hotkey(name, command, keys, **flags)
    cmds.savePrefs(hotkeys=True)


def create_hotkey(  # pylint: disable=too-many-arguments
    name,
    command,
    keys,
    edit=False,
    remove=False,
    annotation="New user script",
    category="custom",
    language="python",
):
    """Create a user hotkey with its namedCommand.

    Args:
        name (str): Name of the command to attach to a hotkey
        command (str): The command to run. Must be an executable string.
        keys (str): The hotkey to use. If you want modifiers, add them before
            the keyboard key and separate them with "+". Eg. "alt+shift+A".
        edit (bool): If a command already exists and you want to update it.
        annotation (str): Add an annotation to the command/hotkey
        category (str): The category in which you add the command.
            Default is "Custom Scripts.custom"
        language (str): The source language used by the command.
            Must be either "mel" or "python"

    """
    key = keys.rsplit("+")[-1]
    mods = keys.rsplit("+")[:-1] or []
    mods_flags = {}
    for each in mods:
        if each.lower() in ["alt", "ctrl", "shift"]:
            mods_flags[each.lower() + "Modifier"] = True

    cmd_exists = cmds.runTimeCommand(name, query=True, exists=True)
    if cmd_exists and remove:
        cmds.hotkey(keyShortcut=key, name="", **mods_flags)
        return

    if cmd_exists and not edit:
        msg = (
            "{0!r} command already exists, "
            "please use a different name or "
            'add the "edit=True" flag'
        ).format(name)
        LOG.warning(msg)
        return

    flags = dict(edit=edit) if cmd_exists else {}
    cmds.runTimeCommand(
        name,
        annotation=annotation,
        category="Custom Scripts." + category,
        commandLanguage=language,
        command=command,
        **flags
    )
    cmds.nameCommand(
        name + "_userCommand", annotation=annotation, command=name
    )

    if not valid_keyset():
        return

    cmds.hotkey(keyShortcut=key, name=name + "_userCommand", **mods_flags)
