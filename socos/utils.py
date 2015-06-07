"""various utility functions"""

import re
from functools import wraps
from soco import SoCo

# matches single numbers ("123") or ranges ("12..34")
RANGE_PATTERN = re.compile(r'(\d+)(..(\d+))?')


def parse_range(txt):
    """Matches a single number A or a range of two numbers A..B

    The range A..B is interpreted as including both A and B

    >>> list(parse_range('123'))
    [123]

    # comparing range objects is not possible in Python 3.2
    >>> list(parse_range('12..34')) == list(range(12, 35))
    True
    """

    matches = RANGE_PATTERN.match(txt)

    if not matches:
        raise ValueError('Invalid number or range: "{}"'.format(txt))

    # the first number is always matched
    val1 = int(matches.group(1))

    # group(2) is "..val2", group(3) is "val2"
    if matches.group(3) is not None:
        val2 = int(matches.group(3))
    else:
        # no second number, so we need a range of length 1
        val2 = val1

    return range(val1, val2+1)


def requires_coordinator(func):
    """
    A decorator to mark functions requiring a
    group coordinator device.
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        """
        Grab sonos from first argument to the original function and turn this
        into sonos.group.coordinator
        before returning the decorated function.
        """
        args = list(args)
        if isinstance(args[0], SoCo):  # Static method
            args[0] = args[0].group.coordinator
        else:  # Ordinary method
            args[1] = args[1].group.coordinator
        return func(*args, **kwargs)
    return decorated
