"""
QuantumPlay — Barre de lecture (bas)
Contrôles complets : lecture, progression, volume, mode répétition
"""

import math
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import (
    Color, Rectangle, Line, RoundedRectangle,
    Ellipse, Mesh, PushMatrix, PopMatrix, Rotate
)
from kivy.clock import Clock
from kivy.animation import Animation

from ui.theme import C, SIZES
from ui.widgets.base import (
    QButton, QIconButton, QLabel, QProgressBar, QVolumeSlider
)


def fmt_time(seconds: float) -> str:
    s = int(seconds)
    return f'{s // 60}:{s % 60:02d}'


class VizBars(Widget):
    """Mini visualiseur animé (8 barres néon)."""

    def __init__(self, **kw):
        super().__init__(
            size_hint=(None, None),
            size=(60, 24),
            **kw
        )
        self._phase = 0.0
        self._playing = False
        self._bars_canvas = []
        Clock.schedule_interval(self._animate, 1 / 30)

        with self.canvas:
            pass  # dessiné dans _animate

    def set_playing(self, val: bool):
        self._playing = val

    def _animate(self, dt):
        if not self._playing or self.canvas is None:
            return
        self._phase += dt * 4
        self.canvas.clear()
        n = 8
        heights = [
            4 + 12 * abs(math.sin(self._phase + i * 0.7))
            for i in range(n)
        ]
        bar_w = 3
        gap   = (self.width - n * bar_w) / (n + 1)

        with self.canvas:
            for i, h in enumerate(heights):
                x = self.x + gap + i * (bar_w + gap)
                y = self.y + (self.height - h) / 2
                # Gradient violet → cyan
                ratio = i / (n - 1)
                r = C['accent_violet'][0] * (1 - ratio) + C['accent_cyan'][0] * ratio
                g = C['accent_violet'][1] * (1 - ratio) + C['accent_cyan'][1] * ratio
                b = C['accent_violet'][2] * (1 - ratio) + C['accent_cyan'][2] * ratio
                Color(r, g, b, 0.85)
                RoundedRectangle(pos=(x, y), size=(bar_w, h), radius=[2])


class PlayButton(Widget):
    """Bouton play/pause circulaire dégradé."""

    def __init__(self, on_press=None, **kw):
        super().__init__(
            size_hint=(None, None),
            size=(50, 50),
            **kw
        )
        self._on_press = on_press
        self._is_playing = False
        self._draw()

    def _draw(self):
        if self.canvas is None:
            return
        self.canvas.clear()
        with self.canvas:
            # Fond dégradé (simulation avec deux cercles)
            Color(*C['accent_violet'])
            Ellipse(pos=self.pos, size=self.size)
            Color(*C['accent_cyan'][:3], 0.4)
            Ellipse(
                pos=(self.x + self.width * 0.3, self.y),
                size=(self.width * 0.7, self.height)
            )
            # Icône
            Color(1, 1, 1, 1)
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            if self._is_playing:
                # Pause : deux barres
                Color(1, 1, 1, 1)
                Rectangle(pos=(cx - 7, cy - 8), size=(4, 16))
                Rectangle(pos=(cx + 3, cy - 8), size=(4, 16))
            else:
                # Play : triangle
                Color(1, 1, 1, 1)
                pts = [
                    cx - 6, cy - 9,
                    cx - 6, cy + 9,
                    cx + 10, cy,
                ]
                Mesh(vertices=[
                    pts[0], pts[1], 0, 0,
                    pts[2], pts[3], 0, 0,
                    pts[4], pts[5], 0, 0,
                ], indices=[0, 1, 2], mode='triangles')

    def set_playing(self, val: bool):
        self._is_playing = val
        self._draw()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self._on_press:
                self._on_press()
            # Animation d'appui
            anim = Animation(size=(44, 44), duration=0.08) + \
                   Animation(size=(50, 50), duration=0.08)
            anim.start(self)
            return True
        return super().on_touch_down(touch)

    def on_size(self, *a):
        self._draw()

    def on_pos(self, *a):
        self._draw()


