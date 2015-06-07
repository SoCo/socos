#!/usr/bin/env Python

"""The music library support for socos"""

from __future__ import print_function


class MusicLibrary(object):
    """Class that implements music library support for socos"""

    def tracks(self, sonos, *args):
        """Public convenience method for `_search_and_play`
        with ``data_type='tracks'``. For details of other arguments
        see `that method
        <#socos.music_lib.MusicLibrary._search_and_play>`_.

        """
        return self._search_and_play(sonos, 'tracks', *args)

    def playlists(self, sonos, *args):
        """Public convenience method for `_search_and_play`
        with ``data_type='playlists'``. For details of other arguments
        see `that method
        <#socos.music_lib.MusicLibrary._search_and_play>`_.

        """
        return self._search_and_play(sonos, 'playlists', *args)

    def sonos_playlists(self, sonos, *args):
        """Public convenience method for `_search_and_play`
        with ``data_type='sonos_playlists'``. For details of other arguments
        see `that method
        <#socos.music_lib.MusicLibrary._search_and_play>`_.
        """
        return self._search_and_play(sonos, 'sonos_playlists', *args)

    def albums(self, sonos, *args):
        """Public convenience method for `_search_and_play`
        with ``data_type='albums'``. For details of other arguments
        see `that method
        <#socos.music_lib.MusicLibrary._search_and_play>`_.

        """
        return self._search_and_play(sonos, 'albums', *args)

    def artists(self, sonos, *args):
        """Public convenience method for `_search_and_play`
        with ``data_type='artists'``. For details of other arguments
        see `that method
        <#socos.music_lib.MusicLibrary._search_and_play>`_.

        """
        return self._search_and_play(sonos, 'artists', *args)

    def _search_and_play(self, sonos, data_type, *args):
        """Retrieve music information objects from the
        music library.

        This method calls the upstream SoCo main method to get,
        and optionally replace or add into the queue, music
        information objects like tracks, albums etc. There are a few
        different ways to call it:

            _search_and_play(sonos, 'artists')

        Will perform a wildcard search for artists.

            _search_and_play(sonos, 'artists', 'Metallica')

        Will perform a fuzzy search for the term 'Metallica' among all
        the artists.

            _search_and_play(sonos, 'artists', 'Metallica', 'add', 1)

        Will perform a fuzzy search for the term 'Metallica' among all
        the artists and add the result by number 1 to the queue. Within
        a group of speakers, this can only be performed on the coordinator.

            _search_and_play(sonos, 'artists', 'Metallica', 'replace', 1)

        Similar to 'add', but this replaces the existing queue with
        the returned music information object.
        """
        if len(args) < 1:
            items = sonos.music_library.get_music_library_information(
                search_type=data_type)
        else:
            items = sonos.music_library.get_music_library_information(
                search_type=data_type, search_term=args[0])

        if len(args) < 2:
            for string in self._print_results(data_type, items):
                yield string
        else:
            yield self._play(sonos, data_type, items, *args)

    @staticmethod
    def _play(sonos, data_type, results, *args):
        """
        Helper method for `_search_and_play` that handles
        adding and replacing of music information objects into
        a queue.

        There are a few different ways to call it:

            _play(sonos, 'artists', results, 'add', 3)

        Will add the item by index 3 from collection `results`
        into the queue.

            _play(sonos, 'artists', items, 'replace', 4)

        Will replace the current queue with the item by index 4 from
        collection `items`.
        """
        action, number = args[1:]

        if action not in ['add', 'replace']:
            message = "'Action must be one of 'add' or 'replace'"
            raise ValueError(message)

        try:
            number = int(number) - 1
        except ValueError:
            raise ValueError('Play number must be parseable as integer')
        if number not in range(len(results)):
            if len(results) == 0:
                message = 'No results to play from'
            elif len(results) == 1:
                message = 'Play number can only be 1'
            else:
                message = 'Play number has to be within the range 1 to {}'.\
                    format(len(results))
            raise ValueError(message)
        item = results[number]
        out = "Added {} to queue: '{}'"
        if action == 'replace':
            sonos.clear_queue()
            out = "Queue replaced with {}: '{}'"
        sonos.add_to_queue(item)
        title = item.title
        if hasattr(title, 'decode'):
            title = title.encode('utf-8')
        return out.format(data_type, title)

    @staticmethod
    def _print_results(data_type, results):
        """Print the results out nicely."""
        print_patterns = {
            'tracks': '{title} on {album} by {creator}',
            'albums': '{title} by {creator}',
            'artists': '{title}',
            'playlists': '{title}',
            'sonos_playlists': '{title}'
        }

        index_length = len(str(len(results)))
        for index, item in enumerate(results):
            item_dict = item.to_dict()
            for key, value in item_dict.items():
                if hasattr(value, 'decode'):
                    item_dict[key] = value.encode('utf-8')
            number = '({{: >{}}}) '.format(index_length).format(index + 1)
            yield number + print_patterns[data_type].format(**item_dict)
