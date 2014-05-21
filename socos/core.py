"""The core module exposes the two public functions process_cmd and shell.
It also contains all private functions used by the two."""

from __future__ import print_function

import sys
import shlex
from collections import OrderedDict

try:
    # pylint: disable=import-error
    import colorama
except ImportError:
    # pylint: disable=invalid-name
    colorama = None

try:
    import readline
except ImportError:
    # pylint: disable=invalid-name
    readline = None

try:
    # pylint: disable=redefined-builtin,invalid-name,undefined-variable
    input = raw_input
except NameError:
    # raw_input has been renamed to input in Python 3
    pass

import soco
from soco.exceptions import SoCoUPnPException

from .exceptions import SoCoIllegalSeekException, SocosException
from .music_lib import MusicLibrary
from .utils import parse_range
from . import mixer

# current speaker (used only in interactive mode)
CUR_SPEAKER = None
# known speakers (used only in interactive mode)
KNOWN_SPEAKERS = {}
# Music library instance
MUSIC_LIB = MusicLibrary()


def process_cmd(args):
    """ Processes a single command """

    cmd = args.pop(0).lower()

    if cmd not in COMMANDS:
        err('Unknown command "{cmd}"'.format(cmd=cmd))
        err(get_help())
        return False

    func, args = _check_args(cmd, args)

    try:
        result = _call_func(func, args)
    except (ValueError, TypeError, SocosException,
            SoCoIllegalSeekException) as ex:
        err(ex)
        return

    # colorama.init() takes over stdout/stderr to give cross-platform colors
    if colorama:
        colorama.init()

    # process output
    if result is None:
        pass

    elif not isinstance(result, str):
        try:
            for line in result:
                print(line)
        except (ValueError, TypeError, SocosException,
                SoCoIllegalSeekException) as ex:
            err(ex)
            return

    else:
        print(result)

    # Release stdout/stderr from colorama
    if colorama:
        colorama.deinit()


def _call_func(func, args):
    """ handles str-based functions and calls appropriately """

    # determine how to call function
    if isinstance(func, str):
        sonos = args.pop(0)
        method = getattr(sonos, func)
        return method(*args)  # pylint: disable=star-args

    else:
        return func(*args)  # pylint: disable=star-args


def _check_args(cmd, args):
    """ checks if func is called for a speaker and updates 'args' """

    req_ip, func = COMMANDS[cmd]

    if not req_ip:
        return func, args

    if not CUR_SPEAKER:
        if not args:
            err('Please specify a speaker IP for "{cmd}".'.format(cmd=cmd))
            return None, None
        else:
            speaker_spec = args.pop(0)
            sonos = soco.SoCo(speaker_spec)
            args.insert(0, sonos)
    else:
        args.insert(0, CUR_SPEAKER)

    return func, args


def shell():
    """ Start an interactive shell """

    if readline is not None:
        readline.parse_and_bind('tab: complete')
        readline.set_completer(complete_command)
        readline.set_completer_delims(' ')

    while True:
        try:
            # Not sure why this is necessary, as there is a player_name attr
            if CUR_SPEAKER:
                # pylint: disable=maybe-no-member
                speaker = CUR_SPEAKER.player_name
                if hasattr(speaker, 'decode'):
                    speaker = speaker.encode('utf-8')
                line = input('socos({speaker}|{state})> '.format(
                    speaker=speaker,
                    state=state(CUR_SPEAKER).title()
                    ))
            else:
                line = input('socos> ')
        except EOFError:
            print('')
            break
        except KeyboardInterrupt:
            print('')
            continue

        line = line.strip()
        if not line:
            continue

        try:
            args = shlex.split(line)
        except ValueError as value_error:
            err('Syntax error: %(error)s' % {'error': value_error})
            continue

        try:
            process_cmd(args)
        except KeyboardInterrupt:
            err('Keyboard interrupt.')
        except EOFError:
            err('EOF.')


def complete_command(text, context):
    """ auto-complete commands

    text is the text to be auto-completed
    context is an index, increased for every call for "text" to get next match
    """
    matches = [cmd for cmd in COMMANDS.keys() if cmd.startswith(text)]
    return matches[context]


