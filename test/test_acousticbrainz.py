# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021 Laurent Monin
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


from functools import partial
import json
import logging
import os
from unittest.mock import (
    MagicMock,
    Mock,
)

from test.picardtestcase import PicardTestCase

from picard.acousticbrainz import (
    ABExtractor,
    ab_extractor_callback,
    ab_feature_extraction,
)
from picard.file import File


mock_extractor = os.path.abspath("./test/data/acousticbrainz/mock_acousticbrainz_extractor.py")

settings = {
    "use_acousticbrainz": True,
    "acousticbrainz_extractor": "",
    "acousticbrainz_extractor_version": "",
    "acousticbrainz_extractor_sha": "",
    "clear_existing_tags": False,
    "compare_ignore_tags": [],
}


class AcousticBrainzSetupTest(PicardTestCase):

    def test_ab_setup_present(self):
        settings['acousticbrainz_extractor'] = mock_extractor
        self.set_config_values(settings)

        # Try to setup AB
        ab_extractor = ABExtractor()

        # Extractor should be found
        self.assertTrue(ab_extractor.available())

    def test_ab_setup_not_present(self):
        settings['acousticbrainz_extractor'] = "non_existing_extractor"
        self.set_config_values(settings)

        # Try to setup AB
        ab_extractor = ABExtractor()

        # Extractor should not be found
        self.assertFalse(ab_extractor.available())


class AcousticBrainzFeatureExtractionTest(PicardTestCase):
    ab_features_file = "test/data/acousticbrainz/acousticbrainz_sample.json"
    singleton = None

    def setUp(self):
        super().setUp()

        AcousticBrainzFeatureExtractionTest.singleton = self
        # Setup mock extractor
        settings['acousticbrainz_extractor'] = mock_extractor
        self.set_config_values(settings)

        with self.loglevel(logging.DEBUG):
            self.tagger.ab_extractor = ABExtractor()
            self.assertTrue(self.tagger.ab_extractor.available())

        # Load an irrelevant test file
        self.file = File("./test/data/test.mp3")

        # Load the AB features sample and copy the recording ID
        with open(self.ab_features_file, "r", encoding="utf-8") as f:
            ab_features = json.load(f)

        # Copy the MB recordingID to the file, as we only work with already matched files
        self.file.metadata['musicbrainz_recordingid'] = ab_features['metadata']['tags']['musicbrainz_trackid']

        self.tagger.webservice = MagicMock()

    @staticmethod
    def mock_ab_extractor_callback_duplicate(tagger, file, result, error):
        AcousticBrainzFeatureExtractionTest.singleton.assertEqual(error, None)
        ab_metadata_file, result, error = result
        AcousticBrainzFeatureExtractionTest.singleton.assertTrue("Duplicate" in error)

    @staticmethod
    def mock_ab_extractor_callback_extraction_failed(tagger, file, result, error):
        AcousticBrainzFeatureExtractionTest.singleton.assertEqual(error, None)
        ab_metadata_file, result, error = result
        AcousticBrainzFeatureExtractionTest.singleton.assertTrue("Duplicate" not in error or "Writing results" not in error)

    @staticmethod
    def mock_ab_extractor_callback_extraction_succeeded(tagger, file, result, error):
        AcousticBrainzFeatureExtractionTest.singleton.assertEqual(error, None)
        ab_metadata_file, result, error = result
        AcousticBrainzFeatureExtractionTest.singleton.assertTrue("Writing results" in error)

    def mock_get_succeed(self, host, port, path, handler, priority, important, parse_response_type):
        # Return features in utf-8 straight from the web response
        error = 0
        with open(AcousticBrainzFeatureExtractionTest.ab_features_file, "rb") as f:
            response = f.read()
        reply = ""
        handler(response, reply, error)

    def mock_get_fail(self, host, port, path, handler, priority, important, parse_response_type):
        error = 203
        response = b"""{"message":"Not found"}\n"""
        reply = ""
        handler(response, reply, error, main_thread=True)

    def test_check_duplicate(self):
        self.tagger.webservice.get = Mock(wraps=self.mock_get_succeed)
        ab_feature_extraction(
            self.tagger,
            self.file.metadata["musicbrainz_recordingid"],
            self.file.filename,
            partial(self.mock_ab_extractor_callback_duplicate, self.tagger, self.file)
        )

    def test_check_not_duplicate_and_fail_extraction(self):
        self.tagger.webservice.get = Mock(wraps=self.mock_get_fail)
        ab_feature_extraction(
            self.tagger,
            self.file.metadata["musicbrainz_recordingid"],
            "fail.mp3",
            partial(self.mock_ab_extractor_callback_extraction_failed, self.tagger, self.file)
        )

    def test_check_not_duplicate_and_succeed_extraction(self):
        self.tagger.webservice.get = Mock(wraps=self.mock_get_fail)
        ab_feature_extraction(
            self.tagger,
            self.file.metadata["musicbrainz_recordingid"],
            "test.mp3",
            partial(self.mock_ab_extractor_callback_extraction_succeeded, self.tagger, self.file)
        )


class AcousticBrainzFeatureSubmissionTest(AcousticBrainzFeatureExtractionTest):
    def setUp(self):
        super().setUp()
        self.tagger.webservice.get = Mock(wraps=self.mock_get_fail)

        # Setup methods and settings required by file.set_pending and file.clear_pending
        self.tagger.tagger_stats_changed = MagicMock()
        self.tagger.tagger_stats_changed.emit = Mock(wraps=self.mock_emit)
        self.set_config_values(settings)

    @staticmethod
    def mock_ab_submission_failed(tagger, file, result, error):
        AcousticBrainzFeatureExtractionTest.singleton.assertEqual(error, None)
        ab_metadata_file, result, error = result
        AcousticBrainzFeatureExtractionTest.singleton.assertTrue("Duplicate" not in error or "Writing results" not in error)

    @staticmethod
    def mock_ab_submission_succeeded(tagger, file, result, error):
        AcousticBrainzFeatureExtractionTest.singleton.assertEqual(error, None)
        ab_metadata_file, result, error = result
        AcousticBrainzFeatureExtractionTest.singleton.assertTrue("Writing results" in error)

    def mock_emit(self):
        pass

    def mock_post_succeed(self, host, port, path, data, handler, parse_response_type, priority, important, mblogin, queryargs=None, request_mimetype=None):
        handler("""{"message":"ok"}""", "", 0)

    def mock_post_fail(self, host, port, path, data, handler, parse_response_type, priority, important, mblogin, queryargs=None, request_mimetype=None):
        handler("""APIBadRequest""", "", 400)

    def test_submit_failed(self):
        self.file.set_pending()
        self.tagger.webservice.post = Mock(wraps=self.mock_post_fail)
        ab_feature_extraction(
            self.tagger,
            self.file.metadata["musicbrainz_recordingid"],
            "test.mp3",
            partial(ab_extractor_callback, self.tagger, self.file)
        )

    def test_submit_succeeded(self):
        self.file.set_pending()
        self.tagger.webservice.post = Mock(wraps=self.mock_post_succeed)
        ab_feature_extraction(
            self.tagger,
            self.file.metadata["musicbrainz_recordingid"],
            "test.mp3",
            partial(ab_extractor_callback, self.tagger, self.file)
        )
