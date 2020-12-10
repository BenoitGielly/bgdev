"""Evaluation Toolkit.

:created: 03/06/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import cProfile
import logging
import os

from maya import cmds, mel
from maya.debug import emPerformanceTest  # type: ignore

LOG = logging.getLogger(__name__)


def frames_per_second(
    iterations=3,
    start=1001,
    frames=100,
    viewports=("viewport2"),
    meshes_only=True,
    outfile=None,
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

    Returns:
        float: The evaluated frame per seconds as a float number.

    """
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


class Profiler(object):
    """Create a python profiler to check for code usage.

    Example:
        ::

            import bgdev.tools.performance
            profiler = bgdev.tools.performance.Profiler()
            profiler.start()
            # run python code
            profiler.stop()
    """

    def __init__(self):
        self.profiler = cProfile.Profile(subcalls=False)

    def start(self):
        """Enable the profiler."""
        self.profiler.enable()

    def stop(self, sort="time"):
        """Stop the profiler and print restult.

        Args:
            sort(str): Sort the stats with given value.
        """
        self.profiler.disable()
        self.stats(sort)

    def stats(self, sort="tottime"):
        """Print the profiler stats.

        Args:
            sort(str): Sort the stats with given value.
        """
        self.profiler.print_stats(sort=sort)
