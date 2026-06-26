"""
QuantumPlay — Moteur de lecture FFmpeg
Gère la lecture audio/vidéo via subprocess ffplay et ffprobe
"""

import os
import re
import json
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable, List, Dict


# ---------------------------------------------------------------------------
# Détection FFmpeg
# ---------------------------------------------------------------------------
def _find_ffmpeg() -> tuple[str, str]:
    """Retourne (ffmpeg_path, ffplay_path)"""
    for base in ('ffmpeg', 'ffplay'):
        try:
            result = subprocess.run(
                [base, '-version'],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                continue
        except FileNotFoundError:
            pass

    ffmpeg = 'ffmpeg'
    ffplay  = 'ffplay'
    ffprobe = 'ffprobe'

    # Sur Windows, chercher dans PATH ou dossier courant
    for candidate in [
        os.path.join(os.path.dirname(__file__), '..', 'bin', 'ffmpeg.exe'),
        r'C:\ffmpeg\bin\ffmpeg.exe',
    ]:
        if os.path.isfile(candidate):
            ffmpeg = candidate
            break

    return ffmpeg, ffplay


FFMPEG_BIN, FFPLAY_BIN = _find_ffmpeg()
FFPROBE_BIN = FFMPEG_BIN.replace('ffmpeg', 'ffprobe')


# ---------------------------------------------------------------------------
# Métadonnées via ffprobe
# ---------------------------------------------------------------------------
def probe_file(path: str) -> Dict:
    """Extrait les métadonnées d'un fichier via ffprobe."""
    try:
        result = subprocess.run(
            [
                FFPROBE_BIN, '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                str(path)
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}


def get_duration(path: str) -> float:
    """Retourne la durée en secondes, 0.0 si inconnue."""
    info = probe_file(path)
    try:
        return float(info['format']['duration'])
    except (KeyError, ValueError, TypeError):
        return 0.0


def get_media_info(path: str) -> Dict:
    """Retourne un dict structuré avec les infos clés du fichier."""
    info  = probe_file(path)
    fmt   = info.get('format', {})
    tags  = fmt.get('tags', {})
    streams = info.get('streams', [])

    audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
    video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)

    duration = 0.0
    try:
        duration = float(fmt.get('duration', 0))
    except (ValueError, TypeError):
        pass

    size = 0
    try:
        size = int(fmt.get('size', 0))
    except (ValueError, TypeError):
        pass

    bitrate = 0
    try:
        bitrate = int(fmt.get('bit_rate', 0)) // 1000
    except (ValueError, TypeError):
        pass

    result = {
        'duration': duration,
        'size':     size,
        'bitrate':  bitrate,
        'title':    tags.get('title', ''),
        'artist':   tags.get('artist', tags.get('ARTIST', '')),
        'album':    tags.get('album', tags.get('ALBUM', '')),
        'format':   fmt.get('format_name', '').split(',')[0].upper(),
        'is_video': video_stream is not None,
        'width':    video_stream.get('width', 0) if video_stream else 0,
        'height':   video_stream.get('height', 0) if video_stream else 0,
        'codec':    (audio_stream or video_stream or {}).get('codec_name', '').upper(),
        'sample_rate': int((audio_stream or {}).get('sample_rate', 0)),
    }
    return result


# ---------------------------------------------------------------------------
# Modèle Track
# ---------------------------------------------------------------------------
class Track:
    def __init__(self, path: str, info: Optional[Dict] = None):
        self.path      = str(path)
        self.filename  = Path(path).name
        self.ext       = Path(path).suffix.lstrip('.').upper()
        self._info     = info or {}
        self.fav       = False

        # Champs remplis après probe
        self.title     = self._info.get('title') or Path(path).stem
        self.artist    = self._info.get('artist') or '—'
        self.album     = self._info.get('album')  or '—'
        self.duration  = self._info.get('duration', 0.0)
        self.size      = self._info.get('size', 0)
        self.bitrate   = self._info.get('bitrate', 0)
        self.format    = self._info.get('format') or self.ext
        self.is_video  = self._info.get('is_video', False)
        self.width     = self._info.get('width', 0)
        self.height    = self._info.get('height', 0)
        self.codec     = self._info.get('codec', '—')
        self.sample_rate = self._info.get('sample_rate', 0)

    @property
    def emoji(self) -> str:
        return '🎬' if self.is_video else '🎵'

    @property
    def duration_str(self) -> str:
        if not self.duration:
            return '—:——'
        s = int(self.duration)
        return f'{s // 60}:{s % 60:02d}'

    @property
    def size_str(self) -> str:
        if not self.size:
            return '—'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024:
                return f'{self.size:.1f} {unit}'
            self.size /= 1024
        return f'{self.size:.1f} TB'

    def __repr__(self):
        return f'<Track {self.title!r}>'


# ---------------------------------------------------------------------------
# Lecteur FFmpeg principal
# ---------------------------------------------------------------------------
class FFmpegEngine:
    """
    Moteur de lecture basé sur ffplay (subprocess).
    ffplay gère la fenêtre vidéo nativement.
    Pour l'audio seul, on utilise ffplay en mode sans fenêtre.
    """

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

        # État
        self.current_track: Optional[Track] = None
        self.is_playing = False
        self.position   = 0.0      # secondes
        self.duration   = 0.0
        self.volume     = 75       # 0..100
        self.muted      = False
        self._start_time = 0.0
        self._seek_offset = 0.0

        # EQ (gains en dB par fréquence)
        self.eq_gains: Dict[int, float] = {}

        # Callbacks
        self.on_track_end:      Optional[Callable] = None
        self.on_position_update: Optional[Callable] = None  # (pos, dur)
        self.on_state_change:   Optional[Callable] = None

        # Thread de suivi progression
        self._progress_thread: Optional[threading.Thread] = None
        self._stop_progress = threading.Event()

    # -----------------------------------------------------------------------
    # Lecture
    # -----------------------------------------------------------------------
    def play(self, track: Track, seek: float = 0.0):
        """Lance la lecture d'une piste."""
        self.stop()
        self.current_track = track
        self.duration       = track.duration
        self._seek_offset   = seek

        cmd = self._build_ffplay_cmd(track, seek)

        with self._lock:
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True
                )
            except FileNotFoundError:
                raise RuntimeError(
                    'ffplay introuvable. Installe FFmpeg et assure-toi '
                    "qu'il est dans le PATH système."
                )

        self.is_playing   = True
        self._start_time  = time.time() - seek
        self.position     = seek

        # Démarrer le suivi de progression
        self._stop_progress.clear()
        self._progress_thread = threading.Thread(
            target=self._progress_loop, daemon=True
        )
        self._progress_thread.start()

        if self.on_state_change:
            self.on_state_change(True)

    def _build_ffplay_cmd(self, track: Track, seek: float) -> List[str]:
        """Construit la commande ffplay."""
        vol_val = 0 if self.muted else int(self.volume)

        cmd = [FFPLAY_BIN, '-nodisp' if not track.is_video else '']
        cmd = [c for c in cmd if c]  # enlever chaînes vides

        cmd += [
            '-autoexit',
            '-volume', str(vol_val),
        ]

        if seek > 0:
            cmd += ['-ss', str(seek)]

        # Filtre EQ si des gains sont définis
        eq_filter = self._build_eq_filter()
        if eq_filter:
            cmd += ['-af', eq_filter]

        cmd += [track.path]
        return cmd

    def _build_eq_filter(self) -> str:
        """Construit le filtre FFmpeg equalizer= pour les bandes actives."""
        parts = []
        for freq, gain in self.eq_gains.items():
            if abs(gain) > 0.05:
                parts.append(f'equalizer=f={freq}:t=o:w=1:g={gain:.1f}')
        return ','.join(parts)

    # -----------------------------------------------------------------------
    # Contrôles
    # -----------------------------------------------------------------------
    def pause(self):
        """Met en pause (redémarre avec seek conservé)."""
        if not self.is_playing:
            return
        self.position = self._current_position()
        self._stop_progress.set()
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
        self.is_playing = False
        if self.on_state_change:
            self.on_state_change(False)

    def resume(self):
        """Reprend la lecture à la position sauvegardée."""
        if self.is_playing or not self.current_track:
            return
        self.play(self.current_track, seek=self.position)

    def toggle_play(self):
        if self.is_playing:
            self.pause()
        else:
            self.resume()

    def stop(self):
        """Arrête complètement la lecture."""
        self._stop_progress.set()
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            self._proc = None
        self.is_playing = False
        self.position   = 0.0
        if self.on_state_change:
            self.on_state_change(False)

    def seek(self, seconds: float):
        """Cherche une position (relance ffplay avec -ss)."""
        if not self.current_track:
            return
        self.play(self.current_track, seek=max(0.0, seconds))

    def seek_relative(self, delta: float):
        self.seek(self._current_position() + delta)

    def set_volume(self, value: int):
        """Volume 0..100. Relance si en cours."""
        self.volume = max(0, min(100, value))
        if self.is_playing and self.current_track:
            pos = self._current_position()
            self.play(self.current_track, seek=pos)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.is_playing and self.current_track:
            pos = self._current_position()
            self.play(self.current_track, seek=pos)

    def set_eq_gain(self, freq: int, gain: float):
        """Ajuste un gain EQ et relance si nécessaire."""
        self.eq_gains[freq] = gain
        if self.is_playing and self.current_track:
            pos = self._current_position()
            self.play(self.current_track, seek=pos)

    # -----------------------------------------------------------------------
    # Export / Conversion
    # -----------------------------------------------------------------------
    def export_mp3(self, track: Track, output_path: str,
                   progress_cb: Optional[Callable] = None):
        """Convertit en MP3 192k."""
        cmd = [
            FFMPEG_BIN, '-y',
            '-i', track.path,
            '-vn', '-ar', '44100', '-ac', '2',
            '-b:a', '192k',
            output_path
        ]
        self._run_export(cmd, track.duration, progress_cb)

    def export_mp4(self, track: Track, output_path: str,
                   progress_cb: Optional[Callable] = None):
        """Convertit en MP4 (copie stream si possible)."""
        cmd = [
            FFMPEG_BIN, '-y',
            '-i', track.path,
            '-c:v', 'copy', '-c:a', 'aac',
            '-movflags', '+faststart',
            output_path
        ]
        self._run_export(cmd, track.duration, progress_cb)

    def _run_export(self, cmd: List[str], duration: float,
                    progress_cb: Optional[Callable]):
        """Exécute une commande d'export en lisant la progression."""
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True, bufsize=1
        )
        time_re = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
        for line in process.stderr:
            if progress_cb and duration:
                m = time_re.search(line)
                if m:
                    h, mn, s = m.groups()
                    elapsed = int(h)*3600 + int(mn)*60 + float(s)
                    progress_cb(min(1.0, elapsed / duration))
        process.wait()
        if process.returncode not in (0, 1):
            raise RuntimeError(f'Export FFmpeg échoué (code {process.returncode})')
        if progress_cb:
            progress_cb(1.0)

    # -----------------------------------------------------------------------
    # Interne
    # -----------------------------------------------------------------------
    def _current_position(self) -> float:
        if not self.is_playing:
            return self.position
        elapsed = time.time() - self._start_time
        return min(self._seek_offset + elapsed, self.duration or 1e9)

    def _progress_loop(self):
        """Thread de suivi : appelle on_position_update régulièrement."""
        while not self._stop_progress.is_set():
            with self._lock:
                proc = self._proc

            if proc is None or proc.poll() is not None:
                # Le processus s'est terminé
                if self.is_playing:
                    self.is_playing = False
                    self.position = 0.0
                    if self.on_state_change:
                        self.on_state_change(False)
                    if self.on_track_end:
                        self.on_track_end()
                break

            pos = self._current_position()
            self.position = pos
            if self.on_position_update and self.duration:
                self.on_position_update(pos, self.duration)

            self._stop_progress.wait(timeout=0.25)


