# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014 Music Technology Group - Universitat Pompeu Fabra
# Copyright (C) 2020-2021 Gabriel Ferreira
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Philipp Wolfer
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
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


from collections import (
    defaultdict,
    namedtuple,
)
from concurrent.futures import Future
from functools import partial
import json
import os
from tempfile import NamedTemporaryFile

from picard import log
from picard.acousticbrainz.extractor import (
    check_extractor_version,
    precompute_extractor_sha,
)
from picard.config import get_config
from picard.const import (
    ACOUSTICBRAINZ_HOST,
    ACOUSTICBRAINZ_PORT,
    EXTRACTOR_NAMES,
)
from picard.util import (
    find_executable,
    load_json,
    run_executable,
)
from picard.util.thread import run_task
from picard.webservice import ratecontrol


ratecontrol.set_minimum_delay((ACOUSTICBRAINZ_HOST, ACOUSTICBRAINZ_PORT), 1000)

ABExtractorProperties = namedtuple('ABExtractorProperties', ('path', 'version', 'sha', 'mtime_ns'))


class ABExtractor:

    def __init__(self):
        self._init_cache()

    def _init_cache(self):
        self.cache = defaultdict(lambda: None)

    def get(self, config=None):
        if not config:
            config = get_config()
        if not config.setting["use_acousticbrainz"]:
            log.debug('ABExtractor: AcousticBrainz disabled')
            return None

        extractor_path = config.setting["acousticbrainz_extractor"]
        if not extractor_path:
            extractor_path = find_extractor()
        else:
            extractor_path = find_executable(extractor_path)
        if not extractor_path:
            log.debug('ABExtractor: cannot find a path to extractor binary')
            return None

        try:
            statinfo = os.stat(extractor_path)
            mtime_ns = statinfo.st_mtime_ns
        except OSError as exc:
            log.warning('ABExtractor: cannot stat extractor: %s', exc)
            return None

        # check if we have this in cache already
        cached = self.cache[(extractor_path, mtime_ns)]
        if cached is not None:
            log.debug('ABExtractor: cached: %r', cached)
            return cached

        # create a new cache entry
        try:
            version = check_extractor_version(extractor_path)
            if version:
                sha = precompute_extractor_sha(extractor_path)
                result = ABExtractorProperties(
                    path=extractor_path,
                    version=version,
                    sha=sha,
                    mtime_ns=mtime_ns
                )
                # clear the cache, we keep only one entry
                self._init_cache()
                self.cache[(result.path, result.mtime_ns)] = result
                log.debug('ABExtractor: caching: %r', result)
                return result
            else:
                raise Exception("check_extractor_version(%r) returned None" % extractor_path)
        except Exception as exc:
            log.warning('ABExtractor: failed to get version or sha: %s', exc)
        return None

    def path(self, config=None):
        result = self.get(config)
        return result.path if result else None

    def version(self, config=None):
        result = self.get(config)
        return result.version if result else None

    def sha(self, config=None):
        result = self.get(config)
        return result.sha if result else None

    def available(self, config=None):
        return self.get(config) is not None


def find_extractor():
    return find_executable(*EXTRACTOR_NAMES)


def ab_check_version(extractor):
    extractor_path = find_executable(extractor)
    return check_extractor_version(extractor_path)


def ab_feature_extraction(tagger, recording_id, input_path, extractor_callback):
    # Fetch existing features from AB server to check for duplicates before extracting
    tagger.webservice.get(
        host=ACOUSTICBRAINZ_HOST,
        port=ACOUSTICBRAINZ_PORT,
        path="/%s/low-level" % recording_id,
        handler=partial(run_extractor, tagger, input_path, extractor_callback),
        priority=True,
        important=False,
        parse_response_type=None
    )


