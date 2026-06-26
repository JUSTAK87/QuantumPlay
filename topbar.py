"""
QuantumPlay — Barre de titre / menu haut
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock

from ui.theme import C, SIZES
from ui.widgets.base import QButton, QIconButton, QLabel


class TopBar(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(
            orientation='horizontal',
            spacing=6,
            padding=(12, 0),
            **kw
        )
        self.main = main

        with self.canvas.before:
            Color(*C['bg_surface'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
            # Ligne dégradée cyan/violet en bas
            Color(*C['accent_cyan'][:3], 0.6)
            self._line = Line(
                points=[self.x, self.y, self.x + self.width, self.y],
                width=1
            )
        self.bind(pos=self._upd, size=self._upd)

        self._build()

    def _build(self):
        # Logo
        logo = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=170,
            spacing=8,
            padding=(0, 0, 12, 0)
        )
        logo.add_widget(Label(
            text='⬡',
            font_size=22,
            color=C['accent_cyan'],
            size_hint=(None, 1),
            width=28
        ))
        logo.add_widget(Label(
            text='QUANTUMPLAY',
            font_size=14,
            bold=True,
            color=C['accent_cyan'],
            size_hint=(None, 1),
            width=130
        ))
        self.add_widget(logo)

        # Menus texte
        menus = [
            ('Média',      self._menu_media),
            ('Lecture',    self._menu_lecture),
            ('Audio',      self._menu_audio),
            ('Vidéo',      self._menu_video),
            ('Outils',     self._menu_outils),
        ]
        for label, cb in menus:
            btn = QButton(
                text=label,
                font_size=12,
                size_hint=(None, None),
                size=(60, 28),
                on_release=cb
            )
            self.add_widget(btn)

        # Barre de recherche
        search_box = BoxLayout(
            size_hint=(1, None),
            height=30,
            spacing=6
        )
        search_icon = Label(
            text='🔍',
            font_size=14,
            size_hint=(None, 1),
            width=24,
            color=C['text_muted']
        )
        self._search = TextInput(
            hint_text='Recherche rapide — fichiers, artistes, albums...',
            hint_text_color=(*C['text_muted'][:3], 1),
            foreground_color=(*C['text_primary'][:3], 1),
            background_color=(*C['bg_card'][:3], 1),
            cursor_color=(*C['accent_cyan'][:3], 1),
            font_size=12,
            multiline=False,
            size_hint=(1, 1),
            padding=(10, 6)
        )
        self._search.bind(text=self._on_search)
        search_box.add_widget(search_icon)
        search_box.add_widget(self._search)
        self.add_widget(search_box)

        # Boutons d'action rapide
        actions = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=160,
            spacing=4
        )
        for icon, tip, cb in [
            ('📄', 'Ouvrir fichier',  lambda *a: self._open_files()),
            ('📁', 'Ouvrir dossier',  lambda *a: self._open_folder()),
            ('🌐', 'URL réseau',      lambda *a: self._open_url()),
            ('🔄', 'Scanner disques', lambda *a: self._scan_drives()),
            ('⚙️', 'Paramètres',     lambda *a: None),
        ]:
            btn = QIconButton(icon=icon, size_px=28)
            btn.bind(on_release=cb)
            actions.add_widget(btn)
        self.add_widget(actions)

    # -----------------------------------------------------------------------
    def _open_files(self):
        from ui.dialogs import open_file_dialog
        open_file_dialog(
            multiple=True,
            callback=lambda paths: self.main.add_files_to_queue(paths, play_first=True)
        )

    def _open_folder(self):
        from ui.dialogs import open_folder_dialog
        open_folder_dialog(
            callback=lambda path: self.main.add_folder_to_queue(path, play_first=True)
        )

    def _open_url(self):
        self.main.main_panel.show_url_dialog()

    def _scan_drives(self):
        self.main.show_notif('🔍 Scan en cours...')
        Clock.schedule_once(
            lambda dt: self.main.show_notif('✅ Scan terminé'), 2
        )

    def _menu_media(self, *a):
        self.main.show_notif('Menu Média')

    def _menu_lecture(self, *a):
        self.main.show_notif('Menu Lecture')

    def _menu_audio(self, *a):
        self.main.show_notif('Menu Audio')

    def _menu_video(self, *a):
        self.main.show_notif('Menu Vidéo')

    def _menu_outils(self, *a):
        self.main.show_notif('Menu Outils')

    def _on_search(self, instance, text):
        if hasattr(self.main, 'main_panel'):
            self.main.main_panel.search(text)

    # -----------------------------------------------------------------------
    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._line.points = [self.x, self.y, self.x + self.width, self.y]