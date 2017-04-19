PLUGIN_NAME = _(u'Re-order sides of a release')
PLUGIN_AUTHOR = u'David Mandelberg'
PLUGIN_DESCRIPTION = _(u"""\
  Split mediums and re-order sides to match side order rather than
  medium order. E.g., if a release has two mediums with track numbers
  <em>A1, A2, ..., D1, D2, ...</em> and <em>B1, B2, ..., C1, C2,
  ...</em>, this plugin will split the release into four mediums and
  reorder the new mediums so that the track numbers are <em>A1, A2,
  ..., B1, B2, ..., C1, C2, ..., D1, D2, ...</em>

  This is primarily intended to make vinyl records designed for record
  changers
  (https://en.wikipedia.org/wiki/Record_changer#Automatic_sequencing)
  play in the correct order.""")
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['1.3.0']

import collections

from picard.metadata import \
  register_album_metadata_processor, register_track_metadata_processor


# List of strings that represent the medium side of a track when the
# track number is one of these strings followed by digits. The order of
# this list specifies the order of the sides.
SIDE_PREFIXES = [
  'A',
  'B',
  'C',
  'D',
  'E',
  'F',
  'G',
  'H',
  'I',
  'J',
  'K',
  'L',
  'M',
  'N',
  'O',
  'P',
  'Q',
  'R',
  'S',
  'T',
  'U',
  'V',
  'W',
  'X',
  'Y',
  'Z',
  ]

# Map from release MBID to information that we can use to re-group and
# re-order the tracks. The per-release info (value of this map) is an
# OrderedDict mapping side name to a sequence of (discnumber of the
# side, first tracknumber of the side, last tracknumber of the side).
# The order of the OrderedDict specifies the intended order of the
# sides.
release_to_side_info = {}

def tracknumber_to_side(tracknumber):
  """Given a track "number", return the side, or None"""

  for side_prefix in SIDE_PREFIXES:
    if not tracknumber.startswith(side_prefix):
      continue

    number_in_side = tracknumber[len(side_prefix):]
    try:
      int(number_in_side)
    except ValueError:
      continue

    return side_prefix

  return None

def get_side_info(release):
  """Return side info (see release_to_side_info), or None if we don't
  want to reorder the sides."""

  side_info = collections.OrderedDict()

  for medium in release.medium_list[0].medium:
    current_side = None

    for track in medium.track_list[0].track:
      tracknumber = track.children['number'][0].text
      trackside = tracknumber_to_side(tracknumber)

      try:
        int_tracknumber = int(track.children['position'][0].text)
      except ValueError:
        # Non-integer tracknumber, so give up.
        return None

      if trackside is None:
        # If any track has no side information, we don't reorder
        # anything.
        return None

      if current_side is not None and current_side == trackside:
        # Another track of the same side as before, so just update the
        # last tracknumber for this side.
        if int_tracknumber > side_info[current_side][2]:
          side_info[current_side][2] = int_tracknumber
        continue

      # At this point, we're on the first track of a new side.

      current_side = trackside

      if current_side in side_info:
        # We've already seen this side somewhere else, so give up.
        return None

      try:
        side_info[current_side] = [
          int(medium.children['position'][0].text),
          int_tracknumber,
          int_tracknumber,
          ]
      except ValueError:
        # Non-integer position, so give up.
        return None

  # At this point, we know that all tracknumbers include side
  # information, and no sides appear in more than one place (every
  # side is contiguous).

  sides_in_order_of_appearance = list(side_info.keys())
  sides_in_intended_order = sorted(
    sides_in_order_of_appearance,
    key=lambda s: SIDE_PREFIXES.index(s),
    )
  if sides_in_order_of_appearance == sides_in_intended_order:
    # Sides are already in the right order, so we don't need to do
    # anything.
    return None

  # Re-order side_info to match the intended order.
  side_info_ordered = collections.OrderedDict()
  for side in sides_in_intended_order:
    side_info_ordered[side] = side_info[side]
  side_info = side_info_ordered

  return side_info

def find_side(side_info, metadata):
  """Given side info and track metadata, return the side that the
  track belongs to."""

  orig_discnumber = int(metadata['discnumber'])
  orig_tracknumber = int(metadata['tracknumber'])

  for side_item in side_info.iteritems():
    (
      side,
      (
        side_discnumber,
        side_first_tracknumber,
        side_last_tracknumber,
        ),
      ) = side_item

    if side_discnumber == orig_discnumber \
        and side_first_tracknumber <= orig_tracknumber \
        and orig_tracknumber <= side_last_tracknumber:
      return side

  raise RuntimeError('Unable to find side for track: ' + metadata)

def analyze_release(tagger, metadata, release):
  """Analyze a release to determine if its sides should be
  re-ordered"""

  side_info = get_side_info(release)
  if side_info is not None:
    release_to_side_info[metadata['musicbrainz_albumid']] = side_info

register_album_metadata_processor(analyze_release)

def reorder_sides(tagger, metadata, *args):
  """Re-order sides of a release, using the information in
  release_to_side_info."""

  if metadata['musicbrainz_albumid'] not in release_to_side_info:
    return

  side_info = release_to_side_info[metadata['musicbrainz_albumid']]
  all_sides = list(side_info.keys())

  side = find_side(side_info, metadata)
  side_first_tracknumber = side_info[side][1]
  side_last_tracknumber = side_info[side][2]

  metadata['totaldiscs'] = str(len(all_sides))
  metadata['discnumber'] = str(all_sides.index(side) + 1)

  metadata['totaltracks'] = \
    str(side_last_tracknumber - side_first_tracknumber + 1)
  metadata['tracknumber'] = \
    str(int(metadata['tracknumber']) - side_first_tracknumber + 1)

register_track_metadata_processor(reorder_sides)