# ---------------------------------------------------------------------------
# Queue de lecture
# ---------------------------------------------------------------------------
class PlayQueue:
    def __init__(self):
        self.tracks:   List[Track] = []
        self.current:  int = 0
        self.shuffle:  bool = False
        self.repeat:   str = 'off'   # 'off' | 'all' | 'one'
        self._history: List[int] = []

    def add(self, track: Track):
        self.tracks.append(track)

    def add_many(self, tracks: List[Track]):
        self.tracks.extend(tracks)

    def remove(self, index: int):
        if 0 <= index < len(self.tracks):
            self.tracks.pop(index)
            if self.current >= len(self.tracks):
                self.current = max(0, len(self.tracks) - 1)

    def clear(self):
        self.tracks.clear()
        self.current = 0
        self._history.clear()

    def current_track(self) -> Optional[Track]:
        if self.tracks:
            return self.tracks[self.current]
        return None

    def next(self) -> Optional[Track]:
        if not self.tracks:
            return None
        if self.repeat == 'one':
            return self.tracks[self.current]
        if self.shuffle:
            import random
            candidates = [i for i in range(len(self.tracks)) if i != self.current]
            self.current = random.choice(candidates) if candidates else self.current
        else:
            if self.current < len(self.tracks) - 1:
                self.current += 1
            elif self.repeat == 'all':
                self.current = 0
            else:
                return None
        return self.tracks[self.current]

    def prev(self) -> Optional[Track]:
        if not self.tracks:
            return None
        if self.current > 0:
            self.current -= 1
        elif self.repeat == 'all':
            self.current = len(self.tracks) - 1
        return self.tracks[self.current]

    def go_to(self, index: int) -> Optional[Track]:
        if 0 <= index < len(self.tracks):
            self.current = index
            return self.tracks[index]
        return None

    @property
    def count(self) -> int:
        return len(self.tracks)