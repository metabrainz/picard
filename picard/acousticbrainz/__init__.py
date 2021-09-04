# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright 2014 Music Technology Group - Universitat Pompeu Fabra
# Copyright 2020-2021 Gabriel Ferreira
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


_acousticbrainz_extractor = None
_acousticbrainz_extractor_sha = None
ratecontrol.set_minimum_delay((ACOUSTICBRAINZ_HOST, ACOUSTICBRAINZ_PORT), 1000)


def get_extractor(config=None):
    if not config:
        config = get_config()
    extractor_path = config.setting["acousticbrainz_extractor"]
    if not extractor_path:
        extractor_path = find_extractor()
    else:
        extractor_path = find_executable(extractor_path)
    return extractor_path


def find_extractor():
    return find_executable(*EXTRACTOR_NAMES)


def ab_available():
    config = get_config()
    return config.setting["use_acousticbrainz"] and _acousticbrainz_extractor_sha is not None


def ab_check_version(extractor):
    extractor_path = find_executable(extractor)
    return check_extractor_version(extractor_path)


def ab_setup_extractor():
    global _acousticbrainz_extractor, _acousticbrainz_extractor_sha
    config = get_config()
    if config.setting["use_acousticbrainz"]:
        acousticbrainz_extractor = get_extractor(config)
        log.debug("Checking up AcousticBrainz availability")
        if acousticbrainz_extractor:
            sha = precompute_extractor_sha(acousticbrainz_extractor)
            version = check_extractor_version(acousticbrainz_extractor)
            if version:
                _acousticbrainz_extractor = acousticbrainz_extractor
                _acousticbrainz_extractor_sha = sha
                log.debug("AcousticBrainz is available: version %s - sha1 %s" % (version, sha))
                return version
        _acousticbrainz_extractor = None
        _acousticbrainz_extractor_sha = None
        log.warning("AcousticBrainz is not available")
    return None


def ab_feature_extraction(tagger, recording_id, input_path, extractor_callback):
    # Fetch existing features from AB server to check for duplicates before extracting
    tagger.webservice.get(
        host=ACOUSTICBRAINZ_HOST,
        port=ACOUSTICBRAINZ_PORT,
        path="/%s/low-level" % recording_id,
        handler=partial(run_extractor, input_path, extractor_callback),
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
        ab_submit_features(tagger, file, ab_metadata_file)
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


def run_extractor(input_path, extractor_callback, response, reply, error, main_thread=False):
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
            extractor_callback(extractor(input_path), None)
        else:
            # Run extractor on a different thread and call the callback when done
            run_task(partial(extractor, input_path), extractor_callback)


def extractor(input_path):
    # Create a temporary file with AcousticBrainz output
    output_file = NamedTemporaryFile("w", suffix=".json")
    output_file.close()  # close file to ensure other processes can write to it

    # Call the features extractor and wait for it to finish
    try:
        return_code, stdout, stderr = run_executable(_acousticbrainz_extractor, input_path, output_file.name)
        results = (output_file.name, return_code, stdout+stderr)
    except (FileNotFoundError, PermissionError) as e:
        # this can happen if _acousticbrainz_extractor was removed or its permissions changed
        return (output_file.name, -1, str(e))

    # Add feature extractor sha to the output features file
    try:
        with open(output_file.name, "r+", encoding="utf-8") as f:
            features = json.load(f)
            features["metadata"]["version"]["essentia_build_sha"] = _acousticbrainz_extractor_sha
            f.seek(0)
            json.dump(features, f, indent=4)
    except FileNotFoundError:
        pass

    # Return task results to the main thread (search for extractor_callback/ab_extractor_callback)
    return results


def ab_submit_features(tagger, file, features_file):
    # If file is not a duplicate and was previously extracted, we now load the features file
    with open(features_file, "r", encoding="utf-8") as f:
        features = json.load(f)

    # Check if extracted recording id matches the current file (recording ID may have been merged with others)
    if features['metadata']['tags']['musicbrainz_trackid'][0] != file.metadata['musicbrainz_recordingid']:
        # If it doesn't, skip the submission
        log.debug("AcousticBrainz features recordingId do not match the file metadata: %s" % file.filename)
        submit_features_callback(file, None, None, True)
        return

    featstr = json.dumps(features)

    # Submit features to the server
    tagger.webservice.post(
        host=ACOUSTICBRAINZ_HOST,
        port=ACOUSTICBRAINZ_PORT,
        path="/%s/low-level" % file.metadata["musicbrainz_recordingid"],
        data=featstr,
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
