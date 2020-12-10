"""Useful decorators to use for methods.

:created: 11/12/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from functools import partial, wraps
from traceback import print_exc

from maya import cmds

_ARGS = {}
_KWARGS = {}
_REPEAT_FUNC = None


def selected(func):
    """Decorate a func to use selection if no args passed."""  # noqa: D202

    @wraps(func)
    def decorator(*args, **kwargs):
        """Decorator."""
        func_return = []
        for each in args or cmds.ls(selection=True):
            func_return.append(func(each, **kwargs))
        return func_return

    return decorator


def _repeat_me():
    # pylint: disable=not-callable
    _REPEAT_FUNC(*_ARGS, **_KWARGS)


def _add_to_last(func, args, kwargs):
    globals()["_REPEAT_FUNC"] = func
    globals()["_ARGS"] = args
    globals()["_KWARGS"] = kwargs

    cmd = "_repeat_me()"
    if __name__ != "__main__":
        cmd = "import {0};{0}._repeat_me()".format(__name__)

    # somehow the callback can errors
    # even though mel.eval-ing it would work...
    try:
        cmds.repeatLast(addCommand='python("{0}")'.format(cmd))
    except BaseException:
        pass


def _undo_me(func, args, kwargs):
    cmds.undoInfo(openChunk=True)
    func_return = None
    try:
        func_return = func(*args, **kwargs)
    except BaseException:
        print_exc()
    finally:
        cmds.undoInfo(closeChunk=True)
    return func_return


def method_decorator(func, repeat=False, undo=False):
    """Decorate a method to make it repeatable and/or undoable.

    Args:
        func (function): The method to decorate.
        repeat (bool): Makes the method repeatable.
        undo (bool): Makes the method undoable.

    Example:
        You can use the custom wrappers in this module
        to decorate your method as you'd like::

            import rigging.ui.decorator

            @bgdev.ui.decorator.UNDO
            def undoable_only_method(*args, **kwargs):
                return args, kwargs

            @bgdev.ui.decorator.REPEAT
            def repeatable_only_method(*args, **kwargs):
                return args, kwargs

            @bgdev.ui.decorator.UNDO_REPEAT
            def undoable_repeatable_method(*args, **kwargs):
                return args, kwargs

    Returns:
        function: The decorated method.
    """
    # black blank line
    @wraps(func)
    def decorator(*args, **kwargs):
        """Actual method being run."""
        if undo:
            func_return = _undo_me(func, args, kwargs)
        else:
            func_return = func(*args, **kwargs)
        if repeat:
            _add_to_last(func, args, kwargs)
        return func_return

    return decorator


UNDO = partial(method_decorator, undo=True, repeat=False)
REPEAT = partial(method_decorator, undo=False, repeat=True)
UNDO_REPEAT = partial(method_decorator, undo=True, repeat=True)
