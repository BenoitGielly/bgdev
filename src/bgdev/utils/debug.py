"""Utility functions for debugging.

Example:
    trace_this(crashing_function, "/user_data/maya_crash_report.txt")

"""
from __future__ import absolute_import

import sys
import trace


def trace_this(func, filepath):
    """Trace function."""
    oldout = sys.stdout
    olderr = sys.stderr
    try:
        with open(filepath, "w") as stream:
            sys.stdout = stream
            sys.stderr = stream
            tracer = trace.Trace(count=False, trace=True)
            tracer.runfunc(func)

    finally:
        sys.stdout = oldout
        sys.stderr = olderr


def crashing_function():
    """Function that forces Maya to crash."""
    from maya.api import OpenMaya

    dagnode = OpenMaya.MFnDagNode()
    node = dagnode.create("transform")
    OpenMaya.MGlobal.deleteNode(node)

    # Do not run this. Yes, it actually crashes Maya
    dagnode.findPlug("translateX", True)
