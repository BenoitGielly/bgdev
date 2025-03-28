# pylint: disable=missing-docstring, maya-short-flag, invalid-name, unused-argument
"""Symmetry stuff.

:created: 14/01/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial

from maya import cmds
from qtpy import QtWidgets


class PlaneVector(QtWidgets.QDialog):
    """Quickly place items in a 3-points plane."""

    def __init__(self):
        super(PlaneVector, self).__init__()
        self.fields = []
        self.setup_ui()
        self.objects_radio.setChecked(True)

    def setup_ui(self):
        """Create the UI widgets."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(2)

        # create option layout
        option_layout = QtWidgets.QHBoxLayout()
        option_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.setSpacing(2)

        self.points_radio = QtWidgets.QRadioButton("Points", self)
        self.points_radio.setChecked(True)
        self.objects_radio = QtWidgets.QRadioButton("Nodes", self)
        self.set_button = QtWidgets.QPushButton("SET", self)

        option_layout.addWidget(self.points_radio)
        option_layout.addWidget(self.objects_radio)
        option_layout.addStretch()
        option_layout.addWidget(self.set_button)

        main_layout.addLayout(option_layout)

        # create points layouts
        for _ in range(1, 4):
            line_layout = QtWidgets.QHBoxLayout()
            line_layout.setContentsMargins(0, 0, 0, 0)
            line_layout.setSpacing(2)

            for i in range(3):
                line_field = QtWidgets.QLineEdit(self)
                line_field.setEnabled(False)
                line_field.setText("0.0000")
                line_layout.addWidget(line_field)
                if i > 0:
                    self.objects_radio.toggled.connect(line_field.setHidden)
                self.fields.append(line_field)
            main_layout.addLayout(line_layout)

        # create scale layout
        scale_layout = QtWidgets.QHBoxLayout()
        scale_layout.setContentsMargins(0, 0, 0, 0)
        scale_layout.setSpacing(2)

        scale_field = QtWidgets.QLineEdit(self)
        scale_field.setText("1.0000")
        scale_button = QtWidgets.QPushButton("Scale", self)

        scale_layout.addWidget(scale_field)
        scale_layout.addWidget(scale_button)
        scale_layout.setStretch(0, 1)
        scale_layout.setStretch(1, 1)
        main_layout.addLayout(scale_layout)

        # create buttons layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)

        zero_button = QtWidgets.QPushButton("0", self)
        mirror_button = QtWidgets.QPushButton("-1", self)

        button_layout.addWidget(zero_button)
        button_layout.addWidget(mirror_button)
        main_layout.addLayout(button_layout)

        main_layout.addStretch()
        self.resize(0, 0)


def mirror_layout():  # pylint: disable=too-many-locals
    import pymel.core as pm

    window = pm.window(title="Vector Plane Tool")
    c = pm.columnLayout(adj=1, p=window)
    b = pm.button(p=c, label="Set")
    h1 = pm.horizontalLayout(p=c, spacing=1)
    f1 = cmds.floatField(v=0, en=False)
    f2 = cmds.floatField(v=0, en=False)
    f3 = cmds.floatField(v=0, en=False)
    h1.redistribute()
    h2 = pm.horizontalLayout(p=c, spacing=1)
    f4 = cmds.floatField(v=0, en=False)
    f5 = cmds.floatField(v=0, en=False)
    f6 = cmds.floatField(v=0, en=False)
    h2.redistribute()
    h3 = pm.horizontalLayout(p=c, spacing=1)
    f7 = cmds.floatField(v=0, en=False)
    f8 = cmds.floatField(v=0, en=False)
    f9 = cmds.floatField(v=0, en=False)
    h3.redistribute()
    fieldsA = [f1, f2, f3]
    fieldsB = [f4, f5, f6]
    fieldsC = [f7, f8, f9]
    fields = [fieldsA, fieldsB, fieldsC]
    b.setCommand(partial(setMirrorToolCMD, fields=fields))
    h = pm.horizontalLayout(p=c, spacing=1)
    fl = cmds.floatField(v=1.0, ed=True)
    cmds.button(label="Scale", c=partial(mirrorToolCMD, fields=fields, fl=fl))
    h.redistribute()
    h = pm.horizontalLayout(p=c, spacing=1)
    cmds.button(label="0", c=partial(mirrorToolCMD, fields=fields, scale=0))
    cmds.button(label="-1", c=partial(mirrorToolCMD, fields=fields, scale=-1))
    h.redistribute()
    window.show()


