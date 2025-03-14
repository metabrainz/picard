# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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


import unittest
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.browser.addrelease import (
    InvalidTokenError,
    NotFoundError,
    _form_input_template,
    _generate_token,
    is_available,
    is_enabled,
    jwt,
    serve_form,
    submit_cluster,
    submit_file,
)
from picard.metadata import Metadata


@unittest.skipIf(jwt is None, "PyJWT not available")
class AddReleaseTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.tagger.browser_integration = MagicMock()

    def test_is_available(self):
        self.assertTrue(is_available())

    def test_is_enabled(self):
        self.tagger.browser_integration.is_running = True
        self.assertTrue(is_enabled())

    def test_is_not_enabled(self):
        self.tagger.browser_integration.is_running = False
        self.assertFalse(is_enabled())

    @patch('picard.browser.addrelease._open_url_with_token')
    def test_submit_cluster(self, mock_open_url):
        cluster = MagicMock()
        submit_cluster(cluster)
        expected = {'cluster': hash(cluster)}
        mock_open_url.assert_called_with(expected)

    @patch('picard.browser.addrelease._open_url_with_token')
    def test_submit_file(self, mock_open_url):
        file = MagicMock()
        file.filename = '/some/file'
        submit_file(file, as_release=True)
        expected = {'file': file.filename, 'as_release': True}
        mock_open_url.assert_called_with(expected)


@unittest.skipIf(jwt is None, "PyJWT not available")
class ServeFormTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.tagger.browser_integration = MagicMock()
        self.tagger.clusters = []
        self.set_config_values({
            'server_host': 'musicbrainz.org',
            'use_server_for_submission': False,
        })

    def test_invalid_jwt(self):
        invalid_token = jwt.encode({'cluster': ''}, 'invalidkey', algorithm='HS256')
        with self.assertRaises(InvalidTokenError):
            serve_form(invalid_token)

    def test_invalid_payload(self):
        token = _generate_token({})
        with self.assertRaises(InvalidTokenError):
            serve_form(token)

    def test_cluster_not_found(self):
        token = _generate_token({'cluster': 'doesnotexist'})
        with self.assertRaises(NotFoundError):
            serve_form(token)

    def test_cluster(self):
        cluster = MagicMock()
        file1 = MagicMock()
        file1.metadata = Metadata({
            'tracknumber': 'A',
            'discnumber': '2',
            'title': 'Song 2',
            'label': 'The Label',
            'catalognumber': '12345',
            'barcode': '67890',
            'musicbrainz_recordingid': 'abc',
        })
        file1.discnumber = 2
        file1.tracknumber = 1
        file2 = MagicMock()
        file2.discnumber = 1
        file2.tracknumber = 1
        file2.metadata = Metadata({
            'tracknumber': '1',
            'discnumber': '1',
            'title': 'Song 1',
        })
        cluster.files = [file1, file2]
        cluster.metadata = Metadata({
            'album': 'The Album',
            'albumartist': 'The Artist',
        })
        self.tagger.clusters.append(cluster)
        token = _generate_token({'cluster': hash(cluster)})
        form = serve_form(token)
        self._validate_form(form, expected_fields={
            'name': cluster.metadata['album'],
            'artist_credit.names.0.artist.name': cluster.metadata['albumartist'],
            'mediums.0.track.0.name': file2.metadata['title'],
            'mediums.0.track.0.number': file2.metadata['tracknumber'],
            'mediums.1.track.0.name': file1.metadata['title'],
            'mediums.1.track.0.number': file1.metadata['tracknumber'],
        })

    def test_file_not_found(self):
        token = _generate_token({'file': 'doesnotexist'})
        with self.assertRaises(NotFoundError):
            serve_form(token)

    def test_file(self):
        file = MagicMock()
        file.filename = '/some/file'
        file.metadata = Metadata({
            'title': 'A Song',
            'artist': 'The Artist',
        })
        file.metadata.length = 102000
        self.tagger.files = {file.filename: file}
        token = _generate_token({'file': file.filename})
        form = serve_form(token)
        self._validate_form(form, expected_fields={
            'edit-recording.name': file.metadata['title'],
            'edit-recording.artist_credit.names.0.artist.name': file.metadata['artist'],
            'edit-recording.length': '1:42',
        })

    def test_file_as_release(self):
        file = MagicMock()
        file.filename = '/some/file'
        file.metadata = Metadata({
            'title': 'A Song',
            'artist': 'The Artist',
        })
        self.tagger.files = {file.filename: file}
        token = _generate_token({'file': file.filename, 'as_release': True})
        form = serve_form(token)
        self._validate_form(form, expected_fields={
            'name': file.metadata['title'],
            'artist_credit.names.0.artist.name': file.metadata['artist'],
        })

    def _validate_form(self, form, expected_fields=None):
        self.assertTrue(form.startswith('<!doctype html>'))
        self.assertIn('<script>document.forms[0].submit()</script>', form)
        if expected_fields:
            for name, value in expected_fields.items():
                self.assertIn(_form_input_template.format(name=name, value=value), form)
