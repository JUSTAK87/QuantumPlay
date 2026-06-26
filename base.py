"""
QuantumPlay — Widgets de base réutilisables
Boutons, labels, separateurs avec le style néon cyberpunk
"""

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import (
    Color, Rectangle, RoundedRectangle,
    Line, Ellipse
)
from kivy.properties import (
    StringProperty, BooleanProperty,
    NumericProperty, ColorProperty
)
from kivy.clock import Clock

from ui.theme import C, SIZES


# ---------------------------------------------------------------------------
# Fond coloré générique
# ---------------------------------------------------------------------------
class QBg(Widget):
    """Widget avec fond uni."""
    bg_color = ColorProperty([0, 0, 0, 0])

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._bg_color = Color(*self.bg_color)
            self._bg_rect  = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=self._upd, size=self._upd,
            bg_color=self._upd_color
        )

    def _upd(self, *a):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def _upd_color(self, *a):
        self._bg_color.rgba = self.bg_color


# ---------------------------------------------------------------------------
# Label stylisé
# ---------------------------------------------------------------------------
class QLabel(Label):
    def __init__(self, text_color=None, font_size=13, bold=False, **kw):
        super().__init__(
            font_size=font_size,
            color=text_color or C['text_primary'],
            bold=bold,
            halign='left',
            valign='middle',
            shorten=True,
            shorten_from='right',
            **kw
        )
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))


class QMonoLabel(QLabel):
    """Label en police monospace."""
    def __init__(self, **kw):
        super().__init__(font_name='RobotoMono', font_size=10, **kw)


# ---------------------------------------------------------------------------
# Bouton stylisé QuantumPlay
# ---------------------------------------------------------------------------
class QButton(Button):
    """
    Bouton avec fond arrondi, bordure, couleurs QuantumPlay.
    active=True → couleur cyan accentuée.
    """
    active = BooleanProperty(False)

    def __init__(self,
                 bg=None,
                 bg_active=None,
                 border_color=None,
                 text_color=None,
                 radius=6,
                 **kw):
        self._q_bg           = bg           or C['bg_card']
        self._q_bg_active    = bg_active    or (*C['accent_cyan'][:3], 0.15)
        self._q_border       = border_color or C['border']
        self._q_text_color   = text_color   or C['text_secondary']
        self._radius         = radius

        kw.setdefault('background_color', (0, 0, 0, 0))
        kw.setdefault('background_normal', '')
        kw.setdefault('background_down', '')
        kw.setdefault('color', self._q_text_color)
        kw.setdefault('font_size', 12)

        super().__init__(**kw)

        with self.canvas.before:
            self._btn_border_color = Color(*self._q_border)
            self._btn_border = RoundedRectangle(
                pos=self.pos, size=self.size,
                radius=[self._radius]
            )
            self._btn_bg_color = Color(*self._q_bg)
            self._btn_bg = RoundedRectangle(
                pos=(self.x + 1, self.y + 1),
                size=(self.width - 2, self.height - 2),
                radius=[self._radius - 1]
            )

        self.bind(pos=self._upd, size=self._upd, active=self._upd_active)
        self.bind(on_press=self._on_press_anim, on_release=self._on_release_anim)

    def _upd(self, *a):
        self._btn_border.pos  = self.pos
        self._btn_border.size = self.size
        self._btn_bg.pos  = (self.x + 1, self.y + 1)
        self._btn_bg.size = (self.width - 2, self.height - 2)

    def _upd_active(self, *a):
        if self.active:
            self._btn_bg_color.rgba   = self._q_bg_active
            self._btn_border_color.rgba = C['accent_cyan']
            self.color = C['accent_cyan']
        else:
            self._btn_bg_color.rgba   = self._q_bg
            self._btn_border_color.rgba = self._q_border
            self.color = self._q_text_color

    def _on_press_anim(self, *a):
        self._btn_bg_color.rgba = (*C['accent_cyan'][:3], 0.1)

    def _on_release_anim(self, *a):
        Clock.schedule_once(lambda dt: self._upd_active(), 0.05)


# ---------------------------------------------------------------------------
# Bouton icône carré (topbar)
# ---------------------------------------------------------------------------
class QIconButton(QButton):
    def __init__(self, icon='?', size_px=28, **kw):
        super().__init__(
            text=icon,
            font_size=16,
            size_hint=(None, None),
            size=(size_px, size_px),
            radius=SIZES['radius'],
            **kw
        )