class PlayerBar(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(
            orientation='horizontal',
            padding=(20, 0),
            spacing=0,
            **kw
        )
        self.main = main
        self._duration = 0.0
        self._volume   = 75
        self._muted    = False

        with self.canvas.before:
            Color(*C['bg_surface'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
            # Ligne supérieure dégradée
            Color(*C['accent_violet'][:3], 0.7)
            self._top_line = Line(
                points=[self.x, self.top, self.right, self.top],
                width=1
            )
        self.bind(pos=self._upd, size=self._upd)

        self._build()

    def _build(self):
        # ── Section gauche : piste en cours ─────────────────────────────
        left = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=280,
            spacing=12
        )

        # Pochette
        art = BoxLayout(
            size_hint=(None, 1),
            width=52
        )
        self._art_label = Label(
            text='🎵',
            font_size=26,
            color=C['text_primary']
        )
        art.add_widget(self._art_label)
        left.add_widget(art)

        # Infos piste
        track_info = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=52,
            spacing=2
        )
        self._title_label = Label(
            text='Aucune piste sélectionnée',
            font_size=13,
            bold=True,
            color=C['text_primary'],
            halign='left', valign='middle',
            shorten=True, shorten_from='right',
            size_hint=(1, None), height=20
        )
        self._title_label.bind(
            size=lambda *a: setattr(self._title_label, 'text_size', self._title_label.size)
        )
        self._artist_label = Label(
            text='—',
            font_size=11,
            color=C['text_secondary'],
            halign='left', valign='middle',
            size_hint=(1, None), height=16
        )
        self._artist_label.bind(
            size=lambda *a: setattr(self._artist_label, 'text_size', self._artist_label.size)
        )

        # Mini actions (♥ + info)
        mini_actions = BoxLayout(
            size_hint=(1, None), height=16,
            spacing=8
        )
        for icon, cb in [
            ('♥', lambda *a: None),
            ('➕', lambda *a: None),
            ('ℹ', lambda *a: None),
        ]:
            btn = Label(
                text=icon, font_size=13,
                color=C['text_muted'],
                size_hint=(None, 1), width=16
            )
            mini_actions.add_widget(btn)

        track_info.add_widget(self._title_label)
        track_info.add_widget(self._artist_label)
        track_info.add_widget(mini_actions)
        left.add_widget(track_info)

        # Mini viz
        self._viz = VizBars()
        left.add_widget(self._viz)

        self.add_widget(left)

        # ── Section centrale : contrôles ─────────────────────────────────
        center = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=6,
            padding=(20, 8)
        )

        # Boutons de contrôle
        controls = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=50,
            spacing=8
        )
        controls.add_widget(Widget(size_hint=(1, 1)))  # spacer

        # Répétition
        self._repeat_btn = Label(
            text='🔁', font_size=18,
            color=C['text_secondary'],
            size_hint=(None, 1), width=32
        )
        self._repeat_btn.bind(on_touch_down=self._touch_repeat)
        controls.add_widget(self._repeat_btn)

        # Précédent
        prev_btn = Label(
            text='⏮', font_size=20,
            color=C['text_secondary'],
            size_hint=(None, 1), width=36
        )
        prev_btn.bind(on_touch_down=self._touch_prev)
        controls.add_widget(prev_btn)

        # Play/Pause
        self._play_btn = PlayButton(on_press=self.toggle_play)
        controls.add_widget(self._play_btn)

        # Stop
        stop_btn = Label(
            text='⏹', font_size=20,
            color=C['text_secondary'],
            size_hint=(None, 1), width=36
        )
        stop_btn.bind(on_touch_down=self._touch_stop)
        controls.add_widget(stop_btn)

        # Suivant
        next_btn = Label(
            text='⏭', font_size=20,
            color=C['text_secondary'],
            size_hint=(None, 1), width=36
        )
        next_btn.bind(on_touch_down=self._touch_next)
        controls.add_widget(next_btn)

        # Aléatoire
        self._shuffle_btn = Label(
            text='🔀', font_size=18,
            color=C['text_secondary'],
            size_hint=(None, 1), width=32
        )
        self._shuffle_btn.bind(on_touch_down=self._touch_shuffle)
        controls.add_widget(self._shuffle_btn)

        controls.add_widget(Widget(size_hint=(1, 1)))  # spacer
        center.add_widget(controls)

        # Barre de progression
        progress_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=20,
            spacing=10
        )
        self._cur_time = Label(
            text='0:00', font_size=10,
            color=C['text_muted'],
            size_hint=(None, 1), width=36
        )
        self._progress = QProgressBar()
        self._progress.on_seek = self._on_seek
        self._dur_time = Label(
            text='0:00', font_size=10,
            color=C['text_muted'],
            size_hint=(None, 1), width=36,
            halign='right', valign='middle'
        )
        progress_row.add_widget(self._cur_time)
        progress_row.add_widget(self._progress)
        progress_row.add_widget(self._dur_time)
        center.add_widget(progress_row)

        self.add_widget(center)

        # ── Section droite : volume + extras ─────────────────────────────
        right = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=280,
            spacing=8,
            padding=(8, 0)
        )

        # Volume
        vol_row = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=140,
            spacing=6
        )
        self._vol_icon = Label(
            text='🔊', font_size=16,
            color=C['text_secondary'],
            size_hint=(None, 1), width=22
        )
        self._vol_icon.bind(on_touch_down=self._touch_mute)
        self._vol_slider = QVolumeSlider()
        self._vol_slider.value = self._volume
        self._vol_slider.on_seek = self._on_volume_change
        vol_row.add_widget(self._vol_icon)
        vol_row.add_widget(self._vol_slider)
        right.add_widget(vol_row)

        # Boutons droite
        right_btns = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=130,
            spacing=4
        )
        for icon, tip, cb in [
            ('🎛', 'Égaliseur',        lambda *a: self._open_eq()),
            ('⛶',  'Mode vidéo',       lambda *a: None),
            ('▦',  'Mini player',      lambda *a: None),
            ('☰',  'Liste de lecture', lambda *a: self._toggle_playlist()),
        ]:
            btn = QIconButton(icon=icon, size_px=28)
            btn.bind(on_release=cb)
            right_btns.add_widget(btn)
        right.add_widget(right_btns)

        self.add_widget(right)

    # -----------------------------------------------------------------------
    # Contrôles de lecture
    # -----------------------------------------------------------------------
    def toggle_play(self):
        if self.main:
            engine = self.main.engine
            queue  = self.main.queue
            if engine.is_playing:
                engine.pause()
            elif engine.current_track:
                engine.resume()
            elif queue.current_track():
                self.main.play_track_obj(queue.current_track())

    def next_track(self):
        if self.main:
            t = self.main.queue.next()
            if t:
                self.main.play_track_obj(t)

    def prev_track(self):
        if self.main:
            t = self.main.queue.prev()
            if t:
                self.main.play_track_obj(t)

    def toggle_mute(self):
        if self.main:
            self.main.engine.toggle_mute()
            self._muted = not self._muted
            self._vol_icon.text = '🔇' if self._muted else '🔊'

    def _on_seek(self, pct: float):
        if self.main and self._duration:
            self.main.engine.seek(pct * self._duration)

    def _on_volume_change(self, pct: float):
        if self.main:
            self.main.engine.set_volume(int(pct * 100))

    def _open_eq(self):
        if self.main:
            self.main.main_panel.show_section('eq')

    def _toggle_playlist(self):
        if self.main:
            self.main.main_panel.show_section('playlist')

    # Touch helpers pour les Labels non-Button
    def _touch_prev(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.prev_track()

    def _touch_next(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.next_track()

    def _touch_stop(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.main:
            self.main.engine.stop()

    def _touch_mute(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.toggle_mute()

    def _touch_shuffle(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.main:
            q = self.main.queue
            q.shuffle = not q.shuffle
            self._shuffle_btn.color = C['accent_cyan'] if q.shuffle else C['text_secondary']

    def _touch_repeat(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.main:
            modes = {'off': 'all', 'all': 'one', 'one': 'off'}
            icons  = {'off': '🔁', 'all': '🔁', 'one': '🔂'}
            q = self.main.queue
            q.repeat = modes[q.repeat]
            self._repeat_btn.text  = icons[q.repeat]
            self._repeat_btn.color = (
                C['accent_cyan'] if q.repeat != 'off' else C['text_secondary']
            )

    # -----------------------------------------------------------------------
    # Mises à jour UI depuis le moteur
    # -----------------------------------------------------------------------
    def set_current_track(self, track):
        self._title_label.text  = track.title
        self._artist_label.text = track.artist
        self._art_label.text    = track.emoji
        self._duration          = track.duration
        self._dur_time.text     = track.duration_str
        self._cur_time.text     = '0:00'
        self._progress.value    = 0

    def update_progress(self, pos: float, dur: float):
        self._duration = dur
        if dur:
            self._progress.value = (pos / dur) * 100
        self._cur_time.text = fmt_time(pos)
        self._dur_time.text = fmt_time(dur)

    def set_play_state(self, playing: bool):
        self._play_btn.set_playing(playing)
        self._viz.set_playing(playing)

    # -----------------------------------------------------------------------
    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._top_line.points = [self.x, self.top, self.right, self.top]