def get_current_track_info(sonos):
    """ Show the current track """
    track = sonos.get_current_track_info()
    return (
        "Current track: %s - %s. From album %s. This is track number"
        " %s in the playlist. It is %s minutes long." % (
            track['artist'],
            track['title'],
            track['album'],
            track['playlist_position'],
            track['duration'],
        )
    )


def get_queue(sonos):
    """ Show the current queue """
    queue = sonos.get_queue()

    # pylint: disable=invalid-name
    ANSI_BOLD = '\033[1m'
    ANSI_RESET = '\033[0m'

    current = int(sonos.get_current_track_info()['playlist_position'])

    queue_length = len(queue)
    padding = len(str(queue_length))

    for idx, track in enumerate(queue, 1):
        if idx == current:
            color = ANSI_BOLD
        else:
            color = ANSI_RESET

        idx = str(idx).rjust(padding)
        yield (
            "%s%s: %s - %s. From album %s.%s" % (
                color,
                idx,
                track.creator,
                track.title,
                track.album,
                ANSI_RESET,
            )
        )


def err(message):
    """ print an error message """
    print(message, file=sys.stderr)


def get_queue_length(sonos):
    """ Helper function for queue related functions """
    return len(sonos.get_queue())


def is_index_in_queue(index, queue_length):
    """ Helper function to verify if index exists """
    if index > 0 and index <= queue_length:
        return True
    return False


def play_index(sonos, index):
    """ Play an item from the playlist """
    index = int(index)
    queue_length = get_queue_length(sonos)

    if is_index_in_queue(index, queue_length):
        # Translate from socos one-based to SoCo zero-based
        index -= 1
        position = sonos.get_current_track_info()['playlist_position']
        current = int(position) - 1
        if index != current:
            return sonos.play_from_queue(index)
    else:
        error = "Index %d is not within range 1 - %d" % (index, queue_length)
        raise ValueError(error)


def list_ips():
    """ List available devices """
    ip_to_device = {device.ip_address: device for device in soco.discover()}
    ip_addresses = list(ip_to_device.keys())
    ip_addresses.sort()

    KNOWN_SPEAKERS.clear()
    for zone_number, ip_address in enumerate(ip_addresses, 1):
        # pylint: disable=no-member
        name = ip_to_device[ip_address].player_name
        if hasattr(name, 'decode'):
            name = name.encode('utf-8')
        KNOWN_SPEAKERS[str(zone_number)] = ip_to_device[ip_address]
        yield '({}) {: <15} {}'.format(zone_number, ip_address, name)


def speaker_info(sonos):
    """ Information about a speaker """
    infos = sonos.get_speaker_info()
    return ('%s: %s' % (i, infos[i]) for i in infos)


def volume(sonos, *args):
    """ Change or show the volume of a device """
    if not args:
        return str(sonos.volume)

    operator = args[0]
    newvolume = mixer.adjust_volume(sonos, operator)
    return str(newvolume)


def bass(sonos, *args):
    """ Change or show the bass value of a device """
    if not args:
        return str(sonos.bass)

    operator = args[0]
    newbass = mixer.adjust_bass(sonos, operator)
    return str(newbass)


def treble(sonos, *args):
    """ Change or show the treble value of a device """
    if not args:
        return str(sonos.treble)

    operator = args[0]
    newtreble = mixer.adjust_treble(sonos, operator)
    return str(newtreble)


def exit_shell():
    """ Exit socos """
    sys.exit(0)


def play(sonos, *args):
    """ Start playing """
    if args:
        idx = args[0]
        play_index(sonos, idx)
    else:
        sonos.play()
    return get_current_track_info(sonos)


def remove_from_queue(sonos, *args):
    """ Remove track from queue by index """
    if args:
        rem_range = parse_range(args[0])
        remove_range_from_queue(sonos, rem_range)

    return get_queue(sonos)


def remove_range_from_queue(sonos, rem_range):
    """ Remove a range of tracks from queue

    rem_range should be a sequence, such as a range object """
    for index in sorted(rem_range, reverse=True):
        remove_index_from_queue(sonos, index)


