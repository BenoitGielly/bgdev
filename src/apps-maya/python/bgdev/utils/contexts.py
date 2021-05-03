"""Context managers.

:created: 08/04/2021
:author: Benoit GIELLY <benoit.gielly@gmail.com>

"""
import contextlib

from bgdev.logger import LOG


@contextlib.contextmanager
def execute_ctx(status):
    """Execute code in a try/except context manager."""
    try:
        LOG.info(status)
        yield
    except Exception as exc:  # pylint:disable=broad-except
        LOG.error("Failed: %s", exc)
