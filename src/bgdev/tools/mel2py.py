"""Convert mel to python.

:created: 23/01/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import print_function

import pymel.tools.mel2py


def convert_command(command, namespace="cmds", verbose=True):
    """Convert mel command-string to python.

    Args:
        command (str): The mel command as a string.
        namespace (str): The namespace to use for the module.
        verbose (bool): Prints the command after conversion.

    Returns:
        str: The convert mel command to python.
    """
    cmd = pymel.tools.mel2py.mel2pyStr(command, pymelNamespace=namespace)
    if verbose:
        print(cmd)  # noqa

    return cmd


def convert_file(files, force_compatibility=True):
    """Convert mel files to python.

    Args:
        files (list): List of path to mel files.
        force_compatibility (bool): Pymel argument. Don't really know if it has
            an impact or not so adding it as a kwarg just in case.

    """
    for each in files:
        with open(each, "r") as stream:
            content = stream.read()
        py_cmd = pymel.tools.mel2py.mel2pyStr(
            content,
            pymelNamespace="cmds",
            forceCompatibility=force_compatibility,
        )
        py_path = each.replace(".mel", ".py")
        with open(py_path, "w") as stream:
            stream.write(py_cmd)
