""" The mixer modules functionality for adjusting volume, bass, treble. """


def _adjust_setting(soco, attr, operator, min_val, max_val):
    """ Adjust setting "attr" by "operator" """

    factor = get_factor(operator)
    val = getattr(soco, attr)
    newval = in_range(val + factor, min_val, max_val)
    setattr(soco, attr, newval)

    return getattr(soco, attr)


def adjust_volume(soco, operator):
    """ Adjust the volume up or down with a factor from 1 to 100 """
    return _adjust_setting(soco, 'volume', operator, 0, 100)


def adjust_bass(soco, operator):
    """ Adjust the bass up or down with a factor from -10 to 10 """
    return _adjust_setting(soco, 'bass', operator, -10, 10)


def adjust_treble(soco, operator):
    """ Adjust the treble up or down with a factor from -10 to 10 """
    return _adjust_setting(soco, 'treble', operator, -10, 10)


def get_factor(operator):
    """ get the factor to adjust the volume, bass, treble... with

    Returns the parsed number, but accounts for operator-only input.

    >>> get_factor('+10')
    10

    >>> get_factor('+')
    1

    >>> get_factor('-')
    -1
    """

    if not operator.startswith(('+', '-')):
        raise ValueError("Valid operators are + and -")

    # if we only have an operator, we assume 1
    if len(operator) == 1:
        operator += '1'

    try:
        return int(operator)

    except ValueError:
        raise ValueError('"{}" is not a number or +/-'.format(operator))


def in_range(val, min_val, max_val):
    """ Make sure val is within min_val, max_val

    >>> in_range(5, 0, 10)
    5

    >>> in_range(0, -10, 10)
    0

    >>> in_range(0, 10, 20)
    10

    >>> in_range(100, 0, 10)
    10
    """
    return min(max(val, min_val), max_val)