def mirrorToolCMD(*args, **kwargs):
    fields = kwargs.get("fields", [])
    fl = kwargs.get("fl")
    scale = kwargs.get("scale", 1.0)
    valTupList = []
    for fg in fields:
        if cmds.floatField(fg[0], q=True, en=True):
            v1 = cmds.floatField(fg[0], q=True, v=1)
            v2 = cmds.floatField(fg[1], q=True, v=1)
            v3 = cmds.floatField(fg[2], q=True, v=1)
            valTupList.append((v1, v2, v3))
    if fl:
        scale = cmds.floatField(fl, q=True, v=True)
    objList = cmds.ls(sl=True, fl=True)
    for obj in objList:
        posTup = get_mirrorvector(obj, mirror=valTupList, scl=scale)
        cmds.xform(obj, ws=True, a=True, t=posTup)


def vector(*args):
    import pymel.core as pm

    vec = None
    argLen = len(args)
    if argLen == 0:
        vec = pm.datatypes.Vector(0)
    elif argLen == 1:
        if isinstance(args[0], pm.datatypes.Vector):
            vec = args[0]
        elif isinstance(
            args[0], (basestring, pm.general.Component, pm.nodetypes.Transform)
        ):
            vec = pm.datatypes.Vector(
                pm.xform(args[0], a=1, ws=True, q=1, t=1)
            )
        elif isinstance(args[0], (list, tuple)):
            vec = pm.datatypes.Vector(args[0])
    elif argLen == 2:
        if isinstance(args[0], pm.datatypes.Vector):
            vec = args[1] - args[0]
        elif isinstance(
            args[0], (basestring, pm.general.Component, pm.nodetypes.Transform)
        ):
            a = pm.datatypes.Vector(pm.xform(args[0], a=1, ws=True, q=1, t=1))
            b = pm.datatypes.Vector(pm.xform(args[1], a=1, ws=True, q=1, t=1))
            vec = b - a
        elif isinstance(args[0], (list, tuple)):
            a = pm.datatypes.Vector(args[0])
            b = pm.datatypes.Vector(args[1])
            vec = b - a
    elif argLen > 2 and isinstance(args[0], (int, float)):
        vec = pm.datatypes.Vector(args[:3])
    return vec


def get_mirrorvector(obj, **kwargs):
    import pymel.core as pm

    mirList = kwargs.get("mirror", None)
    if isinstance(mirList[0], (list, tuple)):
        mVecList = map(vector, mirList)
    elif isinstance(mirList[0], pm.datatypes.Vector):
        mVecList = mirList
    else:
        return None
    scl = kwargs.get("scl", -1.0)
    pVec = vector(obj)
    if len(mVecList) == 1:
        xVec = pVec - mVecList[0]
    elif len(mVecList) == 2:
        aVec = mVecList[0] - mVecList[1]
        bVec = mVecList[0] - pVec
        nVec = aVec ^ (aVec ^ bVec)
        eVec = pVec - mVecList[1]
        nMag = nVec.length()
        if nMag > 0:
            xVec = nVec * ((eVec * nVec) / nMag**2.0)
        else:
            xVec = pm.datatypes.Vector(0)
    elif len(mVecList) == 3:
        aVec = mVecList[0] - mVecList[1]
        bVec = mVecList[0] - mVecList[2]
        nVec = aVec ^ bVec
        eVec = pVec - mVecList[0]
        nMag = nVec.length()
        xVec = nVec * ((eVec * nVec) / nMag**2.0)
    vec = (pVec - xVec) + (xVec * scl)
    return vec


def setMirrorToolCMD(callback, fields=None):
    selList = cmds.ls(sl=True, fl=True, hd=3)
    for fg in fields:
        for f in fg:
            cmds.floatField(f, e=True, v=0.0, en=False, pre=9)
    for sel, fg in zip(selList, fields):
        pos = cmds.xform(sel, ws=True, a=True, q=True, t=True)
        cmds.floatField(fg[0], e=True, v=pos[0], en=True)
        cmds.floatField(fg[1], e=True, v=pos[1], en=True)
        cmds.floatField(fg[2], e=True, v=pos[2], en=True)
