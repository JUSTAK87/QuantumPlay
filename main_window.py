"""
QuantumPlay — Fenêtre principale
Layout global : topbar + sidebar + main + right panel + player bar
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from ui.theme import C, SIZES
from ui.widgets.topbar import TopBar
from ui.widgets.sidebar import Sidebar
from ui.widgets.main_panel import MainPanel
from ui.widgets.right_panel import RightPanel
from ui.widgets.player_bar import PlayerBar
from ui.widgets.notif import NotifManager

from engine.player import FFmpegEngine, PlayQueue, Track
from engine.library import MediaLibrary


class QuantumPlayLayout(FloatLayout):

    def __init__(self, controller=None, **kw):
        super().__init__(**kw)

        self.controller = controller

        # --- Moteur et données ---
        self.engine  = FFmpegEngine()
        self.queue   = PlayQueue()
        self.library = MediaLibrary()
        self.notif   = NotifManager(self)

        # Callbacks moteur
        self.engine.on_track_end       = self._on_track_end
        self.engine.on_position_update = self._on_position_update
        self.engine.on_state_change    = self._on_state_change

        # --- Fond global ---
        with self.canvas.before:
            Color(*C['bg_deep'])
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # --- Construction UI ---
        self._build_layout()

    # -----------------------------------------------------------------------
    # Construction du layout
    # -----------------------------------------------------------------------
    def _build_layout(self):
        """
        Structure :
        ┌─────────────────────────────────────┐
        │            TopBar (48px)            │
        ├──────────┬──────────────┬───────────┤
        │ Sidebar  │  MainPanel   │ RightPanel│
        │ (220px)  │  (flex)      │ (260px)   │
        ├─────────────────────────────────────┤
        │          PlayerBar (130px)          │
        └─────────────────────────────────────┘
        """
        # Colonne principale (vertical)
        root_col = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            spacing=0
        )
        self.add_widget(root_col)

        # -- TopBar --
        self.topbar = TopBar(
            size_hint=(1, None),
            height=SIZES['topbar_h'],
            main=self
        )
        root_col.add_widget(self.topbar)

        # -- Zone centrale (sidebar + main + right) --
        center_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=0
        )
        root_col.add_widget(center_row)

        self.sidebar = Sidebar(
            size_hint=(None, 1),
            width=SIZES['sidebar_w'],
            main=self
        )
        center_row.add_widget(self.sidebar)

        self.main_panel = MainPanel(
            size_hint=(1, 1),
            main=self
        )
        center_row.add_widget(self.main_panel)

        self.right_panel = RightPanel(
            size_hint=(None, 1),
            width=SIZES['right_panel_w'],
            main=self
        )
        center_row.add_widget(self.right_panel)

        # -- PlayerBar --
        self.player_bar = PlayerBar(
            size_hint=(1, None),
            height=SIZES['player_h'],
            main=self
        )
        root_col.add_widget(self.player_bar)

        # Charger la bibliothèque existante dans l'UI
        Clock.schedule_once(self._init_library_ui, 0.3)

    # -----------------------------------------------------------------------
    # Init post-build
    # -----------------------------------------------------------------------
    def _init_library_ui(self, dt):
        for track in self.library.items:
            self.queue.add(track)
        self.main_panel.refresh_playlist()
        self.main_panel.refresh_library()
        self.right_panel.refresh_queue()
        self.sidebar.update_counts(
            play=self.queue.count,
            lib=len(self.library.items),
            history=sum(len(g['items']) for g in self.library.grouped_history())
        )

    # -----------------------------------------------------------------------
    # Callbacks moteur (appelés depuis thread, schedule sur main thread)
    # -----------------------------------------------------------------------
    def _on_track_end(self):
        Clock.schedule_once(lambda dt: self._handle_next(), 0)

    def _on_position_update(self, pos, dur):
        def _upd(dt):
            self.player_bar.update_progress(pos, dur)
            self.right_panel.update_progress(pos, dur)
        Clock.schedule_once(_upd, 0)

    def _on_state_change(self, playing: bool):
        def _upd(dt):
            self.player_bar.set_play_state(playing)
        Clock.schedule_once(_upd, 0)

    def _handle_next(self):
        next_track = self.queue.next()
        if next_track:
            self.play_track_obj(next_track)
        else:
            self.player_bar.set_play_state(False)

    # -----------------------------------------------------------------------
    # API publique de lecture
    # -----------------------------------------------------------------------
    def play_track_obj(self, track: Track):
        """Lance la lecture d'un objet Track."""
        self.engine.play(track)
        self.library.add_history(track)

        # Mettre à jour l'UI
        self.player_bar.set_current_track(track)
        self.right_panel.set_now_playing(track)
        self.main_panel.set_active_track(self.queue.current)
        self.right_panel.refresh_queue()
        self.sidebar.update_counts(
            play=self.queue.count,
            lib=len(self.library.items),
            history=sum(len(g['items']) for g in self.library.grouped_history())
        )
        self.notif.show(f'▶ {track.title}')

    def play_index(self, index: int):
        track = self.queue.go_to(index)
        if track:
            self.play_track_obj(track)

    def add_files_to_queue(self, paths, play_first=False):
        """Ajoute des fichiers à la file et à la bibliothèque."""
        def _on_progress(i, total, track):
            def _ui(dt):
                self.queue.add(track)
                self.main_panel.refresh_playlist()
                self.main_panel.refresh_library()
                self.right_panel.refresh_queue()
                self.sidebar.update_counts(
                    play=self.queue.count,
                    lib=len(self.library.items),
                    history=0
                )
            Clock.schedule_once(_ui, 0)

        import threading
        def _worker():
            new = self.library.add_files(paths, on_progress=_on_progress)
            if play_first and new:
                Clock.schedule_once(
                    lambda dt: self.play_track_obj(new[0]), 0.1
                )
        threading.Thread(target=_worker, daemon=True).start()

    def add_folder_to_queue(self, folder_path: str, play_first=False):
        def _on_done(tracks):
            def _ui(dt):
                for t in tracks:
                    if t not in self.queue.tracks:
                        self.queue.add(t)
                self.main_panel.refresh_playlist()
                self.main_panel.refresh_library()
                self.right_panel.refresh_queue()
                self.sidebar.update_counts(
                    play=self.queue.count,
                    lib=len(self.library.items),
                    history=0
                )
                self.notif.show(f'📂 {len(tracks)} fichiers chargés')
                if play_first and tracks:
                    self.play_track_obj(tracks[0])
            Clock.schedule_once(_ui, 0)

        self.library.add_folder_async(folder_path, on_done=_on_done)

    # -----------------------------------------------------------------------
    # Utilitaires
    # -----------------------------------------------------------------------
    def _update_bg(self, *a):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def show_notif(self, msg: str):
        self.notif.show(msg)