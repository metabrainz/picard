from __future__ import annotations

"""Hilfsfunktionen zur Generierung intelligenter Tag-Vorschläge.

Dieses Modul stellt aktuell eine einfache Heuristik bereit, um fehlende
Tags (Genre, Jahr, Sprache) aus den von MusicBrainz gelieferten Release-
Daten abzuleiten. Weitere Tags oder komplexere Logik können hier später
ergänzt werden.
"""

from typing import Dict, Any

from picard.util import extract_year_from_date

__all__ = [
    "generate_suggestions",
]


def _suggest_genre(release_node: Dict[str, Any]) -> str | None:
    """Gib die wahrscheinlichste Genre-Bezeichnung zurück.

    MusicBrainz liefert im Feld ``tags`` eine Liste mit ``name`` und
    ``count``. Wir wählen das Tag mit der höchsten Zählung.
    """
    tags = release_node.get("tags") or []
    if not tags:
        return None
    # Sortiere nach count (absteigend) und Tag-Name (deterministisch)
    tags_sorted = sorted(tags, key=lambda t: (-int(t.get("count", 0)), t.get("name", "")))
    return tags_sorted[0]["name"] if tags_sorted else None


def _suggest_year(release_node: Dict[str, Any]) -> str | None:
    """Versuche ein Jahr (YYYY) aus dem Release-Datum abzuleiten."""
    date_str: str | None = release_node.get("date")
    if not date_str:
        return None
    year = extract_year_from_date(date_str)
    return str(year) if year else None


def _suggest_language(release_node: Dict[str, Any]) -> str | None:
    """Schlage die Sprachkennung vor (ISO-639-3 Code)."""
    text_rep = release_node.get("text-representation") or {}
    lang = text_rep.get("language")
    return lang


def generate_suggestions(metadata_obj, release_node: Dict[str, Any]) -> Dict[str, str]:
    """Ermittle fehlende Tags und gib passende Vorschläge zurück.

    Args:
        metadata_obj: Das bereits erstellte ``Metadata``-Objekt des Albums.
        release_node: Der vollständige Release-JSON-Knoten von MusicBrainz.

    Returns:
        Dict[tag_name, vorgeschlagener_wert]
    """
    suggestions: Dict[str, str] = {}

    # Genre
    if not metadata_obj["genre"]:
        genre = _suggest_genre(release_node)
        if genre:
            suggestions["genre"] = genre

    # Jahr (date)
    if not metadata_obj["date"]:
        year = _suggest_year(release_node)
        if year:
            suggestions["date"] = year

    # Sprache (language)
    if not metadata_obj["language"]:
        language = _suggest_language(release_node)
        if language:
            suggestions["language"] = language

    return suggestions 