"""
QuantumPlay

Playback Service

Responsable de toute la lecture multimédia.
"""

from engine.player import FFmpegEngine


class PlaybackService:
    """
    Service de lecture multimédia.
    """

    def __init__(self):
        self.engine = FFmpegEngine()

    def play(self, track):
        """Lance la lecture d'une piste."""
        self.engine.play(track)

    def pause(self):
        """Met en pause la lecture."""
        self.engine.pause()

    def stop(self):
        """Arrête la lecture."""
        self.engine.stop()

    def toggle_play(self):
        """Lecture / Pause."""
        self.engine.toggle_play()

    def set_volume(self, volume):
        """Modifie le volume."""
        self.engine.set_volume(volume)