# ---------------------------------------------------------------------------
# Séparateur horizontal / vertical
# ---------------------------------------------------------------------------
class QSeparator(Widget):
    def __init__(self, orientation='horizontal', **kw):
        super().__init__(**kw)
        if orientation == 'horizontal':
            self.size_hint = (1, None)
            self.height = 1
        else:
            self.size_hint = (None, 1)
            self.width = 1

        with self.canvas:
            Color(*C['border'])
            self._line = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._line.pos  = self.pos
        self._line.size = self.size


# ---------------------------------------------------------------------------
# Badge tag (FLAC, HI-RES, etc.)
# ---------------------------------------------------------------------------
class QTag(Label):
    def __init__(self, text='', color=None, **kw):
        _c = color or C['accent_cyan']
        super().__init__(
            text=text,
            font_size=9,
            color=_c,
            size_hint=(None, None),
            padding=(6, 2),
            **kw
        )
        self.texture_update()
        self.size = (self.texture_size[0] + 12, 16)

        with self.canvas.before:
            Color(*_c[:3], 0.15)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[4])
            Color(*_c[:3], 0.5)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 4),
                width=0.8
            )
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, 4
        )


# ---------------------------------------------------------------------------
# Barre de progression interactive
# ---------------------------------------------------------------------------
class QProgressBar(Widget):
    """Barre de progression avec thumb interactif."""
    value    = NumericProperty(0)   # 0..100
    on_seek  = None                 # callback(pct: float)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (1, None)
        self.height = 4

        with self.canvas:
            # Fond
            Color(*C['bg_hover'])
            self._track = RoundedRectangle(pos=self.pos, size=self.size, radius=[2])
            # Fill
            Color(*C['accent_cyan'])
            self._fill = RoundedRectangle(pos=self.pos, size=(0, self.height), radius=[2])
            # Thumb
            Color(1, 1, 1, 0)   # invisible par défaut
            self._thumb = Ellipse(pos=self.pos, size=(12, 12))
            self._thumb_color = self.canvas.children[-2]  # Color avant Ellipse

        self.bind(pos=self._upd, size=self._upd, value=self._upd_value)
        self.register_event_type('on_seek')

    def _upd(self, *a):
        self._track.pos  = self.pos
        self._track.size = self.size
        self._upd_value()

    def _upd_value(self, *a):
        pct = max(0, min(100, self.value))
        fill_w = (pct / 100) * self.width
        self._fill.pos  = self.pos
        self._fill.size = (fill_w, self.height)
        # Thumb
        tx = self.x + fill_w - 6
        ty = self.y + self.height / 2 - 6
        self._thumb.pos = (tx, ty)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._seek(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self._seek(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        touch.ungrab(self)
        return super().on_touch_up(touch)

    def _seek(self, touch):
        touch.grab(self)
        pct = max(0, min(1, (touch.x - self.x) / self.width))
        self.value = pct * 100
        if self.on_seek:
            self.on_seek(pct)

    def on_seek(self, *a):
        pass


# ---------------------------------------------------------------------------
# Slider volume
# ---------------------------------------------------------------------------
class QVolumeSlider(QProgressBar):
    """Slider de volume (identique à la barre de progression)."""
    pass


# ---------------------------------------------------------------------------
# Card média (bibliothèque)
# ---------------------------------------------------------------------------
class QMediaCard(BoxLayout):
    def __init__(self, track, on_play=None, on_double=None, **kw):
        super().__init__(
            orientation='vertical',
            spacing=0,
            padding=0,
            size_hint=(None, None),
            size=(150, 190),
            **kw
        )
        self._track   = track
        self._on_play = on_play
        self._hover   = False

        with self.canvas.before:
            Color(*C['bg_card'])
            self._bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[SIZES['radius_lg']]
            )
            self._border_color = Color(*C['border'])
            self._border = Line(
                rounded_rectangle=(*self.pos, *self.size, SIZES['radius_lg']),
                width=1
            )
        self.bind(pos=self._upd, size=self._upd)

        # Vignette
        thumb = BoxLayout(
            size_hint=(1, None), height=150,
            padding=10
        )
        thumb.add_widget(Label(
            text=track.emoji,
            font_size=48,
            color=C['text_primary']
        ))
        self.add_widget(thumb)

        # Infos
        info = BoxLayout(
            orientation='vertical',
            size_hint=(1, None), height=40,
            padding=(8, 4)
        )
        info.add_widget(QLabel(
            text=track.title,
            font_size=11,
            size_hint=(1, None), height=18
        ))
        info.add_widget(QLabel(
            text=track.duration_str,
            font_size=10,
            text_color=C['text_muted'],
            size_hint=(1, None), height=14
        ))
        self.add_widget(info)

    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (*self.pos, *self.size, SIZES['radius_lg'])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap and self._on_play:
                self._on_play(self._track)
            return True
        return super().on_touch_down(touch)