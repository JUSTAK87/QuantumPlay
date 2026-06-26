"""
QuantumPlay — Barre de navigation latérale gauche
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.properties import StringProperty, BooleanProperty

from ui.theme import C, SIZES
from ui.widgets.base import QLabel, QSeparator


class NavItem(BoxLayout):
    """Élément de navigation dans la sidebar."""

    def __init__(self, icon='', text='', count=None,
                 active=False, sub=False,
                 on_press=None, **kw):
        super().__init__(
            orientation='horizontal',
            size_hint=(1, None),
            height=36,
            padding=(16 if not sub else 34, 0, 8, 0),
            spacing=10,
            **kw
        )
        self._on_press  = on_press
        self._active    = active
        self._sub       = sub

        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            # Bordure gauche active
            self._accent_color = Color(0, 0, 0, 0)
            self._accent = Rectangle(pos=self.pos, size=(2, self.height))
        self.bind(pos=self._upd, size=self._upd)

        # Icône
        self._icon_label = Label(
            text=icon,
            font_size=16 if not sub else 13,
            color=C['text_secondary'],
            size_hint=(None, 1),
            width=22,
            halign='center', valign='middle'
        )
        self.add_widget(self._icon_label)

        # Texte
        self._text_label = Label(
            text=text,
            font_size=13 if not sub else 12,
            color=C['text_secondary'],
            size_hint=(1, 1),
            halign='left', valign='middle'
        )
        self._text_label.bind(
            size=lambda *a: setattr(self._text_label, 'text_size', self._text_label.size)
        )
        self.add_widget(self._text_label)

        # Badge count
        self._count_label = None
        if count is not None:
            self._count_label = Label(
                text=str(count),
                font_size=10,
                color=C['accent_cyan'],
                size_hint=(None, None),
                size=(30, 16),
                halign='center', valign='middle'
            )
            with self._count_label.canvas.before:
                Color(*C['accent_cyan'][:3], 0.12)
                RoundedRectangle(
                    pos=self._count_label.pos,
                    size=self._count_label.size,
                    radius=[8]
                )
            self.add_widget(self._count_label)

        if active:
            self._set_active(True)

    def set_count(self, n: int):
        if self._count_label:
            self._count_label.text = str(n)

    def set_active(self, val: bool):
        self._active = val
        self._set_active(val)

    def _set_active(self, val: bool):
        if val:
            self._bg_color.rgba    = (*C['accent_cyan'][:3], 0.1)
            self._accent_color.rgba = C['accent_cyan']
            self._text_label.color  = C['accent_cyan']
            self._icon_label.color  = C['accent_cyan']
        else:
            self._bg_color.rgba    = (0, 0, 0, 0)
            self._accent_color.rgba = (0, 0, 0, 0)
            self._text_label.color  = C['text_secondary']
            self._icon_label.color  = C['text_secondary']

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._bg_color.rgba = (*C['accent_cyan'][:3], 0.08)
            if self._on_press:
                self._on_press(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._active:
            self._bg_color.rgba = (*C['accent_cyan'][:3], 0.1)
        else:
            self._bg_color.rgba = (0, 0, 0, 0)
        return super().on_touch_up(touch)

    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._accent.pos  = self.pos
        self._accent.size = (2, self.height)


class SectionTitle(Label):
    def __init__(self, text='', **kw):
        super().__init__(
            text=text.upper(),
            font_size=9,
            color=C['text_muted'],
            bold=True,
            size_hint=(1, None),
            height=24,
            halign='left', valign='middle',
            padding=(16, 0)
        )
        self.bind(size=lambda *a: setattr(self, 'text_size', self.size))


class Sidebar(BoxLayout):
    def __init__(self, main=None, **kw):
        super().__init__(orientation='vertical', spacing=0, **kw)
        self.main = main
        self._active_item = None
        self._nav_items: dict = {}

        with self.canvas.before:
            Color(*C['bg_surface'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*C['border'])
            self._border = Rectangle(
                pos=(self.right - 1, self.y),
                size=(1, self.height)
            )
        self.bind(pos=self._upd, size=self._upd)

        self._build()

    def _build(self):
        # Zone scrollable
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=(*C['accent_cyan'][:3], 0.3),
            bar_inactive_color=(*C['accent_cyan'][:3], 0.1)
        )

        nav_col = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=2,
            padding=(0, 8)
        )
        nav_col.bind(minimum_height=nav_col.setter('height'))

        def add(key, icon, text, count=None, sub=False, active=False):
            item = NavItem(
                icon=icon, text=text, count=count,
                active=active, sub=sub,
                on_press=lambda w: self._on_nav(key, w)
            )
            self._nav_items[key] = item
            nav_col.add_widget(item)

        nav_col.add_widget(SectionTitle('Navigation'))
        add('playlist', '▶',  'Lecture',      count=0, active=True)
        add('library',  '📚', 'Bibliothèque', count=0)
        add('history',  '🕐', 'Historique',   count=0)

        nav_col.add_widget(SectionTitle('Internet'))
        add('podcasts', '🎙️', 'Podcasts')

        nav_col.add_widget(QSeparator())
        nav_col.add_widget(SectionTitle('Périphériques'))
        add('dvd', '💿', 'DVD Rom')

        nav_col.add_widget(QSeparator())
        nav_col.add_widget(SectionTitle('Système'))
        add('eq',      '🎛️', 'Égaliseur')
        add('effects', '✨', 'Effets audio')
        add('tech',    '⚙️', 'Moteur audio')
        add('visuals', '🌊', 'Visualisations')

        # Spacer
        nav_col.add_widget(Widget(size_hint_y=1))

        scroll.add_widget(nav_col)
        self.add_widget(scroll)

    def _on_nav(self, key: str, widget: NavItem):
        # Désactiver l'ancien item
        if self._active_item:
            self._active_item.set_active(False)
        widget.set_active(True)
        self._active_item = widget

        # Router vers le bon panel
        if self.main:
            self.main.main_panel.show_section(key)

    def update_counts(self, play=0, lib=0, history=0):
        for key, val in [('playlist', play), ('library', lib), ('history', history)]:
            if key in self._nav_items:
                self._nav_items[key].set_count(val)

    def _upd(self, *a):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._border.pos  = (self.right - 1, self.y)
        self._border.size = (1, self.height)