def ab_extractor_callback(tagger, file, result, error):
    file.clear_pending()

    ab_metadata_file, result, error = result.result() if isinstance(result, Future) else result
    if "Writing results" in error and ab_metadata_file:
        file.acousticbrainz_features_file = ab_metadata_file
        log.debug("AcousticBrainz extracted features of recording %s: %s" %
                  (file.metadata["musicbrainz_recordingid"], file.filename,))

        # Submit results
        ab_submit_features(tagger, file)
    elif 'Duplicate' in error:
        log.debug("AcousticBrainz already has an entry for recording %s: %s" %
                  (file.metadata["musicbrainz_recordingid"], file.filename,))
        file.acousticbrainz_is_duplicate = True
    else:
        # Something went wrong
        log.debug("AcousticBrainz extraction failed with error: %s" % error)
        file.acousticbrainz_error = True
        if result == 1:
            log.warning("AcousticBrainz extraction failed: %s" % file.filename)
        elif result == 2:
            log.warning(
                "AcousticBrainz extraction failed due to missing a MusicBrainz Recording ID: %s" % file.filename)
        else:
            log.warning("AcousticBrainz extraction failed due to an unknown error: %s" % file.filename)
    file.update()


def run_extractor(tagger, input_path, extractor_callback, response, reply, error, main_thread=False):
    duplicate = False
    # Check if AcousticBrainz server answered with the json file for the recording id
    if not error:
        # If it did, mark file as duplicate and skip extraction
        try:
            load_json(response)
            duplicate = True
        except json.JSONDecodeError:
            pass

    if duplicate:
        # If an entry for the same recording ID already exists
        # using the same extractor version exists, skip extraction
        results = (None, 0, "Duplicate")
        extractor_callback(results, None)
    else:
        if main_thread:
            # Run extractor on main thread, used for testing
            extractor_callback(extractor(tagger, input_path), None)
        else:
            # Run extractor on a different thread and call the callback when done
            run_task(partial(extractor, tagger, input_path), extractor_callback)


def extractor(tagger, input_path):
    # Create a temporary file with AcousticBrainz output
    output_file = NamedTemporaryFile("w", suffix=".json")
    output_file.close()  # close file to ensure other processes can write to it

    extractor = tagger.ab_extractor.get()
    if not extractor:
        return (output_file.name, -1, "no extractor found")

    # Call the features extractor and wait for it to finish
    try:
        return_code, stdout, stderr = run_executable(extractor.path, input_path, output_file.name)
        results = (output_file.name, return_code, stdout+stderr)
    except (FileNotFoundError, PermissionError) as e:
        # this can happen if AcousticBrainz extractor was removed or its permissions changed
        return (output_file.name, -1, str(e))

    # Add feature extractor sha to the output features file
    try:
        with open(output_file.name, "r+", encoding="utf-8") as f:
            features = json.load(f)
            features["metadata"]["version"]["essentia_build_sha"] = extractor.sha
            f.seek(0)
            json.dump(features, f, indent=4)
    except FileNotFoundError:
        pass

    # Return task results to the main thread (search for extractor_callback/ab_extractor_callback)
    return results


def ab_submit_features(tagger, file):
    # If file is not a duplicate and was previously extracted, we now load the features file
    with open(file.acousticbrainz_features_file, "r", encoding="utf-8") as f:
        features = json.load(f)

    try:
        musicbrainz_recordingid = features['metadata']['tags']['musicbrainz_trackid'][0]
    except KeyError:
        musicbrainz_recordingid = None

    # Check if extracted recording id exists and matches the current file (recording ID may have been merged with others)
    if not musicbrainz_recordingid or musicbrainz_recordingid != file.metadata['musicbrainz_recordingid']:
        # If it doesn't, skip the submission
        log.debug("AcousticBrainz features recording ID does not match the file metadata: %s" % file.filename)
        submit_features_callback(file, None, None, True)
        return

    # Submit features to the server
    tagger.webservice.post(
        host=ACOUSTICBRAINZ_HOST,
        port=ACOUSTICBRAINZ_PORT,
        path="/%s/low-level" % musicbrainz_recordingid,
        data=json.dumps(features),
        handler=partial(submit_features_callback, file),
        priority=True,
        important=False,
        mblogin=False,
        parse_response_type="json"
    )


def submit_features_callback(file, data, http, error):
    # Check if features submission succeeded or not
    if not error:
        file.acousticbrainz_is_duplicate = True
        os.remove(file.acousticbrainz_features_file)
        file.acousticbrainz_features_file = None
        log.debug("AcousticBrainz features were successfully submitted: %s" % file.filename)
    else:
        file.acousticbrainz_error = True
        log.debug("AcousticBrainz features were not submitted: %s" % file.filename)
    file.update()