def remove_index_from_queue(sonos, index):
    """ Remove one track from the queue by its index """
    queue_length = get_queue_length(sonos)
    if is_index_in_queue(index, queue_length):
        sonos.remove_from_queue(index)
    else:
        error = "Index %d is not within range 1 - %d" % (index, queue_length)
        raise ValueError(error)


def play_next(sonos):
    """ Play the next track """
    try:
        sonos.next()
    except SoCoUPnPException:
        raise SoCoIllegalSeekException('No such track')
    return get_current_track_info(sonos)


def play_previous(sonos):
    """ Play the previous track """
    try:
        sonos.previous()
    except SoCoUPnPException:
        raise SoCoIllegalSeekException('No suck track')
    return get_current_track_info(sonos)


def state(sonos):
    """ Get the current state of a device / group """
    return sonos.get_current_transport_info()['current_transport_state']


def set_speaker(arg):
    """ Set the current speaker for the shell session by ip or speaker number

    Parameters:
    arg    is either an ip or the number of a speaker as shown by list
    """
    # Update the list of known speakers if that has not already been done
    if not KNOWN_SPEAKERS:
        list(list_ips())

    # pylint: disable=global-statement,fixme
    # TODO: this should be refactored into a class with instance-wide state
    global CUR_SPEAKER
    # Set speaker by speaker number as identified by list_ips ...
    if '.' not in arg and arg in KNOWN_SPEAKERS:
        CUR_SPEAKER = KNOWN_SPEAKERS[arg]
    # ... and if not that, then by ip
    else:
        CUR_SPEAKER = soco.SoCo(arg)


def unset_speaker():
    """ resets the current speaker for the shell session """
    global CUR_SPEAKER  # pylint: disable=global-statement
    CUR_SPEAKER = None


def get_help(command=None):
    """ Prints a list of commands with short description """

    def _cmd_summary(item):
        """ Format command name and first line of docstring """
        name, func = item[0], item[1][1]
        if isinstance(func, str):
            func = getattr(soco.SoCo, func)
        doc = getattr(func, '__doc__') or ''
        doc = doc.split('\n')[0].lstrip()
        return ' * {cmd:12s} {doc}'.format(cmd=name, doc=doc)

    if command and command in COMMANDS:
        func = COMMANDS[command][1]
        doc = getattr(func, '__doc__') or ''
        doc = [line.lstrip() for line in doc.split('\n')]
        out = '\n'.join(doc)
    else:
        texts = ['Available commands:']
        # pylint: disable=bad-builtin
        texts += map(_cmd_summary, COMMANDS.items())
        out = '\n'.join(texts)
    return out


# COMMANDS indexes commands by their name. Each command is a 2-tuple of
# (requires_ip, function) where function is either a callable, or a
# method name to be called on a SoCo instance (depending on requires_ip)
# If requires_ip is False, function must be a callable.
COMMANDS = OrderedDict((
    #  cmd         req IP  func
    # pylint: disable=bad-whitespace
    ('list',         (False, list_ips)),
    ('partymode',    (True, 'partymode')),
    ('info',         (True, speaker_info)),
    ('play',         (True, play)),
    ('pause',        (True, 'pause')),
    ('stop',         (True, 'stop')),
    ('next',         (True, play_next)),
    ('previous',     (True, play_previous)),
    ('current',      (True, get_current_track_info)),
    ('queue',        (True, get_queue)),
    ('remove',       (True, remove_from_queue)),
    ('volume',       (True, volume)),
    ('bass',         (True, bass)),
    ('treble',       (True, treble)),
    ('state',        (True, state)),
    ('ml_index',     (True, MUSIC_LIB.index)),
    ('ml_tracks',    (True, MUSIC_LIB.tracks)),
    ('ml_albums',    (True, MUSIC_LIB.albums)),
    ('ml_artists',   (True, MUSIC_LIB.artists)),
    ('ml_playlists', (True, MUSIC_LIB.playlists)),
    ('exit',         (False, exit_shell)),
    ('set',          (False, set_speaker)),
    ('unset',        (False, unset_speaker)),
    ('help',         (False, get_help)),
))
