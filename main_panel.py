"""
QuantumPlay — Panneau principal central
Sections : playlist, bibliothèque, historique, égaliseur, effets, visualiseur
"""

import math
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle,
    Line, Ellipse, Mesh
)
from kivy.clock import Clock

from ui.theme import C, SIZES, EQ_PRESETS, EQ_FREQS_10, EQ_FREQS_20
from ui.widgets.base import QButton, QLabel, QSeparator, QMonoLabel


# ---------------------------------------------------------------------------
# Ligne de piste dans la playlist
# ---------------------------------------------------------------------------
class TrackRow(BoxLayout):
    def __init__(self, track, index, active=False,
                 on_play=None, on_fav=None, **kw):
        super().__init__(
            orientation='horizontal',
            size_hint=(1, None),
            height=44,
            padding=(16, 0, 8, 0),
            spacing=8,
            **kw
        )
        self._track   = track
        self._index   = index
        self._active  = active
        self._on_play = on_play
        self._on_fav  = on_fav

        with self.canvas.before:
            self._bg_c = Color(0, 0, 0, 0)
            self._bg   = Rectangle(pos=self.pos, size=self.size)
            # Séparateur bas
            Color(*C['border'])
            self._sep = Line(
                points=[self.x, self.y, self.x + self.width, self.y],
                width=0.8
            )
        self.bind(pos=self._upd, size=self._upd)

        if active:
            self._bg_c.rgba = (*C['accent_cyan'][:3], 0.08)

        # Numéro / wave
        num_txt = '▶' if active else str(index + 1)
        self._num = Label(
            text=num_txt,
            font_size=12,
            color=C['accent_cyan'] if active else C['text_muted'],
            size_hint=(None, 1), width=32,
            halign='center', valign='middle'
        )
        self.add_widget(self._num)

        # Infos
        info = BoxLayout(orientation='vertical', size_hint=(1, 1))
        name_lbl = Label(
            text=f'{track.emoji} {track.title}',
            font_size=13,
            bold=active,
            color=C['accent_cyan'] if active else C['text_primary'],
            halign='left', valign='middle',
            shorten=True, shorten_from='right',
            size_hint=(1, None), height=22
        )
        name_lbl.bind(size=lambda *a: setattr(name_lbl, 'text_size', name_lbl.size))
        artist_lbl = Label(
            text=track.artist,
            font_size=11,
            color=C['text_muted'],
            halign='left', valign='middle',
            size_hint=(1, None), height=16
        )
        artist_lbl.bind(size=lambda *a: setattr(artist_lbl, 'text_size', artist_lbl.size))
        info.add_widget(name_lbl)
        info.add_widget(artist_lbl)
        self.add_widget(info)

        # Album
        self.add_widget(Label(
            text=track.album,
            font_size=11, color=C['text_muted'],
            size_hint=(None, 1), width=120,
            shorten=True, shorten_from='right',
            halign='left', valign='middle'
        ))

        # Durée
        self.add_widget(Label(
            text=track.duration_str,
            font_size=11, color=C['text_muted'],
            size_hint=(None, 1), width=50,
            halign='right', valign='middle'
        ))

        # Favori
        fav_lbl = Label(
            text='♥' if track.fav else '♡',
            font_size=14,
            color=C['accent_pink'] if track.fav else C['text_muted'],
            size_hint=(None, 1), width=24
        )
        fav_lbl.bind(on_touch_down=self._touch_fav)
        self.add_widget(fav_lbl)
        self._fav_label = fav_lbl

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap and self._on_play:
                self._on_play(self._index)
            return True
        return super().on_touch_down(touch)

    def _touch_fav(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._track.fav = not self._track.fav
            instance.text  = '♥' if self._track.fav else '♡'
            instance.color = C['accent_pink'] if self._track.fav else C['text_muted']

    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._sep.points = [self.x, self.y, self.x + self.width, self.y]


# ---------------------------------------------------------------------------
# Vue playlist
# ---------------------------------------------------------------------------
class PlaylistView(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', **kw)
        self.main = main

        # En-tête
        header = BoxLayout(
            size_hint=(1, None), height=50,
            padding=(16, 0, 8, 0), spacing=10
        )
        with header.canvas.before:
            Color(*C['bg_surface'])
            self._header_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda *a: setattr(self._header_bg, 'pos', header.pos),
                    size=lambda *a: setattr(self._header_bg, 'size', header.size))

        self._title_lbl = Label(
            text='File de lecture',
            font_size=14, bold=True,
            color=C['text_primary'],
            halign='left', valign='middle',
            size_hint=(1, 1)
        )
        self._title_lbl.bind(size=lambda *a: setattr(self._title_lbl, 'text_size', self._title_lbl.size))
        header.add_widget(self._title_lbl)

        btn_row = BoxLayout(size_hint=(None, 1), width=200, spacing=6)
        for text, cb in [
            ('🔀 Mélanger', lambda *a: self._shuffle()),
            ('▶ Tout lire', lambda *a: self._play_all()),
        ]:
            btn = QButton(text=text, font_size=11, size_hint=(None, 1), width=90)
            btn.bind(on_release=cb)
            btn_row.add_widget(btn)
        header.add_widget(btn_row)
        self.add_widget(header)
        self.add_widget(QSeparator())

        # Zone scrollable
        self._scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=(*C['accent_cyan'][:3], 0.3),
            bar_inactive_color=(*C['accent_cyan'][:3], 0.1)
        )
        self._list = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=0
        )
        self._list.bind(minimum_height=self._list.setter('height'))
        self._scroll.add_widget(self._list)
        self.add_widget(self._scroll)

    def refresh(self, tracks, current_index=0):
        self._list.clear_widgets()
        if not tracks:
            self._list.add_widget(self._empty_state())
            return

        for i, track in enumerate(tracks):
            row = TrackRow(
                track=track, index=i,
                active=(i == current_index),
                on_play=lambda idx: self.main.play_index(idx) if self.main else None
            )
            self._list.add_widget(row)

        total = sum(t.duration for t in tracks)
        m, s = int(total) // 60, int(total) % 60
        self._title_lbl.text = f'File de lecture — {len(tracks)} titres · {m}:{s:02d}'

    def set_active(self, index):
        for i, child in enumerate(self._list.children[::-1]):
            if isinstance(child, TrackRow):
                is_active = i == index
                child._bg_c.rgba = (*C['accent_cyan'][:3], 0.08) if is_active else (0,0,0,0)
                child._num.text  = '▶' if is_active else str(i + 1)
                child._num.color = C['accent_cyan'] if is_active else C['text_muted']

    def _shuffle(self):
        if self.main:
            import random
            random.shuffle(self.main.queue.tracks)
            self.refresh(self.main.queue.tracks, self.main.queue.current)

    def _play_all(self):
        if self.main and self.main.queue.tracks:
            self.main.play_index(0)

    def _empty_state(self):
        box = BoxLayout(
            orientation='vertical',
            size_hint=(1, None), height=280,
            spacing=16
        )
        box.add_widget(Label(
            text='🎵', font_size=48,
            color=(*C['text_muted'][:3], 0.3),
            size_hint=(1, None), height=60
        ))
        box.add_widget(Label(
            text='Aucun fichier dans la liste\nGlisse des fichiers ici ou utilise les boutons en haut',
            font_size=13, color=C['text_muted'],
            halign='center', valign='middle',
            size_hint=(1, None), height=50
        ))
        btn = QButton(
            text='📄 Ajouter des fichiers',
            size_hint=(None, None), size=(180, 36)
        )
        btn.bind(on_release=lambda *a: self.main and self.main.topbar._open_files())
        box.add_widget(btn)
        return box


