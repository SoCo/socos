# pylint: disable=too-many-arguments,duplicate-code

"""The core module exposes the two public functions process_cmd and shell.
It also contains all private functions used by the two."""

from __future__ import print_function

import sys
import shlex
from functools import partial
from collections import OrderedDict, namedtuple

try:
    import readline
except ImportError:
    # pylint: disable=invalid-name
    readline = None

try:
    # pylint: disable=import-error
    import colorama
except ImportError:
    # pylint: disable=invalid-name
    colorama = None

import soco
from soco.exceptions import SoCoUPnPException

from socos.exceptions import SoCoIllegalSeekException, SocosException
from socos.utils import parse_range, requires_coordinator
from socos.music_lib import MusicLibrary

from . import mixer

try:
    # pylint: disable=redefined-builtin,invalid-name,undefined-variable
    input = raw_input
except NameError:
    # raw_input has been renamed to input in Python 3
    pass


def err(message):
    """Print an error message"""
    print(message, file=sys.stderr)


def is_index_in_queue(index, queue_length):
    """Helper function to verify if index exists"""
    if index > 0 and index <= queue_length:
        return True
    return False


# The CommandSpec named tuple is used to specify a command.
# Args:
#     requires_ip (bool): Whether the command requires an IP-address
#     command_name (str): The name of the command
#     obj_name (str): The name of the object in the SoCos instance that holds
#         the method that should be executed by this command (None means the
#          SoCos instance itself
#     method_name (str): The name of the method (on obj_name) that should be
#         executed by this command
CommandSpec = namedtuple(
    'CommandSpec', 'requires_ip command_name obj_name method_name')


def add_command(cmd_list, requires_ip=True, command_name=None, obj_name=None,
                method_name=None, only_on_coordinator=False):
    """Return a add command decorator

    This decorator with arguments is used to indicate that a method should add
    a command.

    Args:
        cmd_list (list): List to add commands to, in the form of a CommandSpec
        requires_ip (bool): Indicates if the command needs an IP-address
        command_name (str): The name of the command, if left out will default
            to the method name
        obj_name (str): The name of the object the method should be fetched
            from, if left out assume it is the SoCos instance
        method_name (str): The name of the method (on obj_name) that should be
            called on command
        only_on_coordinator (bool): Whether the command should only be run on
            a coordinator

    NOTE: The reason for using object and method names instead of simply saving
    the method, is that at decorator time, the method has not been bound yet,
    so it is only a normal function. This would give problems when trying to
    call it. So instead note down the object and method names and form the
    list with the actual methods when the instance is fully created.
    """
    def decorate(function, command_name=command_name, obj_name=obj_name,
                 method_name=method_name):
        """Add a command to commands"""
        # Apply requires_coordinator decorator if required
        if only_on_coordinator:
            function = requires_coordinator(function)

        # Get default values
        if method_name is None:
            method_name = function.__name__
        if command_name is None:
            command_name = function.__name__

        # Append the command spec
        cmd_list.append(
            CommandSpec(requires_ip, command_name, obj_name, method_name)
        )
        return function
    return decorate


