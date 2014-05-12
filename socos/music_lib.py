#!/usr/bin/env python

""" The music library support for socos """

from __future__ import print_function


import os
from collections import OrderedDict
import sqlite3
import json
from soco.data_structures import MLTrack, MLAlbum, MLArtist, MLPlaylist
from socos.exceptions import SocosException


class MusicLibrary(object):
    """Class that implements the music library support for socos"""

    def __init__(self):
        # Sqlite3 variables
        self.connection = None
        self.cursor = None
        # As a simple opitmization we cache 10 searches
        self.cached_searches = OrderedDict()
        self.cache_length = 10
        # Date type and tables names
        self.data_types = ['playlists', 'artists', 'albums', 'tracks']

    def _open_db(self):
        """Open a connection to the sqlite3 database and if necessary create
        the the folders and path for it. The file will be saved to:
        USERPATH/.config/socos/musiclib.db where USERPATH is as returned by
        os.path.expanduser
        """
        if not self.connection:
            userdir = os.path.expanduser('~')
            dbdir = os.path.join(userdir, '.config', 'socos')
            if not os.path.exists(dbdir):
                os.makedirs(dbdir)
                yield 'Created folder: \'{}\''.format(dbdir)

            dbpath = os.path.join(dbdir, 'musiclib.db')
            if not os.path.exists(dbpath):
                yield 'Created Sqlite3 database for music library '\
                      'information at: \'{}\''.format(dbpath)
            self.connection = sqlite3.connect(dbpath)
            self.cursor = self.connection.cursor()

    def index(self, sonos):
        """Update the index of the music library information"""
        for string in self._open_db():
            yield string
        # Drop old tables
        query = 'SELECT name FROM sqlite_master WHERE type = "table"'
        self.cursor.execute(query)
        number_of_tables = len(self.cursor.fetchall())
        if number_of_tables == 4:
            yield 'Deleting tables'
            query = 'DROP TABLE {}'
            for table_name in self.data_types:
                self.cursor.execute(query.format(table_name))
        self.connection.commit()

        # Form new tables
        yield 'Creating tables'
        create_statements = [
            'CREATE TABLE tracks (title text, album text, artist text, '
            'content text)',
            'CREATE TABLE albums (title text, artist text, content text)',
            'CREATE TABLE artists (title text, content text)',
            'CREATE TABLE playlists (title text, content text)',
        ]
        for create in create_statements:
            self.cursor.execute(create)
        self.connection.commit()

        # Index the 4 different types of data
        for data_type in self.data_types:
            for string in self._index_single_type(sonos, data_type):
                yield string

    def _index_single_type(self, sonos, data_type):
        """Index a single type if data"""
        fields = self._get_columns(data_type)
        # Artist is called creator in the UPnP data structures
        if 'artist' in fields:
            fields[fields.index('artist')] = 'creator'

        # E.g: INSERT INTO tracks VALUES (?,?,?,?)
        query = 'INSERT INTO {} VALUES ({})'.format(
            data_type, ','.join(['?'] * len(fields)))

        # For brevity
        get_ml_inf = sonos.get_music_library_information

        total = get_ml_inf(data_type, 0, 1)['total_matches']
        yield 'Adding: {}'.format(data_type)
        count = 0
        while count < total:
            # Get as many matches as the device will give each time
            search = get_ml_inf(data_type, start=count, max_items=1000)
            for item in search['item_list']:
                # In the database we save a set of text fields and the content
                # dict as json. See self.index for details on fields.
                values = [getattr(item, field) for field in
                          fields[:-1]]
                values.append(json.dumps(item.to_dict))
                self.cursor.execute(query, values)
            self.connection.commit()

            # Print out status while running because indexing tracks can take a
            # while
            count += search['number_returned']
            yield '{{: >3}}%  {{: >{0}}} out of {{: >{0}}}'\
                .format(len(str(total)))\
                .format(count * 100 / total, count, total)

    def _get_columns(self, table):
        """Return the names of the columns in the table"""
        query = 'PRAGMA table_info({})'.format(table)
        self.cursor.execute(query)
        # The table descriptions look like: (0, u'title', u'text', 0, None, 0)
        return [element[1] for element in self.cursor.fetchall()]

    def tracks(self, sonos, *args):
        """Search for and possibly play tracks from the music library

        Usage: ml_tracks [field=]text [action] [number]

        Field can be 'title', 'album' or 'artist'. If field is not given, then
        'title' is used. Only a single word can be used as search text. Action
        can be 'add' or 'replace' and number refers to the item number in the
        search results.

        Examples:
        ml_tracks artist=metallica
        ml_tracks unforgiven
        ml_tracks unforgiven add 4
        """
        for string in self._search_and_play(sonos, 'tracks', *args):
            yield string

    def albums(self, sonos, *args):
        """Search for and possibly play albums from the music library

        Usage: ml_albums [field=]text [action] [number]

        Field can be 'title' or 'artist'. If field is not given, then 'title'
        is used. Only a single word can be used as search text. Action can be
        'add' or 'replace' and number refers to the item number in the search
        results.

        Examples:
        ml_albums artist=metallica
        ml_albums black
        ml_albums black add 1
        """
        for string in self._search_and_play(sonos, 'albums', *args):
            yield string

    def artists(self, sonos, *args):
        """Search for and possibly play all by artists from music library

        Usage: ml_artists text [action] [number]

        'text' is searched for in the artist titles. Only a single word can '\
        'be used as search text. Action can be 'add' or 'replace' and number '\
        'refers to the item number in the search results.

        Examples:
        ml_artists metallica
        ml_artists metallica add 1
        """
        for string in self._search_and_play(sonos, 'artists', *args):
            yield string

    def playlists(self, sonos, *args):
        """Search for and possibly play playlists imported in the music library

        Usage: ml_playlists text [action] [number]

        'text' is searched for in the playlist titles. Only a single word '\
        'can be used as search text. Action can be 'add' or 'replace' and '\
        'number refers to the item number in the search results.

        Examples:
        ml_playlist metallica
        ml_playlist metallica add 3
        """
        for string in self._search_and_play(sonos, 'playlists', *args):
            yield string

    def _search_and_play(self, sonos, data_type, *args):
        """Perform a music library search and possibly play and item"""
        # Open the data base
        for string in self._open_db():
            yield string

        # Check if the music library has been indexed
        query = 'SELECT name FROM sqlite_master WHERE type = "table"'
        self.cursor.execute(query)
        if len(self.cursor.fetchall()) != 4:
            message = 'Your music library cannot be search until it has been '\
                      'indexed. First run \'ml_index\''
            raise SocosException(message)
        # Check if there is a search term
        if len(args) < 1:
            message = 'Search term missing. See \'help ml_{}\' for details'.\
                format(data_type)
            raise ValueError(message)

        # And finally perform the search
        results = self._search(data_type, *args)

        # If there are no other arguments then the search
        if len(args) == 1:
            for string in self._print_results(data_type, results):
                yield string
        # Or if there are the right number for a play command
        elif len(args) == 3:
            yield self._play(sonos, data_type, results, *args)
        # Else give error
        else:
            message = 'Incorrect play syntax: See \'help ml_{}\' for details'.\
                format(data_type)
            raise ValueError(message)

    def _search(self, data_type, *args):
        """Perform the search"""
        # Process search term
        search_string = args[0]
        if search_string.count('=') == 0:
            field = 'title'
            search = search_string
        elif search_string.count('=') == 1:
            field, search = search_string.split('=')
        else:
            message = '= signs are not allowed in the search string'
            raise ValueError(message)

        # Pad the search term with SQL LIKE wild cards
        search = search.join(['%', '%'])
        # Do the search, if it has not been cached
        if (data_type, field, search) in self.cached_searches:
            results = self.cached_searches[(data_type, field, search)]
        else:
            if field in self._get_columns(data_type)[:-1]:
                # Perform the search in Sqlite3
                query = 'SELECT * FROM {} WHERE {} LIKE ?'.format(data_type,
                                                                  field)
                try:
                    search = search.decode('utf-8')
                except AttributeError:
                    pass
                self.cursor.execute(query, [search])
                results = self.cursor.fetchall()
                # Add results to the cache and reduce cache length if necesary
                self.cached_searches[(data_type, field, search)] = results
                while len(self.cached_searches) > self.cache_length:
                    self.cached_searches.popitem(last=False)
            else:
                message = 'The search field \'{}\' is unknown. Only {} is '\
                    'allowed'.format(field, self._get_columns(data_type)[:-1])
                raise ValueError(message)
        return results

    @staticmethod
    def _play(sonos, data_type, results, *args):
        """Play music library item from search"""
        action, number = args[1:]
        # Check action
        if action not in ['add', 'replace']:
            message = 'Action must be \'add\' or \'replace\''
            raise ValueError(message)

        # Convert and check number
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
                message = 'Play number has to be in the range from 1 to {}'.\
                          format(len(results))
            raise ValueError(message)

        # The last item in the search is the content dict in json
        item_dict = json.loads(results[number][-1])
        ml_classes = {'tracks': MLTrack, 'albums': MLAlbum,
                      'artists': MLArtist, 'playlists': MLPlaylist}
        item = ml_classes[data_type].from_dict(item_dict)

        # Save state before queue manipulation
        player_state =\
            sonos.get_current_transport_info()['current_transport_state']
        out = 'Added to queue: \'{}\''
        if action == 'replace':
            sonos.clear_queue()
            out = 'Queue replaced with: \'{}\''
        sonos.add_to_queue(item)
        if action == 'replace' and player_state == 'PLAYING':
            sonos.play()

        title = item.title
        if hasattr(title, 'decode'):
            title = title.encode('utf-8')
        return out.format(title)

    @staticmethod
    def _print_results(data_type, results):
        """Print the results out nicely"""
        print_patterns = {
            'tracks': '\'{title}\' on \'{album}\' by \'{creator}\'',
            'albums': '\'{title}\' by \'{creator}\'',
            'artists': '\'{title}\'',
            'playlists': '\'{title}\''
        }
        # Length of the results length number
        index_length = len(str(len(results)))
        for index, item in enumerate(results):
            item_dict = json.loads(item[-1])
            for key, value in item_dict.items():
                if hasattr(value, 'decode'):
                    item_dict[key] = value.encode('utf-8')
            number = '({{: >{}}}) '.format(index_length).format(index + 1)
            # pylint: disable=star-args
            yield number + print_patterns[data_type].format(**item_dict)
