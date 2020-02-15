# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Sambhav Kothari
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


def _make_releases_node(recording):
    release_list = []
    for release_group in recording['releasegroups']:
        for release in release_group['releases']:
            release_mb = {}
            release_mb['id'] = release['id']
            release_mb['release-group'] = {}
            release_mb['release-group']['id'] = release_group['id']
            if 'type' in release_group:
                release_mb['release-group']['primary-type'] = release_group['type']
            if 'secondarytypes' in release_group:
                release_mb['release-group']['secondary-types'] = release_group['secondarytypes']
            if 'title' in release:
                release_mb['title'] = release['title']
            else:
                release_mb['title'] = release_group['title']

            if 'country' in release:
                release_mb['country'] = release['country']

            if 'date' in release:
                release_mb['date'] = release['date']

            if 'medium_count' in release:
                release_mb['medium_count'] = release['medium_count']

            if 'track_count' in release:
                release_mb['track-count'] = release['track_count']

            release_mb['media'] = []
            for medium in release['mediums']:
                medium_mb = {}
                if 'format' in medium:
                    medium_mb['format'] = medium['format']

                if 'track_count' in medium:
                    medium_mb['track-count'] = medium['track_count']

                if 'position' in medium:
                    medium_mb['position'] = medium['position']

                if 'tracks' in medium:
                    medium_mb['tracks'] = medium['tracks'][0]

                release_mb['media'].append(medium_mb)

            # AcoustId service is returning country/date as attrib of the release, but really, according to MusicBrainz schema definition,
            # its a one-many sub attribute in release events.
            # They do return the releaseevents, but seem to be copying the first one on to the release.
            # So if we have releaseevents, then use them to create multiple records, and ignore what is coming on the release
            if 'releaseevents' in release:
                for releaseevent in release['releaseevents']:
                    release_mb['country'] = releaseevent.get('country', '')
                    release_mb['date'] = releaseevent.get('date', '')
                    release_list.append(release_mb)
            else:
                release_list.append(release_mb)

    return release_list


def _make_artist_node(artist):
    artist_node = {
        'name': artist['name'],
        'sort-name': artist['name'],
        'id': artist['id']
    }
    return artist_node


def _make_artist_credit_node(artists):
    artist_list = []
    for i, artist in enumerate(artists):
        node = {
            'artist': _make_artist_node(artist),
            'name': artist['name']
        }
        if i > 0:
            node['joinphrase'] = '; '
        artist_list.append(node)
    return artist_list


def parse_recording(recording):
    if 'id' not in recording:  # we have no metadata for this recording
        return

    recording_mb = {
        'id': recording['id']
    }

    if 'title' in recording:
        recording_mb['title'] = recording['title']

    if 'artists' in recording:
        recording_mb['artist-credit'] = _make_artist_credit_node(recording['artists'])

    if 'releasegroups' in recording:
        recording_mb['releases'] = _make_releases_node(recording)

    if 'duration' in recording:
        try:
            recording_mb['length'] = int(recording['duration']) * 1000
        except TypeError:
            pass

    if 'sources' in recording:
        recording_mb['sources'] = recording['sources']

    return recording_mb
