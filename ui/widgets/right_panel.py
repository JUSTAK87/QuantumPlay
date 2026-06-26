from kivy.uix.boxlayout import BoxLayout


class RightPanel(BoxLayout):
    """Placeholder de panneau droit pour permettre le démarrage de l’interface."""

    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', **kw)
        self.main = main

    def refresh_queue(self):
        return None

    def update_progress(self, pos, dur):
        return None

    def set_now_playing(self, track):
        return None
