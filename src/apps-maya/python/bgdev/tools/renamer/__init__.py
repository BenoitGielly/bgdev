"""Convenient wrapper to the core and ui modules.

:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""


def show(*args, **kwargs):
    """Wrap the show function of the core module."""
    from . import core

    return core.show(*args, **kwargs)
