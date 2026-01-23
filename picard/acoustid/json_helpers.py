# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018-2020, 2023 Philipp Wolfer
# Copyright (C) 2020 Ray Bouchard
# Copyright (C) 2020-2021 Laurent Monin
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

# -*- coding: utf-8 -*-

"""
The idea here is to bring the data returned by the AcoustID service into the
same format as the JSON result from the MB web service. Below methods help us
to do that conversion process.
"""

def _make_releases_node(recording):
    release_list = []
    # Cache the iterator to avoid repeated lookups
    for rg in recording.get('releasegroups', []):
        # Local caching: access once, use many times
        rg_id = rg.get('id')
        rg_type = rg.get('type')
        rg_sec_types = rg.get('secondarytypes')
        rg_title = rg.get('title')

        for rel in rg.get('releases', []):
            # Pre-build the base release structure
            base_release = {
                'id': rel.get('id'),
                'release-group': {
                    'id': rg_id,
                    'primary-type': rg_type,
                    'secondary-types': rg_sec_types
                },
                'title': rel.get('title', rg_title),
                'country': rel.get('country'),
                'date': rel.get('date'),
                'medium-count': rel.get('medium_count'),
                'track-count': rel.get('track_count'),
                'media': []
            }

            # Optimization: Remove 'None' values from release-group in one pass
            base_release['release-group'] = {
                k: v for k, v in base_release['release-group'].items() if v is not None
            }

            for medium in rel.get('mediums', []):
                media_mb = {
                    'format': medium.get('format'),
                    'track-count': medium.get('track_count'),
                    'position': medium.get('position'),
                }
                if 'tracks' in medium:
                    tracks = medium['tracks']
                    for t in tracks:
                        # Direct assignment is faster than calling functions repeatedly
                        t['number'] = t.get('position')
                    media_mb['track'] = tracks
                
                base_release['media'].append(media_mb)

            # Fix the reference bug: append copies if there are multiple events
            events = rel.get('releaseevents')
            if events:
                for event in events:
                    new_rel = base_release.copy()
                    new_rel['country'] = event.get('country', '')
                    new_rel['date'] = event.get('date', '')
                    release_list.append(new_rel)
            else:
                release_list.append(base_release)

    return release_list


def _make_artist_node(artist):
    # Using a literal is slightly faster than dict()
    name = artist.get('name')
    return {
        'name': name,
        'sort-name': name,
        'id': artist.get('id'),
    }


def _make_artist_credit_node(artists):
    # List comprehension is significantly faster for larger artist lists
    return [
        {
            'artist': _make_artist_node(a),
            'name': a.get('name'),
            'joinphrase': '; ' if i > 0 else None
        }
        for i, a in enumerate(artists)
    ]


def parse_recording(recording):
    rec_id = recording.get('id')
    if not rec_id:
        return None

    recording_mb = {'id': rec_id}

    # Clean check for optional attributes
    for attr in ('title', 'sources'):
        if attr in recording:
            recording_mb[attr] = recording[attr]

    if 'artists' in recording:
        recording_mb['artist-credit'] = _make_artist_credit_node(recording['artists'])

    if 'releasegroups' in recording:
        recording_mb['releases'] = _make_releases_node(recording)

    duration = recording.get('duration')
    if duration is not None:
        try:
            recording_mb['length'] = int(duration) * 1000
        except (ValueError, TypeError):
            pass

    return recording_mb


def recording_has_metadata(recording):
    # Short-circuit evaluation for speed
    return 'id' in recording and recording.get('title') is not None
