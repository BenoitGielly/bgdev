"""Docstring template using Google convention.

:created: 16/11/2018
:author: Benoit Gielly <benoit.gielly@gmail.com>

This module is just a template to show how to write docstrings properly
using the Google's syntax. It will show all the different use cases and
keywords to use to get sphinx working nicely.

You can find a link to the Google Docstring guide here:
    http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

Happy docstring-ing! :D

"""
from __future__ import absolute_import, print_function

from functools import wraps
from traceback import print_exc


def example_function(param1, param2=None, *args, **kwargs):
    # pylint: disable=keyword-arg-before-vararg,unused-argument
    """Show an example of a module level function.

    Function parameters should be documented in the ``Args`` section. The name
    of each parameter is required. The type and description of each parameter
    is optional, but should be included if not obvious.

    If ``*args`` or ``**kwargs`` are accepted,
    they should be listed as ``*args`` and ``**kwargs``.

    The format for a parameter is::

        name (type): description
            The description may span multiple lines. Following
            lines should be indented. The "(type)" is optional.

            Multiple paragraphs are supported in parameter
            descriptions.

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter. Defaults to None.
            Second line of description should be indented.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        bool: True if successful, False otherwise.

        The return type is optional and may be specified at the beginning of
        the ``Returns`` section followed by a colon.

        The ``Returns`` section may span multiple lines and paragraphs.
        Following lines should be indented to match the first line.

        The ``Returns`` section supports any reStructuredText formatting,
        including literal blocks::

            {
                'param1': param1,
                'param2': param2
            }

    Raises:
        AttributeError: The ``Raises`` section is a list of all exceptions
            that are relevant to the interface.
        ValueError: If `param2` is equal to `param1`.

    Example:
        ``Examples`` should be written in doctest format, and should
        illustrate how to use the function.

        >>> print([i for i in range(4)])
        [0, 1, 2, 3]

    Examples:
        You can also use literal blocks::

            print([i for i in range(4)])
            >>> [0, 1, 2, 3]

    Todo:
        * The ``Todo`` section lists in an orange block every task that needs to be done.
        * Make sure to use an * (asterisk) to display bullet points

    """
    if param1 == param2:
        raise ValueError("param1 may not be equal to param2")
    return True


def example_generator(num):
    """Create generators.

    They have a ``Yields`` section instead of a ``Returns`` section.

    Args:
        num (int): The upper limit of the range to generate,
            from 0 to `num` - 1.

    Yields:
        int: The next number in the range of 0 to `num` - 1.

    """
    for i in range(num):
        yield i


def example_decorator(func):
    """Decorate a method.

    Decorators need a special treatment to generate the documentation properly.
    You have to decorate the inner function with `@wraps` from `functools` or
    the docstring of the decorated function will be ignored.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        """Docstring."""
        try:
            return func(*args, **kwargs)
        except BaseException:
            print_exc()

    return inner


@example_decorator
def example_decorated_function(arg):
    """Test the docstring to ensure the @wraps decorator worked.

    Args:
        arg (str): Description of `arg1`

    Returns:
        type: The value of `arg1`

    """
    return arg


class ExampleClass(object):
    """The summary line for a class docstring should fit on one line.

    If the class has public attributes, they may be documented here
    in an ``Attributes`` section and follow the same formatting as a
    function's ``Args`` section. Alternatively, attributes may be documented
    inline with the attribute's declaration (see __init__ method below).

    Properties created with the ``@property`` decorator should be documented
    in the property's getter method.

    Attributes:
        attr1 (str): Description of `attr1`.
        attr2 (:obj:`int`, optional): Description of `attr2`.
    """

    def __init__(self, param1, param2, param3):
        """Init method example docstring.

        The __init__ should be documented here rather than the class docstring.

        Note:
            Do not include the `self` parameter in the ``Args`` section.

        Args:
            param1 (str): Description of `param1`.
            param2 (:obj:`int`): Description of `param2`.
                Multiple lines are supported.
            param3 (list(str)): Description of `param3`.
        """
        self._value = None
        self.attr1 = param1
        self.attr2 = param2
        self.attr3 = param3  #: Doc comment *inline* with attribute

        #: list(str): Doc comment *before* attribute, with type specified
        self.attr4 = ["attr4"]

        self.attr5 = None
        """str: Docstring *after* attribute, with type specified."""

    @property
    def getter_only_property(self):
        """str: Properties should be documented in their getter method."""
        return "getter_only_property"

    @property
    def getter_setter_property(self):
        # pylint: disable=differing-param-doc,differing-type-doc
        """Get a property.

        If the setter method contains notable behavior, it should be
        mentioned here.

        Args:
            value (str): Properties with both a getter and setter
                should only be documented in their getter method.

        Returns:
            list: The returned value/object.
        """
        return ["getter_setter_property"]

    @getter_setter_property.setter
    def getter_setter_property(self, value):
        self._value = value

    def example_method(self, param1, param2):
        """Class methods are similar to regular functions.

        See :func:`.example_function` for a better description.

        Note:
            Do not include the `self` parameter in the ``Args`` section.

        """
        return self.attr1, param1, param2
