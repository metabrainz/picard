# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Laurent Monin
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

import sys
import math
import time

from collections import defaultdict
from picard import log

# ============================================================================
# Throttling/congestion avoidance
# ============================================================================

# Throttles requests to a given hostkey by assigning a minimum delay between
# requests in milliseconds.
#

# Plugins may assign limits to their associated service(s) like so:
#
# >>> from picard.webservice import ratecontrol
# >>> ratecontrol.set_minimum_delay(('myservice.org', 80), 100)  # 10 requests/second


# Minimun delay for the given hostkey (in milliseconds), can be set using
# set_minimum_delay()
REQUEST_DELAY_MINIMUM = defaultdict(lambda: 1000)

# Current delay (adaptive) between requests to a given hostkey.
REQUEST_DELAY = defaultdict(lambda: 1000)  # Conservative initial value.

# Determines delay during exponential backoff phase.
REQUEST_DELAY_EXPONENT = defaultdict(lambda: 0)

# Unacknowledged request counter.
#
# Bump this when handing a request to QNetworkManager and trim when receiving
# a response.
CONGESTION_UNACK = defaultdict(lambda: 0)

# Congestion window size in terms of unacked requests.
#
# We're allowed to send up to `int(this)` many requests at a time.
CONGESTION_WINDOW_SIZE = defaultdict(lambda: 1.0)

# Slow start threshold.
#
# After placing this many unacknowledged requests on the wire, switch from
# slow start to congestion avoidance.  (See `_adjust_throttle`.)  Initialized
# upon encountering a temporary error.
CONGESTION_SSTHRESH = defaultdict(lambda: 0)

# Storage of last request times per host key
LAST_REQUEST_TIMES = defaultdict(lambda: 0)


def set_minimum_delay(hostkey, delay_ms):
    """Set the minimun delay between requests
            hostkey is an unique key, for example (host, port)
            delay_ms is the delay in milliseconds
    """
    REQUEST_DELAY_MINIMUM[hostkey] = delay_ms


def current_delay(hostkey):
    """Returns the current delay (adaptive) between requests for this hostkey
            hostkey is an unique key, for example (host, port)
    """
    return REQUEST_DELAY[hostkey]


def get_delay_to_next_request(hostkey):
    """Calculate delay to next request to hostkey (host, port)
       returns a tuple (wait, delay) where:
           wait is True if a delay is needed
           delay is the delay in milliseconds to next request
    """
    if CONGESTION_UNACK[hostkey] >= int(CONGESTION_WINDOW_SIZE[hostkey]):
        # We've maxed out the number of requests to `hostkey`, so wait
        # until responses begin to come back.  (See `_timer_run_next_task`
        # strobe in `_handle_reply`.)
        return (True, sys.maxsize)

    interval = REQUEST_DELAY[hostkey]
    if not interval:
        log.debug("%s: Starting another request without delay", hostkey)
        return (False, 0)
    last_request = LAST_REQUEST_TIMES[hostkey]
    if not last_request:
        log.debug("%s: First request", hostkey)
        _remember_request_time(hostkey)  # set it on first run
        return (False, interval)
    elapsed = (time.time() - last_request) * 1000
    if elapsed >= interval:
        log.debug("%s: Last request was %d ms ago, starting another one", hostkey, elapsed)
        return (False, interval)
    delay = int(math.ceil(interval - elapsed))
    log.debug("%s: Last request was %d ms ago, waiting %d ms before starting another one",
              hostkey, elapsed, delay)
    return (True, delay)


def _remember_request_time(hostkey):
    if REQUEST_DELAY[hostkey]:
        LAST_REQUEST_TIMES[hostkey] = time.time()


def increment_requests(hostkey):
    """Store the request time for this hostkey, and increment counter
       It has to be called on each request
    """
    _remember_request_time(hostkey)
    # Increment the number of unack'd requests on sending a new one
    CONGESTION_UNACK[hostkey] += 1
    log.debug("%s: Incrementing requests to: %d", hostkey, CONGESTION_UNACK[hostkey])


