"""Evaluation Toolkit.

:created: 03/06/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cProfile
import datetime
import logging
import os
import pstats
import time
from contextlib import ContextDecorator

LOG = logging.getLogger(__name__)


def frames_per_second(
    iterations=3,
    start=1001,
    frames=100,
    viewports=("viewport2"),
    meshes_only=True,
    outfile=None,
    force_gpu=True,
):
    """Evaluate the framePerSecond in the current scene.

    Args:
        iterations (int): Amount of time the timeline should run.
        start (int): Start frame.
        frames (int): The amount of frames to run.
        viewports (list): Select the viewports you want to evaluate on.
            Possible values are "legacy" and "viewport2".
        meshes_only (bool): Hides everything but meshes in the viewport.
        outfile (bool or str): Save the output fps in the given txt file.
            If `True` is passed, query the current scene path and save the log
            next to it (Useful when benchmarking multiple scenes in a loop).
        force_gpu (bool): Force enabling the GPU override.

    Returns:
        float: The evaluated frame per seconds as a float number.

    """
    # pylint: disable=import-outside-toplevel
    from maya import cmds
    from maya import mel
    from maya.debug import emPerformanceTest  # type: ignore

    # override Maya's emPerformanceTest method to work with custom viewports
    def switch_maya_viewport(new_mode):
        """Override Maya's method."""
        if new_mode == "legacy":
            mel.eval(
                'setRendererInModelPanel "base_OpenGL_Renderer" modelPanel4'
            )
        elif new_mode == "viewport2":
            mel.eval('setRendererInModelPanel "vp2Renderer" modelPanel4')
        else:
            raise NameError(
                "Selected viewport {!r} not found!".format(new_mode)
            )

    emPerformanceTest.switchMayaViewport = switch_maya_viewport

    # start the FPS evaluation tool
    if not isinstance(viewports, list):
        viewports = [viewports]

    # set the frame range
    if frames <= 10:
        LOG.warning(
            "End frame must be higher than start frame. Using 10 as a minimum."
        )
        frames = 10

    end = start + frames
    cmds.playbackOptions(
        edit=True,
        animationStartTime=start,
        minTime=start,
        animationEndTime=end,
        maxTime=end,
    )
    cmds.currentTime(start)

    # enable GPU acceleration
    if force_gpu:
        mel.eval("turnOnOpenCLEvaluatorActive();")

    # disable color management
    color_management = cmds.colorManagementPrefs(query=True, cmEnabled=True)
    cmds.colorManagementPrefs(edit=True, cmEnabled=False)

    # hide all nodes but meshes in viewport
    if meshes_only:
        panels = cmds.getPanel(type="modelPanel")
        for each in panels:
            cmds.modelEditor(each, edit=True, allObjects=False)
            cmds.modelEditor(each, edit=True, polymeshes=True)
        cmds.refresh()

    # setup the mayaPerformanceTest
    emPerformanceTest.EMPERFORMANCE_PLAYBACK_MAX = frames
    options = emPerformanceTest.emPerformanceOptions()
    options.setViewports(viewports)
    options.setTestTypes([options.TEST_PLAYBACK])
    options.setReportProgress(True)
    options.iterationCount = iterations
    options.evalModes = ["emp"]

    # run the performanceTest
    # (code snippet below from maya source files >>> BLACK MAGIC)
    csv = emPerformanceTest.emPerformanceTest(None, "csv", options)
    row_dictionary = dict(zip(csv[0].split(",")[1:], csv[1].split(",")[1:]))
    start_title, end_title, frame = "Start Frame", "End Frame", 0.0
    if start_title in row_dictionary and end_title in row_dictionary:
        frame = (
            float(row_dictionary[end_title])
            - float(row_dictionary[start_title])
            + 1.0
        )

    # build up message string
    msg = "Playback Speeds\n {:=>17}".format("\n")
    for viewport in viewports:
        mode = "{} - Parallel".format(viewport)
        title = "{} Playback EMP Avg".format(viewport)
        playback_time = float(row_dictionary[title])
        rate = playback_time if frame == 0.0 else frame / playback_time
        msg += "    {} = {} fps\n".format(mode, rate)
    LOG.info("\n %s", msg)

    # re-enable color management
    cmds.colorManagementPrefs(edit=True, cmEnabled=color_management)

    # generate a text file to log out the evaluation result
    if outfile is True:
        scene = cmds.file(query=True, sceneName=True)
        outfile = "{}.txt".format(os.path.splitext(scene)[0]) if scene else ""

    if outfile:
        os.system("echo '{}' > {}".format(msg, outfile))
        LOG.info("FPS logs saved into %s", outfile)

    return rate


class Profiler(ContextDecorator):
    """Create a python profiler to check for code usage.

    Example:
        ::

            from bgdev.tools.performance import Profiler()

            # use as an instantiated object
            profiler = Profiler()
            profiler.start()
            >>> run python code
            profiler.stop()

            # use as a context manager
            with Profiler(sort="tottime", depth=10) as profiler:
                >>> run code

            # print stats
            profiler.stats("cumulative", depth=10)

    """

    def __init__(self, timer=True, stats=True, sort="tottime", depth=8):
        self._use_timer = timer
        self._use_stats = stats
        self._sort = sort
        self._depth = depth

        self.profiler = cProfile.Profile()
        self.pstats = None
        self.timer = 0
        self.start_time = 0
        self.step_time = 0

    def __enter__(self):
        """Initialise the timer on __enter__."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Stop timer and display cProfiler stats."""
        self.stop()
        self.stats()

    def start(self):
        """Enable the profiler."""
        self.start_time = time.time()
        self.step_time = self.start_time
        self.profiler.enable()

    def step(self, message=None, running=False):
        """Display a timer step."""
        running_time = time.time() - self.start_time
        interval_time = time.time() - self.step_time
        self.step_time = time.time()

        msg = message or "Step timer is:"
        self.display_timer(interval_time, msg)

        # display running total
        if running:
            msg = "Running total so far:"
            self.display_timer(running_time, message=msg)

    def stop(self):
        """Stop the profiler."""
        self.profiler.disable()
        self.timer = time.time() - self.start_time
        if self._use_stats:
            self.pstats = pstats.Stats(self.profiler)
        if self._use_timer:
            self.display_timer(self.timer)

    @staticmethod
    def display_timer(timer, message=""):
        """Get execution time."""
        result = datetime.timedelta(seconds=int(timer))
        timecode = "{}min {}secs".format(*str(result).split(":")[1:])
        message = message or "Executed in"
        LOG.info("%s %.4s seconds (%s)", message, timer, timecode)

    def stats(self, sort=None, depth=None):
        """Print profiler's stats.

        Args:
            sort (str): Sort the stats with given value.
            depth (int): Maximum entries to print from the stat table.
        """
        if self.pstats:
            sort = sort or self._sort
            depth = depth or self._depth
            self.pstats.sort_stats(sort).print_stats(depth)
