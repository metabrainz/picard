from __future__ import annotations

"""WatchFolderManager

Überwacht vom Nutzer konfigurierte Verzeichnisse auf neue / geänderte Audiodateien
und importiert diese automatisch in Picard. Bei Bedarf wird anschließend der
Auto-Tag-Workflow ausgelöst (je nach Einstellungen).
"""

from pathlib import Path
import os
from typing import Iterable, Set, List

from PyQt6 import QtCore

from picard.config import get_config
from picard import log
from picard.util import is_hidden

# Sehr grobe Auswahl gängiger Audio-Extensions
AUDIO_EXTS: Set[str] = {
    ".mp3", ".flac", ".ogg", ".oga", ".m4a", ".mp4", ".aac", ".wav",
    ".aif", ".aiff", ".wma", ".opus",
}


class WatchFolderManager(QtCore.QObject):
    """Verwalte überwachte Ordner und löse Picard-Workflows bei Änderungen aus."""

    def __init__(self, tagger, paths: Iterable[str] | None = None):
        super().__init__(parent=tagger)
        self.tagger = tagger
        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_directory_changed)
        self.tagger.file_loaded.connect(self._on_file_loaded)
        self.tagger.file_updated.connect(self._on_file_updated)
        self._paths: Set[str] = set()
        self._paused = False
        if paths:
            for p in paths:
                self.add_path(p)

    # ------------------------------------------------------------------
    # Pfad-Management
    # ------------------------------------------------------------------

    def add_path(self, path: str):
        path = os.path.abspath(path)
        if path in self._paths:
            return
        if not os.path.isdir(path):
            log.warning("WatchFolder: %s ist kein Verzeichnis", path)
            return
        self._paths.add(path)
        self._watcher.addPath(path)
        log.info("WatchFolder: Überwache %s", path)

    def remove_path(self, path: str):
        path = os.path.abspath(path)
        if path not in self._paths:
            return
        self._paths.remove(path)
        self._watcher.removePath(path)
        log.info("WatchFolder: Entfernt %s", path)

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------

    def start(self):
        """Aktiviere die Überwachung aller registrierten Pfade."""
        if not self._paused:
            return
        self._watcher.addPaths(list(self._paths))
        self._paused = False

    def stop(self):
        """Pausiere die Überwachung (Pfadliste bleibt erhalten)."""
        if self._paused:
            return
        self._watcher.removePaths(list(self._paths))
        self._paused = True

    @property
    def running(self) -> bool:
        return not self._paused

    @property
    def paths(self) -> List[str]:
        return sorted(self._paths)

    # ------------------------------------------------------------------
    # Ereignis-Handling
    # ------------------------------------------------------------------

    def _on_directory_changed(self, directory: str):
        """Callback, wenn sich Inhalte im überwachten Verzeichnis ändern."""
        try:
            for entry in os.scandir(directory):
                if not entry.is_file():
                    continue
                if is_hidden(entry.path):
                    continue
                if self._is_audio_file(entry.path) and entry.path not in self.tagger.files:
                    log.info("WatchFolder: Neue Datei erkannt: %s", entry.path)
                    # Importiere Datei nach Picard (Target = None → Standard-Logik)
                    self.tagger.add_paths([entry.path])
        except OSError as exc:
            log.error("WatchFolder: Fehler beim Zugriff auf %s – %s", directory, exc)

    def _on_file_loaded(self, file):
        """Reagiert auf eine neu in Picard geladene Datei."""
        config = get_config()
        if not config or not config.setting["watch_folders_auto_tag"]:
            return
        if file.filename in self.tagger.files:
            log.info("WatchFolder: Starte Auto-Tagging für %s", file.filename)
            self.tagger.run_lookup_in_browser([file])

    def _on_file_updated(self, file):
        """Reagiert auf eine Aktualisierung einer Datei (z.B. nach Tagging)."""
        config = get_config()
        if not config or not config.setting["watch_folders_auto_save"]:
            return
        # Prüfen, ob die Datei aus einem Watch-Folder stammt (optional, aber sicherer)
        if any(file.filename.startswith(p) for p in self._paths):
            if file.is_modified() and not file.is_saving:
                log.info("WatchFolder: Starte Auto-Saving für %s", file.filename)
                self.tagger.save_files([file])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_audio_file(path: str) -> bool:
        return Path(path).suffix.lower() in AUDIO_EXTS 