import sys


def forget(module):
    """Remove given module from sys.modules dict.

    Forces Python to forget about given module and reload it when called again.

    Args:
        module (str): The name of the module to forget.
    """
    for each in sorted(sys.modules.copy()):
        if each == module or each.startswith("{}.".format(module)):
            del sys.modules[each]
