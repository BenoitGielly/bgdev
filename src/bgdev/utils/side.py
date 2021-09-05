"""Module to deal with sided data.

:created: 02/07/2018
:author: Benoit Gielly <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from copy import deepcopy


def convert_side(data, sides="LR", both=False):
    # pylint: disable=too-many-branches
    """Replace recursively all iterations of {} with side in a data structure.

    Args:
        data (list or dict): The data to traverse and update.
        sides (str): The sides to replace brackets with.
        both (bool): By default, if the key is "sided", the values associated
            will only get the same side as the key.
            Otherwise, values will get both sides. Default is `False`.

    Example:
        ::

            data = side.convert_side({
                "spine_01_grp": "spine_01_jnt",
                "{}_shoulder_mechanic_grp": "{}_arm_shoulder_jnt",
                "{}_knee_pistons_grp": "{}_leg_knee_jnt",
            })

            >>> # Result: {"L_knee_pistons_grp": "L_leg_knee_jnt",
                 "L_shoulder_mechanic_grp": "L_arm_shoulder_jnt",
                 "R_knee_pistons_grp": "R_leg_knee_jnt",
                 "R_shoulder_mechanic_grp": "R_arm_shoulder_jnt",
                 "spine_01_grp": "spine_01_jnt"} #

    Returns:
        dict or list: An updated and sided copy of the given data.

    """
    # convert string to list
    if isinstance(data, basestring):
        data = [data]

    # set list to be dict values
    is_list = isinstance(data, list)
    data = dict(key=data) if is_list else data

    # iter key/values and replace sides
    for key, values in deepcopy(data).iteritems():
        if key.startswith("{}"):
            del data[key]
            base_val = values
            for side in sides:
                values = deepcopy(base_val)
                if both:
                    data[key.format(side)] = values
                    continue
                if isinstance(values, dict):
                    values = convert_side(values, sides=[side])
                elif isinstance(values, basestring):
                    values = values.format(side)
                else:
                    values = [x.format(side) for x in values]
                    _ = [
                        values.remove(x)
                        for x in list(values)
                        if values.count(x) > 1
                    ]
                data[key.format(side)] = values

    for key, values in deepcopy(data).iteritems():
        if isinstance(values, dict):
            values = convert_side(values)
        elif isinstance(values, basestring):
            if values.startswith("{}"):
                values = list({values.format(side) for side in sides})
        else:
            values = [x.format(side) for x in values for side in sides]
            _ = [values.remove(x) for x in list(values) if values.count(x) > 1]
        data[key] = values

    return data.values()[0] if is_list else data
