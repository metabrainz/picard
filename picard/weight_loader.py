# Picard, the next-generation MusicBrainz tagger
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

from picard.matching import TieredWeights

# Weights for different elements when comparing a cluster to a release.
# Organized in 3 tiers:
#   Tier 1 (identifiers): high weights — exact matches dominate the score
#   Tier 2 (similarity): moderate weights — fuzzy matching core
#   Tier 3 (preferences): low weights — tie-breaking discriminators
CLUSTER_COMPARISON_WEIGHTS = {
    'identifiers': {
        'barcode': 28,
        'catno': 22,
    },
    'similarity': {
        'album': 17,
        'albumartist': 6,
        'date': 4,
        'totalalbumtracks': 5,
    },
    'preferences': {
        'format': 2,
        'releasecountry': 2,
        'releasetype': 10,
    },
}


class WeightLoader:
    def __init__(self):
        from picard.const import defaults
        self._config = None
        self.load_weights(defaults.DEFAULT_WEIGHTS)
        self._cached_config = defaults.DEFAULT_WEIGHTS

    @property
    def weights(self):
        if self._config is None:
            from picard.config import get_config
            self._config = get_config()
        if self._config.setting['user_defined_weights'] != self._cached_config:
            self._cached_config = self._config.setting['user_defined_weights']
            self.load_weights(self._config.setting['user_defined_weights'])
        return self._weights

    @property
    def cluster_weights(self) -> TieredWeights:
        if self._config is None:
            from picard.config import get_config
            self._config = get_config()
        if self._config.setting['user_defined_weights'] != self._cached_config:
            self._cached_config = self._config.setting['user_defined_weights']
            self.load_weights(self._config.setting['user_defined_weights'])
        return self._cluster_weights

    def _update_cluster_weights(self):
        weights = self._weights
        tmp = dict(CLUSTER_COMPARISON_WEIGHTS)

        for tag, weight in weights:
            if tag == "cataloguenumber":
                tmp["identifiers"]["catno"] = weight
            elif tag == "barcode":
                tmp["identifiers"]["barcode"] = weight
            elif tag == "album":
                tmp["similarity"]["album"] = weight
            elif tag == "albumartist":
                tmp["similarity"]["albumartist"] = weight
            elif tag == "date":
                tmp["similarity"]["date"] = weight
            else:
                # the rest go into preferences
                tmp["preferences"][tag] = weight
        self._cluster_weights = tmp

    def load_weights(self, weights_str, default_weights={}):
        tmp = dict(default_weights)
        for line in weights_str.split("\n"):
            (tag, weight) = line.strip().split(",")
            try:
                tmp[tag] = int(weight)
            except ValueError:
                continue
        self._weights = tuple(tmp.items())
        self._update_cluster_weights()


weight_loader = WeightLoader()
