# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018, 2020-2021, 2023-2024 Laurent Monin
# Copyright (C) 2018-2023, 2026 Philipp Wolfer
# Copyright (C) 2026 metaisfacil
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from picard import PICARD_VERSION_STR
from picard.config import get_config
from picard.const import (
    ACOUSTID_KEY,
    ACOUSTID_URL,
)
from picard.util import encoded_queryargs
from picard.webservice import ratecontrol

from .apihelper import APIHelper


ratecontrol.set_minimum_delay_for_url(ACOUSTID_URL, 333)


class AcoustIdAPIHelper(APIHelper):
    client_key = ACOUSTID_KEY
    client_version = PICARD_VERSION_STR

    def __init__(self, webservice):
        super().__init__(webservice, base_url=ACOUSTID_URL)

    def _encode_acoustid_args(self, args):
        args['client'] = self.client_key
        args['clientversion'] = self.client_version
        args['format'] = 'json'
        return '&'.join((k + '=' + v for k, v in encoded_queryargs(args).items()))

    def query_acoustid(self, handler, **args):
        body = self._encode_acoustid_args(args)
        return self.post(
            "/lookup",
            body,
            handler,
            priority=False,
            important=False,
            mblogin=False,
            request_mimetype='application/x-www-form-urlencoded',
        )

    @staticmethod
    def _submissions_to_args(submissions):
        config = get_config()
        args = {'user': config.setting['acoustid_apikey']}
        for i, submission in enumerate(submissions):
            for key, value in submission.args.items():
                if value:
                    args[".".join((key, str(i)))] = value
        return args

    def submit_acoustid_fingerprints(self, submissions, handler):
        args = self._submissions_to_args(submissions)
        body = self._encode_acoustid_args(args)
        return self.post(
            "/submit",
            body,
            handler,
            priority=True,
            important=False,
            mblogin=False,
            request_mimetype='application/x-www-form-urlencoded',
        )
