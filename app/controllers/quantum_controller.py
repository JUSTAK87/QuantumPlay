"""
QuantumPlay

Quantum Controller

Chef d'orchestre de l'application.
Il coordonne les services sans contenir directement
la logique métier.
"""

from app.services.playback_service import PlaybackService
from app.services.library_service import LibraryService
from app.services.notification_service import NotificationService
from app.services.history_service import HistoryService
from app.services.search_service import SearchService
from app.services.settings_service import SettingsService


class QuantumController:
    """
    Contrôleur principal de QuantumPlay.
    Coordonne les services et fait le lien avec l'interface.
    """

    def __init__(self):
        self.playback = PlaybackService()
        self.library = LibraryService()
        self.notifications = NotificationService()
        self.history = HistoryService()
        self.search = SearchService()
        self.settings = SettingsService()

    def play_track(self, track):
        self.playback.play(track)

    def pause(self):
        self.playback.pause()

    def stop(self):
        self.playback.stop()

    def resume(self):
        self.playback.resume()