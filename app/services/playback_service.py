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
    
    @property
    def current_track(self):
        return self.engine.current_track


    @property
    def position(self):
        return self.engine.position


    @property
    def duration(self):
        return self.engine.duration
    
    @property
    def on_track_end(self):
        return self.engine.on_track_end

    @on_track_end.setter
    def on_track_end(self, callback):
        self.engine.on_track_end = callback


    @property
    def on_position_update(self):
        return self.engine.on_position_update

    @on_position_update.setter
    def on_position_update(self, callback):
        self.engine.on_position_update = callback


    @property
    def on_state_change(self):
        return self.engine.on_state_change

    @on_state_change.setter
    def on_state_change(self, callback):
        self.engine.on_state_change = callback