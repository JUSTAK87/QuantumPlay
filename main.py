"""
QuantumPlay — Lecteur multimédia Python/Kivy
Point d'entrée principal
"""

import os

# Utiliser ANGLE au lieu d'OpenGL Desktop
os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"
os.environ.setdefault('KIVY_NO_ENV_CONFIG', '0')

from kivy.config import Config
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '780')
Config.set('graphics', 'minimum_width', '960')
Config.set('graphics', 'minimum_height', '620')
Config.set('graphics', 'resizable', '1')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from ui.theme import THEME
from ui.main_window import QuantumPlayLayout


class QuantumPlayApp(App):
    title = 'QuantumPlay'
    icon  = 'assets/logo.ico'

    def build(self):
        Window.clearcolor = get_color_from_hex(THEME['bg_deep'])
        Window.bind(on_key_down=self._on_key_down)
        self.root_layout = QuantumPlayLayout()
        return self.root_layout

    def _on_key_down(self, window, key, scancode, codepoint, modifier):
        """Raccourcis clavier globaux"""
        layout = self.root_layout
        # Espace → lecture/pause
        if key == 32:
            layout.player_bar.toggle_play()
            return True
        # Flèche droite → piste suivante
        if key == 275:
            layout.player_bar.next_track()
            return True
        # Flèche gauche → piste précédente
        if key == 276:
            layout.player_bar.prev_track()
            return True
        # M → mute
        if codepoint == 'm':
            layout.player_bar.toggle_mute()
            return True
        return False

    def on_stop(self):
        """Nettoyage à la fermeture"""
        try:
            self.root_layout.engine.stop()
        except Exception:
            pass


if __name__ == '__main__':
    QuantumPlayApp().run()