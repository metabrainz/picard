#!/usr/bin/env python3
"""Refresh corpus fixtures from MusicBrainz.

The single source of truth is corpus/releases.tsv (MBID<tab>description).
This script fetches release JSON from the MB API and caches it locally.

Usage:
    python scripts/eval_matching/refresh_corpus.py          # refresh all
    python scripts/eval_matching/refresh_corpus.py --add ID # add a new release
"""

import argparse
import json
from pathlib import Path
import sys
import time
import urllib.request


CORPUS_DIR = Path(__file__).parent / "corpus"
RELEASES_TSV = CORPUS_DIR / "releases.tsv"
MB_API = "https://musicbrainz.org/ws/2/release"
MB_INC = "artist-credits+media+recordings+release-groups"
USER_AGENT = "PicardEvalMatching/1.0 (https://github.com/metabrainz/picard)"
REQUEST_DELAY = 1.1  # seconds between requests (MB rate limit)


def load_registry():
    """Load releases.tsv → list of (mbid, description)."""
    entries = []
    if RELEASES_TSV.exists():
        for line in RELEASES_TSV.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                mbid, _, desc = line.partition("\t")
                entries.append((mbid.strip(), desc.strip()))
    return entries


def append_to_registry(mbid, description):
    """Append a new entry to releases.tsv."""
    with open(RELEASES_TSV, "a", encoding="utf-8") as f:
        f.write(f"{mbid}\t{description}\n")


def fetch_release(release_id):
    """Fetch a release from the MusicBrainz API."""
    url = f"{MB_API}/{release_id}?inc={MB_INC}&fmt=json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def save_release(data):
    """Save release JSON to corpus/, named by MBID prefix."""
    path = CORPUS_DIR / f"eval_release_{data['id'][:8]}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return path


def refresh_all():
    """Re-fetch all releases listed in releases.tsv."""
    entries = load_registry()
    print(f"Refreshing {len(entries)} releases from releases.tsv...")
    for i, (mbid, desc) in enumerate(entries):
        try:
            data = fetch_release(mbid)
            path = save_release(data)
            tracks = sum(len(m.get("tracks", [])) for m in data.get("media", []))
            print(f"  [{i + 1}/{len(entries)}] {path.name} - {desc} ({tracks} tracks)")
        except Exception as e:
            print(f"  [{i + 1}/{len(entries)}] FAILED {mbid} ({desc}): {e}", file=sys.stderr)
        if i < len(entries) - 1:
            time.sleep(REQUEST_DELAY)


def add_release(release_id):
    """Fetch a release, save it, and append to releases.tsv."""
    # Check if already in registry
    existing = {mbid for mbid, _ in load_registry()}
    if release_id in existing:
        print(f"Already in registry: {release_id}", file=sys.stderr)
        sys.exit(1)

    data = fetch_release(release_id)
    path = save_release(data)

    # Build description from fetched data
    ac = data.get("artist-credit", [])
    artist = "".join(c.get("name", "") + c.get("joinphrase", "") for c in ac)
    title = data["title"]
    date = data.get("date", "?")
    country = data.get("country", "?")
    tracks = sum(len(m.get("tracks", [])) for m in data.get("media", []))
    desc = f"{artist} - {title} {date} {country} ({tracks} tracks)"

    append_to_registry(release_id, desc)
    print(f"Added: {path.name}")
    print(f"  {desc}")
    print(f"  Appended to {RELEASES_TSV.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--add", metavar="RELEASE_ID", help="Fetch a new release and add to corpus + registry")
    args = parser.parse_args()

    if args.add:
        add_release(args.add)
    else:
        refresh_all()


if __name__ == "__main__":
    main()