# ---------------------------------------------------------------------------
# Vue bibliothèque (grille de cards)
# ---------------------------------------------------------------------------
class LibraryView(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', **kw)
        self.main = main

        # Toolbar
        toolbar = BoxLayout(
            size_hint=(1, None), height=44,
            padding=(12, 6), spacing=8
        )
        with toolbar.canvas.before:
            Color(*C['bg_surface'])
            self._tb_bg = Rectangle(pos=toolbar.pos, size=toolbar.size)
        toolbar.bind(pos=lambda *a: setattr(self._tb_bg, 'pos', toolbar.pos),
                     size=lambda *a: setattr(self._tb_bg, 'size', toolbar.size))

        for text, cb in [
            ('📄 Ajouter', lambda *a: self.main and self.main.topbar._open_files()),
            ('📁 Dossier',  lambda *a: self.main and self.main.topbar._open_folder()),
        ]:
            btn = QButton(text=text, font_size=11, size_hint=(None, 1), width=100)
            btn.bind(on_release=cb)
            toolbar.add_widget(btn)

        self._count_lbl = Label(
            text='0 fichiers',
            font_size=11, color=C['text_muted'],
            size_hint=(1, 1), halign='right', valign='middle'
        )
        toolbar.add_widget(self._count_lbl)
        self.add_widget(toolbar)
        self.add_widget(QSeparator())

        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=(*C['accent_cyan'][:3], 0.3),
            bar_inactive_color=(*C['accent_cyan'][:3], 0.1)
        )
        self._grid = GridLayout(
            cols=5,
            size_hint=(1, None),
            spacing=12,
            padding=16
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        scroll.add_widget(self._grid)
        self.add_widget(scroll)

    def refresh(self, tracks):
        self._grid.clear_widgets()
        self._count_lbl.text = f'{len(tracks)} fichiers'
        if not tracks:
            self._grid.add_widget(Label(
                text='Bibliothèque vide\nAjoute des fichiers audio ou vidéo',
                font_size=13, color=C['text_muted'],
                halign='center', valign='middle',
                size_hint=(1, None), height=260
            ))
            return
        for track in tracks:
            card = self._make_card(track)
            self._grid.add_widget(card)

    def _make_card(self, track):
        card = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(155, 200),
            spacing=0
        )
        with card.canvas.before:
            Color(*C['bg_card'])
            self._card_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[SIZES['radius_lg']]
            )
            Color(*C['border'])
            Line(rounded_rectangle=(*card.pos, *card.size, SIZES['radius_lg']), width=0.8)
        card.bind(
            pos=lambda *a: None,
            size=lambda *a: None
        )

        # Vignette
        thumb = BoxLayout(size_hint=(1, None), height=120)
        thumb.add_widget(Label(
            text=track.emoji, font_size=44,
            color=C['text_primary']
        ))
        card.add_widget(thumb)

        # Infos
        info = BoxLayout(
            orientation='vertical',
            size_hint=(1, None), height=48,
            padding=(8, 4)
        )
        title = Label(
            text=track.title, font_size=11,
            color=C['text_primary'],
            halign='left', valign='middle',
            shorten=True, shorten_from='right',
            size_hint=(1, None), height=18
        )
        title.bind(size=lambda *a: setattr(title, 'text_size', title.size))
        meta = Label(
            text=f'{track.artist} · {track.duration_str}',
            font_size=10, color=C['text_muted'],
            halign='left', valign='middle',
            size_hint=(1, None), height=14
        )
        meta.bind(size=lambda *a: setattr(meta, 'text_size', meta.size))
        info.add_widget(title)
        info.add_widget(meta)

        # Bouton lire
        play_btn = QButton(
            text='▶ Lire', font_size=10,
            size_hint=(1, None), height=24
        )
        play_btn.bind(on_release=lambda *a: self.main and self._play_track(track))
        info.add_widget(play_btn)
        card.add_widget(info)
        return card

    def _play_track(self, track):
        if not self.main:
            return
        q = self.main.queue
        if track not in q.tracks:
            q.add(track)
        idx = q.tracks.index(track)
        self.main.play_index(idx)


