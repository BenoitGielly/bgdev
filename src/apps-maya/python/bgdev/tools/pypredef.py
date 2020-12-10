"""Generate pypredefs using Maya's help query to read command flags.

:created: 18/05/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from keyword import iskeyword
import logging
import os
import re

from maya import cmds, mel

try:
    import urllib
except ImportError:
    import urllib2 as urllib


LOG = logging.getLogger(__name__)


def get_maya_urls():
    """Generate a table for each commands from the online documentation.

    Returns:
        dict: Generates a {command:url} dictionnary.
    """
    version = cmds.about(majorVersion=True)
    url = (
        "http://help.autodesk.com/cloudhelp/{}/"
        "ENU/Maya-Tech-Docs/CommandsPython/{{}}.html"
    ).format(version)

    try:
        response = urllib.urlopen(url.format("index_all"))
        html = response.read()
        commands = re.findall(r'<a href="(.*?).html"', html)
    except (urllib.URLError, urllib.HTTPError):
        commands = []

    data = {}
    for each in commands:
        data[each] = url.format(each)
    return data


def indent(text, amount=4):
    """Indent each lines of the given string.

    Args:
        text (str): Text to indent
        amount (int): Number or character padding

    Returns:
        str: Indented text.

    """
    return "".join(amount * " " + line for line in text.splitlines(True))


def cleanup_flags(docstring):
    """Cleanup the docstring from the mel output to a nicer result.

    Args:
        docstring (str): The docstring extracted from the help command query.

    Example:

        Reformat this docstring::

            Flags:
               -n -name        String
               -p -parent      String
               -s -shared
              -ss -skipSelect

        So it looks like this::

            Flags:
                name (n): String
                parent (p): String
                shared (s): None
                skipSelect (ss): None

    Also returns a list of all the flags so they can be added to the method
    definition (eg. "flag=None") so IDE can autocomplete them.

    Args:
        docstring (str): The docstring containing the flags to cleanup.

    Returns:
        tuple: The cleaned-up docstring with nicer flags, and the list of flags
    """
    lines = docstring.splitlines(True)

    # get header
    header = lines[0].strip()

    # parse other lines
    desc_lines = []
    flag_lines = []
    temp_flags = []
    for each in lines[1:]:
        line = each.strip()
        if "Flags" in each:
            flag_lines.append(line)
        elif line.startswith("-"):
            temp_flags.append(line)
        elif line:
            desc_lines.append(line)

    # parse and cleanup flags
    flags = []
    for line in temp_flags:
        shortname, longname, desc = None, None, None
        for each in line.split():
            if each.startswith("-") and not shortname:
                shortname = each[1:]
            elif each.startswith("-"):
                longname = each[1:]
            else:
                desc = each
        if not longname:
            longname, shortname = shortname, longname
        txt = "{} ({}): {}".format(longname, shortname, desc)
        flag_lines.append(indent(txt, 4))
        flag = longname if not iskeyword(longname) else shortname
        if flag:
            flags.append(flag)

    return header, desc_lines, flag_lines, flags


def generate_pypredef(module, outdir=None, doclink=True):
    """Generate pypredefs using Maya's help query to read command flags.

    Args:
        module (mod): Module from which you want to generate the pypredef.
        outdir (str): Directory in which you want to export the text file.
        doclink (bool): Adds a link to the online documentation.

    Note:
        There are a few maya commands (e.g. "nexCtx") that are almost
        1 MILLION line length... so there's a test to skip the command
        if the docstring is longer than 10k lines.

    Example:
        ::

            from maya import cmds
            generate_pypredef(cmds, outdir="~/Desktop")

    """
    filetext = ""
    # use the cmds.help method if extracting maya commands
    if module.__name__ == "maya.cmds":
        maya_urls = get_maya_urls() if doclink else {}
        commands = sorted(cmds.help("*", list=True))
        for each in commands:
            if hasattr(cmds, each) and not iskeyword(each):
                strip = cmds.help(each).strip()
                if len(strip) > 10000:
                    continue
                header, l_desc, l_flags, all_flags = cleanup_flags(strip)
                header = "{}.\n".format(header) if header else header
                html = maya_urls.get(each, "")
                html = "\n{}\n".format(html) if html else html
                desc = "\n".join(l_desc)
                desc = "\n{}\n".format(desc) if desc else desc
                flags = "\n".join(l_flags)
                flags = "\n{}\n".format(flags) if flags else flags
                docstring = '"""{}{}{}{}\n"""\nreturn args, kwargs\n'
                docstring = docstring.format(header, html, desc, flags)
                def_flags = "=None, ".join([x for x in all_flags])
                def_flags += "=None, " if def_flags else ""
                def_txt = "\n\ndef {}({}*args, **kwargs):\n{}".format(
                    each, def_flags, indent(docstring, 4)
                )
                filetext += def_txt

    # use python to list commands otherwise
    else:
        for each in sorted(dir(module)):
            if bool(mel.eval("exists " + each)):
                strip = mel.eval("help %s" % each).strip("\n")
                strip = strip if not "\n" in strip else strip + "\n"
                if len(strip) > 10000:
                    continue
                docstring = '"""{}"""\nreturn args, kwargs\n'.format(strip)
                def_txt = "\n\ndef {}(*args, **kwargs):\n{}".format(
                    each, indent(docstring, 4)
                )
                filetext += def_txt

    # create path
    if not outdir:
        outdir = os.path.join(os.environ.get("HOME"), "pypredef")
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # export file
    file_path = os.path.join(outdir, "%s.pypredef" % module.__name__)
    with open(file_path, "w") as stream:
        stream.writelines(filetext)

    LOG.info("Pypredef generated and saved into %r", file_path)