class SoCos(object):  # pylint: disable=too-many-public-methods
    """The main SoCos class"""

    # The list of command (specs) will be filled out during class parsing by
    # means of decorators
    command_list = []
    add_command = partial(add_command, command_list)

    def __init__(self):
        self.known_speakers = {}
        self.current_speaker = None
        self.music_lib = MusicLibrary()

        # Form the ordered dict of commands
        self.commands = OrderedDict()
        for command_spec in self.command_list:
            if command_spec.obj_name is None:
                obj = self
            else:
                obj = getattr(self, command_spec.obj_name)
            self.commands[command_spec.command_name] = (
                command_spec.requires_ip,
                getattr(obj, command_spec.method_name)
            )

    def process_cmd(self, args):
        """Process a single command"""

        cmd = args.pop(0).lower()

        if cmd not in self.commands:
            err('Unknown command "{cmd}"'.format(cmd=cmd))
            err(self.get_help())
            return False

        func, args = self._check_args(cmd, args)
        # None, None is returned with missing IP, in this case return
        if (func, args) == (None, None):
            return

        try:
            result = func(*args)
        except (KeyError, ValueError, TypeError, SocosException,
                SoCoIllegalSeekException) as ex:
            err(ex)
            return

        # colorama.init() takes over stdout/stderr to give cross-platform
        # colors
        if colorama:
            colorama.init()

        # process output
        if result is None:
            pass
        elif not isinstance(result, str):
            try:
                for line in result:
                    print(line)
            except (KeyError, ValueError, TypeError, SocosException,
                    SoCoIllegalSeekException) as ex:
                err(ex)
                return
        else:
            print(result)

        # Release stdout/stderr from colorama
        if colorama:
            colorama.deinit()

    def _check_args(self, cmd, args):
        """Checks if func is called for a speaker and updates 'args'"""

        req_ip, func = self.commands[cmd]

        if not req_ip:
            return func, args

        if not self.current_speaker:
            if not args:
                err('Please specify a speaker IP for "{cmd}".'.format(cmd=cmd))
                return None, None
            else:
                speaker_spec = args.pop(0)
                sonos = soco.SoCo(speaker_spec)
                args.insert(0, sonos)
        else:
            args.insert(0, self.current_speaker)

        return func, args

    def shell(self):
        """Start an interactive shell"""

        if readline is not None:
            readline.parse_and_bind('tab: complete')
            readline.set_completer(self.complete_command)
            readline.set_completer_delims(' ')

        while True:
            try:
                # Not sure why this is necessary, as there is a player_name
                # attr
                if self.current_speaker:
                    # pylint: disable=maybe-no-member
                    speaker = self.current_speaker.player_name
                    if hasattr(speaker, 'decode'):
                        speaker = speaker.encode('utf-8')
                    line = input('socos({speaker}|{state})> '.format(
                        speaker=speaker,
                        state=self.state(self.current_speaker).title()
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
                self.process_cmd(args)
            except KeyboardInterrupt:
                err('Keyboard interrupt.')
            except EOFError:
                err('EOF.')

    def complete_command(self, text, context):
        """auto-complete commands

        Args:
            text (str): The text to be auto-completed
            context (int): An index that is increased for every call for
                "text" to get next match
        """
        matches = [cmd for cmd in self.commands.keys() if cmd.startswith(text)]
        return matches[context]

    # ### Helper methods
    @staticmethod
    @requires_coordinator
    def get_queue_length(sonos):
        """Return the queue length"""
        return len(sonos.get_queue())

    @requires_coordinator
    def play_index(self, sonos, index):
        """Play an item from the playlist"""
        index = int(index)
        queue_length = self.get_queue_length(sonos)

        if is_index_in_queue(index, queue_length):
            # Translate from socos one-based to SoCo zero-based
            index -= 1
            position = sonos.get_current_track_info()['playlist_position']
            current = int(position) - 1
            if index != current:
                return sonos.play_from_queue(index)
        else:
            error = "Index %d is not within range 1 - %d" % \
                    (index, queue_length)
            raise ValueError(error)

    def remove_range_from_queue(self, sonos, rem_range):
        """Remove a range of tracks from queue

        rem_range should be a sequence, such as a range object"""
        for index in sorted(rem_range, reverse=True):
            self.remove_index_from_queue(sonos, index)

    @requires_coordinator
    def remove_index_from_queue(self, sonos, index):
        """Remove one track from the queue by its index"""
        queue_length = self.get_queue_length(sonos)
        if is_index_in_queue(index, queue_length):
            index -= 1
            sonos.remove_from_queue(index)
        else:
            error = "Index %d is not within range 1 - %d" % \
                    (index, queue_length)
            raise ValueError(error)

    # ### Here starts the commands
    @add_command(requires_ip=False, command_name='list')
    def list_ips(self):
        """List available devices"""
        ip_to_device = {device.ip_address: device
                        for device in soco.discover()}
        ip_addresses = list(ip_to_device.keys())
        ip_addresses.sort()

        self.known_speakers.clear()
        for zone_number, ip_address in enumerate(ip_addresses, 1):
            # pylint: disable=no-member
            name = ip_to_device[ip_address].player_name
            if hasattr(name, 'decode'):
                name = name.encode('utf-8')
            self.known_speakers[str(zone_number)] = ip_to_device[ip_address]
            yield '({}) {: <15} {}'.format(zone_number, ip_address, name)

    @add_command(requires_ip=False)
    def partymode(self):
        """Put all the speakers in the same group, a.k.a Party Mode."""
        self.current_speaker.partymode()

    @staticmethod
    @add_command(command_name='info')
    def speaker_info(sonos):
        """Information about a speaker"""
        infos = sonos.get_speaker_info()
        return ('%s: %s' % (i, infos[i]) for i in infos)

    @add_command(only_on_coordinator=True)
    def play(self, sonos, *args):
        """Start playing"""
        if args:
            idx = args[0]
            self.play_index(sonos, idx)
        else:
            sonos.play()
        return self.get_current_track_info(sonos)

    @add_command(only_on_coordinator=True)
    def pause(self, sonos):
        """Pause"""
        if self.state(sonos) == 'PLAYING':
            sonos.pause()
        return self.get_current_track_info(sonos)

    @add_command(only_on_coordinator=True)
    def stop(self, sonos):
        """Stop"""
        states = ['PLAYING', 'PAUSED_PLAYBACK']

        if self.state(sonos) in states:
            sonos.stop()
        return self.get_current_track_info(sonos)

    @add_command(only_on_coordinator=True)
    def next(self, sonos):
        """Play the next track"""
        try:
            sonos.next()
        except SoCoUPnPException:
            raise SoCoIllegalSeekException('No such track')
        return self.get_current_track_info(sonos)

    @add_command(only_on_coordinator=True)
    def previous(self, sonos):
        """Play the previous track"""
        try:
            sonos.previous()
        except SoCoUPnPException:
            raise SoCoIllegalSeekException('No suck track')
        return self.get_current_track_info(sonos)

    @staticmethod
    @add_command(only_on_coordinator=True)
    def mode(sonos, *args):
        """Change or show the play mode of a device
        Accepted modes: NORMAL, SHUFFLE_NOREPEAT, SHUFFLE, REPEAT_ALL"""
        if not args:
            return sonos.play_mode

        mode = args[0]
        sonos.play_mode = mode

        return sonos.play_mode

    @staticmethod
    @add_command(only_on_coordinator=True, command_name='current')
    def get_current_track_info(sonos):
        """Show the current track"""
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

    @staticmethod
    @add_command(only_on_coordinator=True, command_name='queue')
    def get_queue(sonos):
        """Show the current queue"""
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

    @add_command(command_name='remove')
    def remove_from_queue(self, sonos, *args):
        """Remove track from queue by index"""
        if args:
            rem_range = parse_range(args[0])
            self.remove_range_from_queue(sonos, rem_range)

        return self.get_queue(sonos)

    @staticmethod
    @add_command()
    def volume(sonos, *args):
        """Change or show the volume of a device"""
        if not args:
            return str(sonos.volume)

        operator = args[0]
        newvolume = mixer.adjust_volume(sonos, operator)
        return str(newvolume)

    @staticmethod
    @add_command()
    def bass(sonos, *args):
        """Change or show the bass value of a device"""
        if not args:
            return str(sonos.bass)

        operator = args[0]
        newbass = mixer.adjust_bass(sonos, operator)
        return str(newbass)

    @staticmethod
    @add_command()
    def treble(sonos, *args):
        """Change or show the treble value of a device"""
        if not args:
            return str(sonos.treble)

        operator = args[0]
        newtreble = mixer.adjust_treble(sonos, operator)
        return str(newtreble)

    @staticmethod
    @add_command(only_on_coordinator=True)
    def state(sonos):
        """Get the current state of a device / group"""
        return sonos.get_current_transport_info()['current_transport_state']

    # Add music library commands
    for method_name in ['tracks', 'albums', 'artists', 'playlists',
                        'sonos_playlists']:
        command_list.append(
            CommandSpec(requires_ip=True, command_name=method_name,
                        obj_name='music_lib', method_name=method_name)
        )

    @staticmethod
    @add_command(requires_ip=False, command_name='exit')
    def exit_shell():
        """Exit socos"""
        sys.exit(0)

    @add_command(requires_ip=False, command_name='set')
    def set_speaker(self, arg):
        """Set the current speaker for the shell session by ip or speaker
        number

        Args:
            arg (str or int): Is either an ip or the number of a speaker as
                shown by list
        """
        # Update the list of known speakers if that has not already been done
        if not self.known_speakers:
            list(self.list_ips())

        # Set speaker by speaker number as identified by list_ips ...
        if '.' not in arg and arg in self.known_speakers:
            self.current_speaker = self.known_speakers[arg]
        # ... and if not that, then by ip
        else:
            self.current_speaker = soco.SoCo(arg)

    @add_command(requires_ip=False, command_name='unset')
    def unset_speaker(self):
        """Resets the current speaker for the shell session"""
        self.current_speaker = None

    @add_command(requires_ip=False, command_name='help')
    def get_help(self, command=None):
        """Print a list of commands with short description"""

        def _cmd_summary(item):
            """Format command name and first line of docstring"""
            name, func = item[0], item[1][1]
            doc = getattr(func, '__doc__') or ''
            doc = doc.split('\n')[0].lstrip()
            return ' * {cmd:12s} {doc}'.format(cmd=name, doc=doc)

        if command and command in self.commands:
            func = self.commands[command][1]
            doc = getattr(func, '__doc__') or ''
            doc = [line.lstrip() for line in doc.split('\n')]
            out = '\n'.join(doc)
        else:
            texts = ['Available commands:']
            # pylint: disable=bad-builtin
            texts += map(_cmd_summary, self.commands.items())
            out = '\n'.join(texts)
        return out