def decrement_requests(hostkey):
    """Decrement counter, it has to be called on each reply
    """
    assert(CONGESTION_UNACK[hostkey] > 0)
    CONGESTION_UNACK[hostkey] -= 1
    log.debug("%s: Decrementing requests to: %d", hostkey, CONGESTION_UNACK[hostkey])


def copy_minimal_delay(from_hostkey, to_hostkey):
    """Copy minimal delay from one hostkey to another
        Useful for redirections
    """
    if (from_hostkey in REQUEST_DELAY_MINIMUM
            and to_hostkey not in REQUEST_DELAY_MINIMUM):
        REQUEST_DELAY_MINIMUM[to_hostkey] = REQUEST_DELAY_MINIMUM[from_hostkey]
        log.debug("%s: Copy minimun delay from %s, setting it to %dms",
                  to_hostkey, from_hostkey, REQUEST_DELAY_MINIMUM[to_hostkey])


def adjust(hostkey, slow_down):
    """Adjust `REQUEST` and `CONGESTION` metrics when a HTTP request completes.

            Args:
                    hostkey: `(host, port)`.
                    slow_down: `True` if we encountered intermittent server trouble
                    and need to slow down.
    """
    if slow_down:
        _slow_down(hostkey)
    elif CONGESTION_UNACK[hostkey] <= CONGESTION_WINDOW_SIZE[hostkey]:
        # not in backoff phase anymore
        _out_of_backoff(hostkey)


def _slow_down(hostkey):
    # Backoff exponentially until ~30 seconds between requests.
    delay = max(pow(2, REQUEST_DELAY_EXPONENT[hostkey]) * 1000,
                REQUEST_DELAY_MINIMUM[hostkey])

    REQUEST_DELAY_EXPONENT[hostkey] = min(
        REQUEST_DELAY_EXPONENT[hostkey] + 1, 5)

    # Slow start threshold is ~1/2 of the window size up until we saw
    # trouble.  Shrink the new window size back to 1.
    CONGESTION_SSTHRESH[hostkey] = int(CONGESTION_WINDOW_SIZE[hostkey] / 2.0)
    CONGESTION_WINDOW_SIZE[hostkey] = 1.0

    log.debug(
        '%s: slowdown; delay: %dms -> %dms; ssthresh: %d; cws: %.3f',
        hostkey,
        REQUEST_DELAY[hostkey],
        delay,
        CONGESTION_SSTHRESH[hostkey],
        CONGESTION_WINDOW_SIZE[hostkey]
    )

    REQUEST_DELAY[hostkey] = delay


def _out_of_backoff(hostkey):
    REQUEST_DELAY_EXPONENT[hostkey] = 0  # Coming out of backoff, so reset.

    # Shrink the delay between requests with each successive reply to
    # converge on maximum throughput.
    delay = max(int(REQUEST_DELAY[hostkey] / 2),
                REQUEST_DELAY_MINIMUM[hostkey])

    cws = CONGESTION_WINDOW_SIZE[hostkey]
    sst = CONGESTION_SSTHRESH[hostkey]

    if sst and cws >= sst:
        # Analogous to TCP's congestion avoidance phase.  Window growth is linear.
        phase = 'congestion avoidance'
        cws = cws + (1.0 / cws)
    else:
        # Analogous to TCP's slow start phase.  Window growth is exponential.
        phase = 'slow start'
        cws += 1

    if (REQUEST_DELAY[hostkey] != delay
        or CONGESTION_WINDOW_SIZE[hostkey] != cws):
        log.debug(
            '%s: oobackoff; delay: %dms -> %dms; %s; window size %.3f -> %.3f',
            hostkey,
            REQUEST_DELAY[hostkey],
            delay,
            phase,
            CONGESTION_WINDOW_SIZE[hostkey],
            cws
        )

        CONGESTION_WINDOW_SIZE[hostkey] = cws
        REQUEST_DELAY[hostkey] = delay
