"""
QuantumPlay — Bibliothèque multimédia
Scan, indexation et gestion des fichiers
"""

import os
import json
import threading
from pathlib import Path
from typing import List, Optional, Callable, Dict

from engine.player import Track, get_media_info


AUDIO_EXTS = {
    '.mp3', '.flac', '.wav', '.ogg', '.opus', '.m4a',
    '.aac', '.wma', '.aiff', '.ape', '.mpc', '.wv',
}
VIDEO_EXTS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv',
    '.webm', '.m4v', '.ts', '.m2ts', '.vob', '.ogv',
}
MEDIA_EXTS = AUDIO_EXTS | VIDEO_EXTS

STATE_FILE = Path.home() / '.quantumplay' / 'state.json'


class MediaLibrary:
    """Gère la bibliothèque de médias et les playlists."""

    def __init__(self):
        self.items:     List[Track] = []
        self.playlists: List[Dict]  = []
        self.history:   List[Dict]  = []
        self._lock = threading.Lock()

        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    # -----------------------------------------------------------------------
    # Ajout de fichiers
    # -----------------------------------------------------------------------
    def add_files(self, paths: List[str],
                  on_progress: Optional[Callable] = None) -> List[Track]:
        """Ajoute des fichiers, probe les métadonnées dans un thread."""
        new_tracks = []
        existing = {t.path for t in self.items}

        for i, path in enumerate(paths):
            if path in existing:
                continue
            ext = Path(path).suffix.lower()
            if ext not in MEDIA_EXTS:
                continue
            info = get_media_info(path)
            track = Track(path, info)
            with self._lock:
                self.items.append(track)
            new_tracks.append(track)
            existing.add(path)
            if on_progress:
                on_progress(i + 1, len(paths), track)

        self._save_state()
        return new_tracks

    def add_folder(self, folder_path: str,
                   on_progress: Optional[Callable] = None) -> List[Track]:
        """Scan récursif d'un dossier."""
        paths = []
        for root, _, files in os.walk(folder_path):
            for f in sorted(files):
                ext = Path(f).suffix.lower()
                if ext in MEDIA_EXTS:
                    paths.append(os.path.join(root, f))
        return self.add_files(paths, on_progress)

    def add_folder_async(self, folder_path: str,
                         on_track_added: Optional[Callable] = None,
                         on_done: Optional[Callable] = None):
        """Version asynchrone du scan dossier."""
        def _worker():
            tracks = self.add_folder(
                folder_path,
                on_progress=lambda i, t, track: on_track_added(track) if on_track_added else None
            )
            if on_done:
                on_done(tracks)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    # -----------------------------------------------------------------------
    # Filtrage / tri
    # -----------------------------------------------------------------------
    def filter(self, kind: str = 'all') -> List[Track]:
        with self._lock:
            items = list(self.items)
        if kind == 'audio':
            return [t for t in items if not t.is_video]
        if kind == 'video':
            return [t for t in items if t.is_video]
        if kind == 'favorites':
            return [t for t in items if t.fav]
        if kind == 'recent':
            return items[-20:][::-1]
        return items

    def remove(self, track: Track):
        with self._lock:
            if track in self.items:
                self.items.remove(track)
        self._save_state()

    def clear(self):
        with self._lock:
            self.items.clear()
        self._save_state()

    # -----------------------------------------------------------------------
    # Playlists
    # -----------------------------------------------------------------------
    def create_playlist(self, name: str) -> Dict:
        pl = {'id': f'pl_{id(name)}_{len(self.playlists)}',
              'name': name, 'tracks': []}
        self.playlists.append(pl)
        self._save_state()
        return pl

    def get_playlist(self, pl_id: str) -> Optional[Dict]:
        return next((p for p in self.playlists if p['id'] == pl_id), None)

    def add_to_playlist(self, pl_id: str, track: Track):
        pl = self.get_playlist(pl_id)
        if pl and track.path not in [t.get('path') for t in pl['tracks']]:
            pl['tracks'].append({'path': track.path, 'title': track.title})
            self._save_state()

    def delete_playlist(self, pl_id: str):
        self.playlists = [p for p in self.playlists if p['id'] != pl_id]
        self._save_state()

    # -----------------------------------------------------------------------
    # Historique
    # -----------------------------------------------------------------------
    def add_history(self, track: Track):
        from datetime import datetime
        entry = {
            'path':   track.path,
            'title':  track.title,
            'artist': track.artist,
            'format': track.format,
            'emoji':  track.emoji,
            'time':   datetime.now().strftime('%H:%M'),
            'date':   datetime.now().strftime('%Y-%m-%d'),
        }
        self.history.insert(0, entry)
        self.history = self.history[:200]   # max 200 entrées
        self._save_state()

    def grouped_history(self) -> List[Dict]:
        """Retourne l'historique groupé par date."""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        groups: Dict[str, List] = {}
        for entry in self.history:
            label = 'Aujourd\'hui' if entry['date'] == today else entry['date']
            groups.setdefault(label, []).append(entry)
        return [{'group': k, 'items': v} for k, v in groups.items()]

    # -----------------------------------------------------------------------
    # Persistance JSON
    # -----------------------------------------------------------------------
    def _save_state(self):
        try:
            data = {
                'library': [
                    {'path': t.path, 'fav': t.fav}
                    for t in self.items
                ],
                'playlists': self.playlists,
                'history':   self.history[:100],
            }
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_state(self):
        try:
            if not STATE_FILE.exists():
                return
            with open(STATE_FILE, encoding='utf-8') as f:
                data = json.load(f)

            # Recharger la bibliothèque (seulement les fichiers qui existent encore)
            for entry in data.get('library', []):
                path = entry.get('path', '')
                if path and Path(path).exists():
                    info  = get_media_info(path)
                    track = Track(path, info)
                    track.fav = entry.get('fav', False)
                    self.items.append(track)

            self.playlists = data.get('playlists', [])
            self.history   = data.get('history', [])
        except Exception:
            pass