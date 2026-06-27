"""
QuantumPlay

Playback Service

Responsable de toute la lecture multimédia.
"""

from engine.player import FFmpegEngine


class PlaybackService:
    """
    Service responsable de toute la lecture audio/vidéo.
    """

    def __init__(self):
        self.engine = FFmpegEngine()

    def play(self, track):
        self.engine.play(track)

    def pause(self):
        self.engine.pause()

    def stop(self):
        self.engine.stop()

    def resume(self):
        self.engine.resume()

    def seek(self, position):
        self.engine.seek(position)

    def set_volume(self, volume):
        self.engine.set_volume(volume)

    def toggle_mute(self):
        self.engine.toggle_mute()

    @property
    def is_playing(self):
        return self.engine.is_playing