# ---------------------------------------------------------------------------
# Vue historique
# ---------------------------------------------------------------------------
class HistoryView(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', **kw)
        self.main = main

        scroll = ScrollView(
            size_hint=(1, 1), do_scroll_x=False,
            bar_width=3,
            bar_color=(*C['accent_cyan'][:3], 0.3),
        )
        self._list = BoxLayout(
            orientation='vertical',
            size_hint=(1, None), spacing=2, padding=16
        )
        self._list.bind(minimum_height=self._list.setter('height'))
        scroll.add_widget(self._list)
        self.add_widget(scroll)

    def refresh(self, grouped):
        self._list.clear_widgets()
        if not grouped:
            self._list.add_widget(Label(
                text='🕐  Aucun historique',
                font_size=13, color=C['text_muted'],
                size_hint=(1, None), height=260,
                halign='center', valign='middle'
            ))
            return
        for group in grouped:
            self._list.add_widget(Label(
                text=group['group'].upper(),
                font_size=9, color=C['text_muted'],
                bold=True, size_hint=(1, None), height=24,
                halign='left', valign='middle'
            ))
            for item in group['items']:
                row = BoxLayout(
                    size_hint=(1, None), height=44,
                    spacing=12, padding=(8, 0)
                )
                row.add_widget(Label(
                    text=item.get('emoji', '🎵'), font_size=20,
                    size_hint=(None, 1), width=36
                ))
                info = BoxLayout(orientation='vertical', size_hint=(1, 1))
                for txt, fs, col in [
                    (item.get('title', ''), 13, C['text_primary']),
                    (f"{item.get('format','')} · {item.get('artist','')}", 10, C['text_muted']),
                ]:
                    lbl = Label(
                        text=txt, font_size=fs, color=col,
                        halign='left', valign='middle',
                        size_hint=(1, None), height=18,
                        shorten=True, shorten_from='right'
                    )
                    lbl.bind(size=lambda w, *a: setattr(w, 'text_size', w.size))
                    info.add_widget(lbl)
                row.add_widget(info)
                row.add_widget(Label(
                    text=item.get('time', ''),
                    font_size=10, color=C['text_muted'],
                    size_hint=(None, 1), width=40,
                    halign='right', valign='middle'
                ))
                self._list.add_widget(row)


# ---------------------------------------------------------------------------
# Vue Égaliseur
# ---------------------------------------------------------------------------
class EqView(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', spacing=0, padding=16, **kw)
        self.main = main
        self._freqs  = EQ_FREQS_10
        self._gains  = {f: 0.0 for f in EQ_FREQS_10}
        self._drag_freq  = None
        self._drag_start = None
        self._drag_val   = 0.0

        self._build()

    def _build(self):
        # En-tête
        header = BoxLayout(size_hint=(1, None), height=42, spacing=8)
        header.add_widget(Label(
            text='🎛  ÉGALISEUR',
            font_size=15, bold=True,
            color=C['accent_cyan'],
            halign='left', valign='middle',
            size_hint=(None, 1), width=160
        ))
        header.add_widget(Widget(size_hint=(1, 1)))

        # Sélecteur bandes
        self._mode_btn = QButton(
            text='10 bandes', font_size=11,
            size_hint=(None, 1), width=100
        )
        self._mode_btn.bind(on_release=self._toggle_bands)
        header.add_widget(self._mode_btn)

        # Presets
        for name in ['flat', 'bass', 'club', 'vocal', 'cinema', 'gaming']:
            btn = QButton(text=name.capitalize(), font_size=10,
                          size_hint=(None, 1), width=64)
            btn.bind(on_release=lambda b, n=name: self._apply_preset(n))
            header.add_widget(btn)

        reset_btn = QButton(
            text='Reset', font_size=10,
            size_hint=(None, 1), width=54
        )
        reset_btn.bind(on_release=lambda *a: self._reset())
        header.add_widget(reset_btn)
        self.add_widget(header)

        # Canevas EQ
        self._eq_canvas_widget = EqCanvas(
            freqs=self._freqs,
            gains=self._gains,
            size_hint=(1, 1),
            main=self
        )
        self.add_widget(self._eq_canvas_widget)

    def _toggle_bands(self, *a):
        if len(self._freqs) == 10:
            self._freqs = EQ_FREQS_20
            self._gains = {f: 0.0 for f in EQ_FREQS_20}
            self._mode_btn.text = '20 bandes'
        else:
            self._freqs = EQ_FREQS_10
            self._gains = {f: 0.0 for f in EQ_FREQS_10}
            self._mode_btn.text = '10 bandes'
        self._eq_canvas_widget.update_data(self._freqs, self._gains)

    def _apply_preset(self, name: str):
        vals = EQ_PRESETS.get(name, [0]*10)
        freqs = EQ_FREQS_10
        for i, freq in enumerate(freqs):
            if freq in self._gains:
                self._gains[freq] = vals[i] if i < len(vals) else 0.0
        self._eq_canvas_widget.update_data(self._freqs, self._gains)
        if self.main:
            for freq, gain in self._gains.items():
                self.main.engine.set_eq_gain(freq, gain)

    def _reset(self):
        for f in self._gains:
            self._gains[f] = 0.0
        self._eq_canvas_widget.update_data(self._freqs, self._gains)
        if self.main:
            for freq in self._gains:
                self.main.engine.set_eq_gain(freq, 0.0)

    def set_band_gain(self, freq: int, gain: float):
        self._gains[freq] = gain
        if self.main:
            self.main.engine.set_eq_gain(freq, gain)


class EqCanvas(Widget):
    """Canevas des barres EQ interactives."""

    def __init__(self, freqs, gains, main=None, **kw):
        super().__init__(**kw)
        self.main   = main
        self._freqs = freqs
        self._gains = gains
        self._drag  = None  # (freq, start_y, start_gain)
        self.bind(pos=self._draw, size=self._draw)

    def update_data(self, freqs, gains):
        self._freqs = freqs
        self._gains = gains
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        if not self._freqs:
            return

        n  = len(self._freqs)
        bw = (self.width - 8) / n
        with self.canvas:
            # Fond
            Color(*C['bg_card'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

            # Ligne zéro
            zy = self.y + self.height / 2
            Color(*C['accent_cyan'][:3], 0.2)
            Line(points=[self.x + 4, zy, self.right - 4, zy], width=0.8)

            for i, freq in enumerate(self._freqs):
                gain   = self._gains.get(freq, 0.0)
                pct    = (gain + 12) / 24    # 0..1 (0 = -12dB, 1 = +12dB)
                cx     = self.x + 4 + (i + 0.5) * bw
                bar_h  = abs(gain) / 12 * (self.height * 0.4)
                bar_y  = zy if gain >= 0 else zy - bar_h

                # Couleur selon valeur
                if gain > 0:
                    Color(*C['accent_cyan'][:3], 0.9)
                elif gain < 0:
                    Color(*C['accent_pink'][:3], 0.8)
                else:
                    Color(*C['text_muted'][:3], 0.4)

                bw2 = max(8, bw - 6)
                RoundedRectangle(
                    pos=(cx - bw2 / 2, bar_y),
                    size=(bw2, max(3, bar_h)),
                    radius=[3]
                )

                # Valeur dB
                Color(*C['text_secondary'])
                # (les labels Kivy sont dessinés via widgets séparés, pas canvas)

                # Label fréquence
                Color(*C['text_muted'])

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        n  = len(self._freqs)
        if n == 0:
            return True
        bw = (self.width - 8) / n
        idx = int((touch.x - self.x - 4) / bw)
        idx = max(0, min(n - 1, idx))
        freq = self._freqs[idx]
        self._drag = (freq, touch.y, self._gains.get(freq, 0.0))
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._drag:
            freq, start_y, start_gain = self._drag
            delta = (touch.y - start_y) / (self.height * 0.04)
            new_gain = max(-12.0, min(12.0, start_gain + delta))
            self._gains[freq] = round(new_gain, 1)
            self._draw()
            if self.main and hasattr(self.main, 'set_band_gain'):
                self.main.set_band_gain(freq, new_gain)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._drag = None
        return super().on_touch_up(touch)


# ---------------------------------------------------------------------------
# Panneau principal avec onglets
# ---------------------------------------------------------------------------
class MainPanel(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', **kw)
        self.main = main

        with self.canvas.before:
            Color(*C['bg_panel'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

        # Onglets
        self._tabs = BoxLayout(
            size_hint=(1, None), height=38,
            spacing=0
        )
        with self._tabs.canvas.before:
            Color(*C['bg_surface'])
            self._tab_bg = Rectangle(pos=self._tabs.pos, size=self._tabs.size)
        self._tabs.bind(
            pos=lambda *a: setattr(self._tab_bg, 'pos', self._tabs.pos),
            size=lambda *a: setattr(self._tab_bg, 'size', self._tabs.size)
        )

        self._tab_btns = {}
        for key, label in [
            ('playlist', 'File de lecture'),
            ('library',  'Bibliothèque'),
            ('history',  'Historique'),
        ]:
            btn = self._make_tab_btn(key, label)
            self._tabs.add_widget(btn)
            self._tab_btns[key] = btn

        self.add_widget(self._tabs)
        self.add_widget(QSeparator())

        # Contenu des sections
        self._sections = {}
        self._current_section = None

        self._playlist_view = PlaylistView(main=main, size_hint=(1, 1))
        self._library_view  = LibraryView(main=main, size_hint=(1, 1))
        self._history_view  = HistoryView(main=main, size_hint=(1, 1))
        self._eq_view       = EqView(main=main, size_hint=(1, 1))

        for key, widget in [
            ('playlist', self._playlist_view),
            ('library',  self._library_view),
            ('history',  self._history_view),
            ('eq',       self._eq_view),
        ]:
            widget.opacity = 0
            widget.disabled = True
            self._sections[key] = widget
            self.add_widget(widget)

        # Afficher la playlist par défaut
        self.show_section('playlist')

    def _make_tab_btn(self, key, label):
        btn = Label(
            text=label, font_size=12,
            color=C['text_muted'],
            size_hint=(None, 1), width=130,
            halign='center', valign='middle'
        )
        with btn.canvas.after:
            Color(0, 0, 0, 0)
            btn._underline_color = btn.canvas.after.children[-1]
            btn._underline = Line(
                points=[btn.x, btn.y, btn.right, btn.y], width=2
            )
        btn.bind(pos=self._upd_tab_line(btn), size=self._upd_tab_line(btn))
        btn.bind(on_touch_down=lambda w, t: self._tab_touch(key, w, t))
        return btn

    def _upd_tab_line(self, btn):
        def _f(*a):
            btn._underline.points = [btn.x, btn.y, btn.right, btn.y]
        return _f

    def _tab_touch(self, key, widget, touch):
        if widget.collide_point(*touch.pos):
            self.show_section(key)

    def show_section(self, key: str):
        # Masquer l'ancienne section
        if self._current_section and self._current_section in self._sections:
            w = self._sections[self._current_section]
            w.opacity  = 0
            w.disabled = True
            # Désactiver l'onglet
            if self._current_section in self._tab_btns:
                btn = self._tab_btns[self._current_section]
                btn.color = C['text_muted']
                try:
                    btn._underline_color.rgba = (0, 0, 0, 0)
                except Exception:
                    pass

        self._current_section = key

        if key in self._sections:
            w = self._sections[key]
            w.opacity  = 1
            w.disabled = False

        # Activer l'onglet correspondant
        if key in self._tab_btns:
            btn = self._tab_btns[key]
            btn.color = C['accent_cyan']
            try:
                btn._underline_color.rgba = C['accent_cyan']
            except Exception:
                pass

    def refresh_playlist(self):
        if self.main:
            self._playlist_view.refresh(
                self.main.queue.tracks,
                self.main.queue.current
            )

    def refresh_library(self):
        if self.main:
            self._library_view.refresh(self.main.library.items)

    def refresh_history(self):
        if self.main:
            self._history_view.refresh(self.main.library.grouped_history())

    def set_active_track(self, index: int):
        self._playlist_view.set_active(index)

    def search(self, text: str):
        # Filtrage simple sur titre/artiste
        if not self.main:
            return
        if not text:
            self._library_view.refresh(self.main.library.items)
            return
        text_low = text.lower()
        filtered = [
            t for t in self.main.library.items
            if text_low in t.title.lower() or text_low in t.artist.lower()
        ]
        self._library_view.refresh(filtered)

    def show_url_dialog(self):
        pass  # TODO: popup URL

    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size