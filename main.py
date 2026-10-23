# -*- coding: utf-8 -*-
"""
SPIS GIER - aplikacja do prowadzenia statystyk gier (Kivy / Android).

Ekrany:
  start     - wybór / utworzenie pliku statystyk (gdy brak ostatniego pliku)
  main      - karta główna: spis gier
  game      - karta gry: ranking uczestników, lista rozgrywek
  round     - karta rozgrywki: tabela wyników
"""
import json
import os

from kivy.config import Config

Config.set("kivy", "exit_on_escape", "0")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.utils import platform

import storage
from storage import fmt_number, parse_number
from theme import C, darker, player_color

APP_TITLE = "Spis gier"
INITIAL_ROWS = 10
MAX_PLAYERS = 12

KV = """
#:import C theme.C

<FlatButton>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: root.fg
    font_size: '16sp'
    bold: True
    size_hint_y: None
    height: dp(50)
    halign: 'center'
    valign: 'middle'
    text_size: self.width - dp(8), None
    canvas.before:
        Color:
            rgba: root.bg if self.state == 'normal' else root.bg_down
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<ChoiceButton>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: C['dark'] if self.state == 'down' else C['text']
    font_size: '15sp'
    size_hint_y: None
    height: dp(44)
    text_size: self.width - dp(8), None
    halign: 'center'
    canvas.before:
        Color:
            rgba: C['gold'] if self.state == 'down' else C['surface2']
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]

<Txt>:
    color: C['text']
    font_size: '16sp'
    size_hint_y: None
    text_size: self.width, None
    height: self.texture_size[1]
    halign: 'left'
    valign: 'middle'
    markup: True

<RowLbl>:
    color: C['text']
    font_size: '16sp'
    markup: True
    text_size: self.size
    halign: 'left'
    valign: 'middle'
    shorten: True
    shorten_from: 'right'

<Cell>:
    color: root.fg
    font_size: '15sp'
    bold: True
    halign: 'center'
    valign: 'middle'
    text_size: self.width - dp(6), self.height
    shorten: True
    shorten_from: 'right'
    canvas.before:
        Color:
            rgba: root.bg
        Rectangle:
            pos: self.x + dp(1), self.y + dp(1)
            size: self.width - dp(2), self.height - dp(2)

<Card>:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(4)
    size_hint_y: None
    canvas.before:
        Color:
            rgba: root.bg if self.state == 'normal' else C['surface2']
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: root.border
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(14))
            width: dp(1.2)

<Panel>:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(6)
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: root.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: root.border
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(14))
            width: dp(1.2)

<Field>:
    multiline: False
    write_tab: False
    font_size: '17sp'
    size_hint_y: None
    height: dp(46)
    padding: [dp(10), (self.height - self.line_height) / 2.0]
    background_normal: ''
    background_active: ''
    background_color: C['field']
    foreground_color: C['text']
    cursor_color: C['gold']
    hint_text_color: C['muted']
    selection_color: C['gold'][0], C['gold'][1], C['gold'][2], 0.4

<ScoreField>:
    halign: 'center'
    font_size: '17sp'
    padding: [dp(4), (self.height - self.line_height) / 2.0]

<TopBar>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(16), dp(14), dp(16), dp(10)
    spacing: dp(2)
    canvas.before:
        Color:
            rgba: C['surface']
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: C['gold']
        Rectangle:
            pos: self.x, self.y
            size: self.width, dp(2)

<BottomBar>:
    size_hint_y: None
    height: dp(74)
    padding: dp(12)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: C['surface']
        Rectangle:
            pos: self.pos
            size: self.size
"""


# ==========================================================================
# Widżety bazowe
# ==========================================================================
class FlatButton(Button):
    bg = ListProperty(C["surface2"])
    bg_down = ListProperty(darker(C["surface2"]))
    fg = ListProperty(C["text"])

    def on_bg(self, *_):
        self.bg_down = darker(self.bg)

    def __init__(self, **kw):
        super(FlatButton, self).__init__(**kw)
        self.on_bg()


def GoldButton(**kw):
    kw.setdefault("bg", C["gold"])
    kw.setdefault("fg", C["dark"])
    return FlatButton(**kw)


def RedButton(**kw):
    kw.setdefault("bg", C["red"])
    return FlatButton(**kw)


class ChoiceButton(ToggleButton):
    pass


class Txt(Label):
    pass


class Cell(Label):
    bg = ListProperty(C["surface"])
    fg = ListProperty(C["text"])


class Card(ButtonBehavior, BoxLayout):
    """Klikalna karta. Bez fixed_height wysokość dopasowuje się do treści."""
    bg = ListProperty(C["surface"])
    border = ListProperty(C["line"])

    def __init__(self, fixed_height=None, **kw):
        super(Card, self).__init__(**kw)
        if fixed_height is not None:
            self.height = fixed_height
        else:
            self.bind(minimum_height=self.setter("height"))


class RowLbl(Label):
    """Etykieta wypełniająca przydzielone miejsce (do wierszy tabel)."""
    pass


class Panel(BoxLayout):
    bg = ListProperty(C["surface"])
    border = ListProperty(C["line"])


class Field(TextInput):
    pass


class ScoreField(Field):
    """Pole wyniku - cyfry, minus, plus, przecinek, kropka."""
    invalid = BooleanProperty(False)
    ALLOWED = set("0123456789-+.,")

    def insert_text(self, substring, from_undo=False):
        s = "".join(ch for ch in substring if ch in self.ALLOWED)
        return super(ScoreField, self).insert_text(s, from_undo=from_undo)

    def on_invalid(self, *_):
        self.background_color = C["invalid"] if self.invalid else C["field"]


class TopBar(BoxLayout):
    pass


class BottomBar(BoxLayout):
    pass


def esc(text):
    """Zabezpieczenie tekstu przed interpretacją jako markup Kivy."""
    return (text or "").replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def hexcol(color):
    return "%02x%02x%02x" % tuple(int(max(0, min(1, x)) * 255) for x in color[:3])


def app():
    return App.get_running_app()


# ==========================================================================
# Okna dialogowe
# ==========================================================================
def make_popup(title, content, height=None, size_hint=(0.92, None), auto_dismiss=True):
    p = Popup(title=title, content=content, size_hint=size_hint,
              auto_dismiss=auto_dismiss,
              title_color=C["gold"], title_size="18sp",
              separator_color=C["gold"], separator_height=dp(2),
              background="", background_color=C["surface"],
              overlay_color=(0, 0, 0, 0.6))
    if height is not None:
        p.height = height
    return p


def message(title, text):
    box = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(6))
    box.add_widget(Txt(text=esc(text)))
    box.add_widget(Widget())
    p = make_popup(title, box, height=dp(240))
    btn = GoldButton(text="OK")
    btn.bind(on_release=lambda *_: p.dismiss())
    box.add_widget(btn)
    p.open()
    return p


def ask(title, text, buttons, auto_dismiss=False):
    """buttons: lista (etykieta, callback, rodzaj) gdzie rodzaj: gold/red/plain."""
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(6))
    box.add_widget(Txt(text=esc(text)))
    box.add_widget(Widget())
    p = make_popup(title, box, height=dp(170) + dp(60) * len(buttons),
                   auto_dismiss=auto_dismiss)
    for label, cb, kind in buttons:
        maker = {"gold": GoldButton, "red": RedButton}.get(kind, FlatButton)
        b = maker(text=label)

        def handler(_btn, cb=cb):
            p.dismiss()
            if cb:
                cb()
        b.bind(on_release=handler)
        box.add_widget(b)
    p.open()
    return p


def ask_text(title, label, initial, on_ok, ok_text="Zapisz"):
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(6))
    box.add_widget(Txt(text=esc(label), color=C["muted"]))
    field = Field(text=initial)
    box.add_widget(field)
    err = Txt(text="", color=C["red"], font_size="14sp")
    box.add_widget(err)
    box.add_widget(Widget())
    row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    p = make_popup(title, box, height=dp(300))
    cancel = FlatButton(text="Anuluj")
    ok = GoldButton(text=ok_text)
    cancel.bind(on_release=lambda *_: p.dismiss())

    def do_ok(*_):
        v = field.text.strip()
        if not v:
            err.text = "Nazwa nie może być pusta."
            return
        p.dismiss()
        on_ok(v)
    ok.bind(on_release=do_ok)
    field.bind(on_text_validate=do_ok)
    row.add_widget(cancel)
    row.add_widget(ok)
    box.add_widget(row)
    p.open()
    Clock.schedule_once(lambda dt: setattr(field, "focus", True), 0.25)
    return p


class FileDialog(object):
    """Wybór istniejącego pliku (mode='open') albo folderu i nazwy nowego
    pliku (mode='new')."""

    def __init__(self, mode, on_done):
        self.mode = mode
        self.on_done = on_done
        a = app()
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(4))

        quick = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        for label, path in a.quick_dirs():
            b = FlatButton(text=label, height=dp(44), font_size="14sp")
            b.bind(on_release=lambda _b, p=path: self.go_to(p))
            quick.add_widget(b)
        box.add_widget(quick)

        self.path_lbl = Txt(text="", color=C["muted"], font_size="13sp")
        box.add_widget(self.path_lbl)

        start = a.last_dir() or a.default_dir()
        self.fc = FileChooserListView(path=start, filters=["*.csv", "*.CSV"],
                                      dirselect=False, size_hint_y=1)
        self.fc.bind(path=self._update_path, on_submit=self._on_submit,
                     selection=self._on_selection)
        box.add_widget(self.fc)

        self.name_in = None
        if mode == "new":
            box.add_widget(Txt(text="Nazwa nowego pliku (zapisany w folderze powyżej):",
                               color=C["muted"], font_size="14sp"))
            self.name_in = Field(text="statystyki.csv")
            box.add_widget(self.name_in)

        self.err = Txt(text="", color=C["red"], font_size="14sp")
        box.add_widget(self.err)

        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel = FlatButton(text="Anuluj")
        ok = GoldButton(text="Otwórz" if mode == "open" else "Utwórz")
        cancel.bind(on_release=lambda *_: self.popup.dismiss())
        ok.bind(on_release=self._ok)
        row.add_widget(cancel)
        row.add_widget(ok)
        box.add_widget(row)

        title = "Otwórz plik statystyk" if mode == "open" else "Nowy plik statystyk"
        self.popup = make_popup(title, box, size_hint=(0.96, 0.9))
        self._update_path()
        self.popup.open()

    def go_to(self, path):
        try:
            if not os.path.isdir(path):
                os.makedirs(path)
            self.fc.path = path
        except Exception as e:
            self.err.text = "Brak dostępu do folderu: %s" % e

    def _update_path(self, *_):
        self.path_lbl.text = esc(self.fc.path)

    def _on_selection(self, *_):
        if self.mode == "new" and self.fc.selection:
            sel = self.fc.selection[0]
            if os.path.isfile(sel):
                self.name_in.text = os.path.basename(sel)

    def _on_submit(self, _fc, selection, _touch):
        if self.mode == "open" and selection:
            self._ok()

    def _ok(self, *_):
        if self.mode == "open":
            if not self.fc.selection or not os.path.isfile(self.fc.selection[0]):
                self.err.text = "Zaznacz plik .csv na liście."
                return
            path = self.fc.selection[0]
            self.popup.dismiss()
            self.on_done(path)
        else:
            name = (self.name_in.text or "").strip()
            if not name:
                self.err.text = "Podaj nazwę pliku."
                return
            if not name.lower().endswith(".csv"):
                name += ".csv"
            path = os.path.join(self.fc.path, name)
            if os.path.exists(path):
                def overwrite():
                    self.popup.dismiss()
                    self.on_done(path, overwrite=True)

                def open_existing():
                    self.popup.dismiss()
                    app().open_path(path)
                ask("Plik istnieje",
                    "Plik %s już istnieje. Co zrobić?" % name,
                    [("Otwórz istniejący", open_existing, "gold"),
                     ("Nadpisz (utrata danych)", overwrite, "red"),
                     ("Anuluj", None, "plain")])
                return
            self.popup.dismiss()
            self.on_done(path)


class NewGameDialog(object):
    def __init__(self):
        self.count = 2
        self.fields = []
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(4))

        box.add_widget(Txt(text="Nazwa gry", color=C["muted"], font_size="14sp"))
        self.name_in = Field(hint_text="np. Tysiąc, Scrabble, Rummikub")
        box.add_widget(self.name_in)

        cnt_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        cnt_row.add_widget(Txt(text="Liczba uczestników", color=C["muted"],
                               font_size="14sp", size_hint_y=1, height=dp(48)))
        minus = FlatButton(text="-", size_hint_x=None, width=dp(50), height=dp(48),
                           font_size="22sp")
        self.cnt_lbl = Txt(text="2", halign="center", size_hint=(None, 1),
                           width=dp(40), font_size="20sp", bold=True)
        plus = FlatButton(text="+", size_hint_x=None, width=dp(50), height=dp(48),
                          font_size="22sp")
        minus.bind(on_release=lambda *_: self.set_count(self.count - 1))
        plus.bind(on_release=lambda *_: self.set_count(self.count + 1))
        cnt_row.add_widget(minus)
        cnt_row.add_widget(self.cnt_lbl)
        cnt_row.add_widget(plus)
        box.add_widget(cnt_row)

        sv = ScrollView(do_scroll_x=False, size_hint_y=1)
        self.players_box = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.players_box.bind(minimum_height=self.players_box.setter("height"))
        sv.add_widget(self.players_box)
        box.add_widget(sv)

        box.add_widget(Txt(text="Kto wygrywa rozgrywkę?", color=C["muted"],
                           font_size="14sp"))
        mode_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.mode_max = ChoiceButton(text="Najwięcej punktów", group="winmode",
                                     state="down", allow_no_selection=False)
        self.mode_min = ChoiceButton(text="Najmniej punktów", group="winmode",
                                     allow_no_selection=False)
        mode_row.add_widget(self.mode_max)
        mode_row.add_widget(self.mode_min)
        box.add_widget(mode_row)

        self.err = Txt(text="", color=C["red"], font_size="14sp")
        box.add_widget(self.err)

        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel = FlatButton(text="Anuluj")
        ok = GoldButton(text="Utwórz grę")
        cancel.bind(on_release=lambda *_: self.popup.dismiss())
        ok.bind(on_release=self._ok)
        row.add_widget(cancel)
        row.add_widget(ok)
        box.add_widget(row)

        self.popup = make_popup("Nowa gra", box, size_hint=(0.95, 0.92))
        self.set_count(2)
        self.popup.open()

    def set_count(self, n):
        n = max(1, min(MAX_PLAYERS, n))
        self.count = n
        self.cnt_lbl.text = str(n)
        while len(self.fields) < n:
            i = len(self.fields)
            row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
            dot = Cell(text=str(i + 1), bg=player_color(i), fg=C["dark"],
                       size_hint_x=None, width=dp(34))
            f = Field(hint_text="Imię uczestnika %d" % (i + 1))
            row.add_widget(dot)
            row.add_widget(f)
            self.fields.append((row, f))
            self.players_box.add_widget(row)
        while len(self.fields) > n:
            row, _f = self.fields.pop()
            self.players_box.remove_widget(row)

    def _ok(self, *_):
        name = self.name_in.text.strip()
        players = [f.text.strip() for _r, f in self.fields]
        if not name:
            self.err.text = "Podaj nazwę gry."
            return
        if any(not p for p in players):
            self.err.text = "Podaj imiona wszystkich uczestników."
            return
        if len(set(p.lower() for p in players)) != len(players):
            self.err.text = "Imiona uczestników muszą być różne."
            return
        mode = "min" if self.mode_min.state == "down" else "max"
        self.popup.dismiss()
        app().add_game(name, players, mode)


# ==========================================================================
# Ekran startowy
# ==========================================================================
class StartScreen(Screen):
    def __init__(self, **kw):
        super(StartScreen, self).__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(28), spacing=dp(14))
        root.add_widget(Widget())
        root.add_widget(Txt(text="[b]SPIS GIER[/b]", font_size="38sp",
                            halign="center", color=C["gold"]))
        root.add_widget(Txt(text="statystyki Twoich rozgrywek", halign="center",
                            color=C["muted"]))
        root.add_widget(Widget(size_hint_y=None, height=dp(20)))
        self.msg = Txt(text="", halign="center", font_size="15sp")
        root.add_widget(self.msg)
        root.add_widget(Widget(size_hint_y=None, height=dp(10)))
        b1 = FlatButton(text="Wskaż istniejący plik")
        b2 = GoldButton(text="Utwórz nowy plik")
        b3 = FlatButton(text="Zamknij program", bg=C["surface"])
        b1.bind(on_release=lambda *_: app().open_file_dialog())
        b2.bind(on_release=lambda *_: app().new_file_dialog())
        b3.bind(on_release=lambda *_: app().quit())
        root.add_widget(b1)
        root.add_widget(b2)
        root.add_widget(b3)
        root.add_widget(Widget())
        self.add_widget(root)

    def set_message(self, text):
        self.msg.text = esc(text)

    def on_back(self):
        app().quit()


# ==========================================================================
# Karta główna
# ==========================================================================
class MainScreen(Screen):
    def __init__(self, **kw):
        super(MainScreen, self).__init__(**kw)
        root = BoxLayout(orientation="vertical")

        top = TopBar()
        head = BoxLayout(size_hint_y=None, height=dp(44))
        head.add_widget(Txt(text="[b]SPIS GIER[/b]", font_size="24sp",
                            color=C["gold"], size_hint_y=1))
        fbtn = FlatButton(text="Plik", size_hint_x=None, width=dp(76),
                          height=dp(40), font_size="14sp", pos_hint={"center_y": 0.5})
        fbtn.bind(on_release=lambda *_: self.file_menu())
        head.add_widget(fbtn)
        top.add_widget(head)
        self.file_lbl = Txt(text="", color=C["muted"], font_size="13sp")
        top.add_widget(self.file_lbl)
        root.add_widget(top)

        sv = ScrollView(do_scroll_x=False)
        self.list = GridLayout(cols=1, spacing=dp(10), padding=dp(12), size_hint_y=None)
        self.list.bind(minimum_height=self.list.setter("height"))
        sv.add_widget(self.list)
        root.add_widget(sv)

        bottom = BottomBar()
        add = GoldButton(text="+ Nowa gra")
        close = FlatButton(text="Zamknij")
        add.bind(on_release=lambda *_: NewGameDialog())
        close.bind(on_release=lambda *_: app().quit())
        bottom.add_widget(add)
        bottom.add_widget(close)
        root.add_widget(bottom)
        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        a = app()
        self.file_lbl.text = esc(a.path or "")
        self.list.clear_widgets()
        if not a.data.games:
            self.list.add_widget(Widget(size_hint_y=None, height=dp(60)))
            self.list.add_widget(Txt(
                text="Nie ma jeszcze żadnej gry.\nDodaj pierwszą przyciskiem [b]+ Nowa gra[/b].",
                halign="center", color=C["muted"]))
            return
        for g in a.data.games:
            self.list.add_widget(self._game_card(g))

    def _game_card(self, g):
        card = Card()
        card.add_widget(Txt(text="[b]%s[/b]" % esc(g.name), font_size="20sp"))
        names = "  ".join("[color=%s]%s[/color]" % (hexcol(player_color(i)), esc(p))
                          for i, p in enumerate(g.players))
        card.add_widget(Txt(text=names, font_size="15sp"))
        leaders = g.leaders()
        info = "Rozgrywek: [b]%d[/b]" % len(g.rounds)
        if leaders:
            lead = ", ".join(esc(g.players[i]) for i in leaders)
            info += "   ·   Prowadzi: [color=%s][b]%s[/b][/color]" % (hexcol(C["gold"]), lead)
        card.add_widget(Txt(text=info, font_size="14sp", color=C["muted"]))
        card.bind(on_release=lambda *_: app().open_game(g))
        return card

    def file_menu(self):
        a = app()
        ask("Plik statystyk",
            "Bieżący plik:\n%s" % (a.path or "-"),
            [("Otwórz inny plik", a.open_file_dialog, "plain"),
             ("Utwórz nowy plik", a.new_file_dialog, "plain"),
             ("Anuluj", None, "plain")], auto_dismiss=True)

    def on_back(self):
        app().quit()


# ==========================================================================
# Karta gry
# ==========================================================================
class GameScreen(Screen):
    game = None

    def __init__(self, **kw):
        super(GameScreen, self).__init__(**kw)
        root = BoxLayout(orientation="vertical")

        top = TopBar()
        self.title_lbl = Txt(text="", font_size="22sp", color=C["gold"])
        top.add_widget(self.title_lbl)
        self.sub_lbl = Txt(text="", font_size="14sp", color=C["muted"])
        top.add_widget(self.sub_lbl)
        tools = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        ren = FlatButton(text="Zmień nazwę", height=dp(38), font_size="14sp")
        dele = FlatButton(text="Usuń grę", height=dp(38), font_size="14sp",
                          bg=C["red_dark"])
        ren.bind(on_release=lambda *_: self.rename_game())
        dele.bind(on_release=lambda *_: self.delete_game())
        tools.add_widget(ren)
        tools.add_widget(dele)
        top.add_widget(Widget(size_hint_y=None, height=dp(6)))
        top.add_widget(tools)
        root.add_widget(top)

        sv = ScrollView(do_scroll_x=False)
        self.content = GridLayout(cols=1, spacing=dp(10), padding=dp(12), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        sv.add_widget(self.content)
        root.add_widget(sv)

        bottom = BottomBar()
        add = GoldButton(text="+ Rozgrywka")
        save = FlatButton(text="Zapisz")
        close = FlatButton(text="Zamknij")
        add.bind(on_release=lambda *_: app().open_round(self.game, None))
        save.bind(on_release=lambda *_: self.save())
        close.bind(on_release=lambda *_: self.close())
        bottom.add_widget(add)
        bottom.add_widget(save)
        bottom.add_widget(close)
        root.add_widget(bottom)
        self.add_widget(root)

    def set_game(self, game):
        self.game = game

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        g = self.game
        if g is None:
            return
        self.title_lbl.text = "[b]%s[/b]" % esc(g.name)
        mode = "najwięcej punktów" if g.win_mode == "max" else "najmniej punktów"
        self.sub_lbl.text = "Rozegrane rozgrywki: [b]%d[/b]   ·   wygrywa: %s" % (
            len(g.rounds), mode)
        self.content.clear_widgets()

        # ---- ranking ----
        panel = Panel()
        panel.add_widget(Txt(text="[b]KLASYFIKACJA[/b]", font_size="14sp", color=C["muted"]))
        totals = g.totals()
        wins = g.wins()
        leaders = set(g.leaders())
        order = sorted(range(len(g.players)), key=lambda i: totals[i],
                       reverse=(g.win_mode == "max"))
        hdr = BoxLayout(size_hint_y=None, height=dp(22), spacing=dp(8))
        hdr.add_widget(Widget(size_hint_x=None, width=dp(32)))
        hdr.add_widget(RowLbl(text="uczestnik", font_size="12sp", color=C["muted"]))
        hdr.add_widget(RowLbl(text="wygrane", font_size="12sp", color=C["muted"],
                              size_hint_x=None, width=dp(70), halign="center"))
        hdr.add_widget(RowLbl(text="punkty", font_size="12sp", color=C["muted"],
                              size_hint_x=None, width=dp(90), halign="right"))
        panel.add_widget(hdr)
        for place, i in enumerate(order, start=1):
            is_lead = i in leaders
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            row.add_widget(Cell(text=str(place), bg=player_color(i), fg=C["dark"],
                                size_hint_x=None, width=dp(32)))
            name = esc(g.players[i])
            if is_lead:
                name = "[b]%s[/b]  [color=%s][size=12sp]LIDER[/size][/color]" % (
                    name, hexcol(C["gold"]))
            row.add_widget(RowLbl(text=name, font_size="17sp"))
            row.add_widget(RowLbl(text=str(wins[i]), size_hint_x=None, width=dp(70),
                                  halign="center", color=C["muted"]))
            row.add_widget(RowLbl(text="[b]%s[/b]" % fmt_number(totals[i]),
                                  size_hint_x=None, width=dp(90), halign="right",
                                  font_size="19sp",
                                  color=C["gold"] if is_lead else C["text"]))
            panel.add_widget(row)
        if leaders:
            panel.border = C["gold"]
        self.content.add_widget(panel)

        # ---- lista rozgrywek ----
        self.content.add_widget(Txt(text="[b]ROZGRYWKI[/b]  (najnowsze na górze)",
                                    font_size="14sp", color=C["muted"]))
        if not g.rounds:
            self.content.add_widget(Txt(
                text="Brak rozgrywek. Dodaj pierwszą przyciskiem [b]+ Rozgrywka[/b].",
                color=C["muted"], halign="center"))
        for rnd in reversed(g.rounds):
            self.content.add_widget(self._round_card(rnd))

    def _round_card(self, rnd):
        g = self.game
        nr = g.round_number(rnd)
        card = Card(orientation="horizontal", spacing=dp(8), padding=dp(12),
                    fixed_height=dp(96))
        left = BoxLayout(orientation="vertical", spacing=dp(2))
        left.add_widget(RowLbl(text="[b]Nr %d[/b]   %s" % (nr, esc(rnd.name)),
                               font_size="17sp"))
        winners = g.round_winners(rnd)
        if winners:
            t = rnd.totals(len(g.players))
            wtxt = ", ".join(esc(g.players[i]) for i in winners)
            label = "Zwycięzca" if len(winners) == 1 else "Remis"
            left.add_widget(RowLbl(text="%s: [color=%s][b]%s[/b][/color] (%s)" % (
                label, hexcol(C["gold"]), wtxt, fmt_number(t[winners[0]])),
                font_size="14sp"))
        else:
            left.add_widget(RowLbl(text="brak wyników", font_size="14sp", color=C["muted"]))
        left.add_widget(RowLbl(text=esc(rnd.created), font_size="12sp", color=C["muted"]))
        card.add_widget(left)
        btns = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_x=None,
                         width=dp(84))
        ren = FlatButton(text="Nazwa", height=dp(32), font_size="13sp")
        dele = FlatButton(text="Usuń", height=dp(32), font_size="13sp", bg=C["red_dark"])
        ren.bind(on_release=lambda *_: self.rename_round(rnd))
        dele.bind(on_release=lambda *_: self.delete_round(rnd))
        btns.add_widget(ren)
        btns.add_widget(dele)
        card.add_widget(btns)
        card.bind(on_release=lambda *_: app().open_round(g, rnd))
        return card

    # ---- akcje ----
    def rename_game(self):
        def done(v):
            self.game.name = v
            app().save()
            self.refresh()
        ask_text("Zmień nazwę gry", "Nowa nazwa gry:", self.game.name, done)

    def delete_game(self):
        def do():
            app().data.games.remove(self.game)
            app().save()
            self.game = None
            app().go("main", "right")
        ask("Usuń grę",
            "Czy na pewno usunąć grę „%s” razem ze wszystkimi rozgrywkami (%d)?"
            % (self.game.name, len(self.game.rounds)),
            [("Usuń", do, "red"), ("Anuluj", None, "plain")])

    def rename_round(self, rnd):
        def done(v):
            rnd.name = v
            app().save()
            self.refresh()
        ask_text("Zmień nazwę rozgrywki", "Nowa nazwa rozgrywki:", rnd.name, done)

    def delete_round(self, rnd):
        def do():
            self.game.rounds.remove(rnd)
            app().save()
            self.refresh()
        ask("Usuń rozgrywkę",
            "Czy na pewno usunąć rozgrywkę nr %d „%s”?"
            % (self.game.round_number(rnd), rnd.name),
            [("Usuń", do, "red"), ("Anuluj", None, "plain")])

    def save(self):
        if app().save():
            message("Zapisano", "Statystyki zapisane do pliku.")

    def close(self):
        app().save()
        app().go("main", "right")

    def on_back(self):
        self.close()


# ==========================================================================
# Karta rozgrywki
# ==========================================================================
class RoundScreen(Screen):
    ROWNUM_W = dp(40)
    ROW_H = dp(46)
    MIN_COL_W = dp(86)

    def __init__(self, **kw):
        super(RoundScreen, self).__init__(**kw)
        self.game = None
        self.rnd = None
        self.is_new = False
        self.dirty = False
        self._loading = False
        self.cells = []
        self.round_name = ""

        self.root_box = BoxLayout(orientation="vertical")
        top = TopBar()
        self.game_lbl = Txt(text="", font_size="14sp", color=C["muted"])
        top.add_widget(self.game_lbl)
        line = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        self.title_lbl = Txt(text="", font_size="20sp", color=C["gold"], size_hint_y=1,
                             shorten=True)
        line.add_widget(self.title_lbl)
        ren = FlatButton(text="Nazwa", size_hint_x=None, width=dp(84), height=dp(38),
                         font_size="14sp", pos_hint={"center_y": 0.5})
        ren.bind(on_release=lambda *_: self.rename())
        line.add_widget(ren)
        top.add_widget(line)
        self.root_box.add_widget(top)

        self.table_holder = BoxLayout(padding=(dp(8), dp(8), dp(8), 0))
        self.root_box.add_widget(self.table_holder)

        bottom = BottomBar()
        back = FlatButton(text="Wróć")
        save = GoldButton(text="Zapisz rozgrywkę")
        back.bind(on_release=lambda *_: self.on_back())
        save.bind(on_release=lambda *_: self.save_round())
        bottom.add_widget(back)
        bottom.add_widget(save)
        self.root_box.add_widget(bottom)
        self.add_widget(self.root_box)

    # ---- budowa tabeli ----
    def load(self, game, rnd):
        self.game = game
        self.rnd = rnd
        self.is_new = rnd is None
        nr = len(game.rounds) + 1 if self.is_new else game.round_number(rnd)
        self.round_name = game.default_round_name() if self.is_new else rnd.name
        self.nr = nr
        self.game_lbl.text = esc(game.name)
        self._update_title()
        self._build_table()
        self._loading = True
        if rnd is not None:
            for (r, c), v in rnd.scores.items():
                while r >= len(self.cells):
                    self._add_row()
                if c < len(game.players):
                    self.cells[r][c].text = fmt_number(v)
        self._loading = False
        self.dirty = False
        self._recalc()

    def _update_title(self):
        self.title_lbl.text = "[b]Nr %d[/b]  ·  %s" % (self.nr, esc(self.round_name))

    def _build_table(self):
        self.table_holder.clear_widgets()
        n = len(self.game.players)
        avail = Window.width - dp(16)
        col_w = max(self.MIN_COL_W, (avail - self.ROWNUM_W) / float(n))
        self.col_w = col_w
        total_w = self.ROWNUM_W + col_w * n
        cols = n + 1

        table = BoxLayout(orientation="vertical", size_hint_x=None, width=total_w)

        # nagłówek: imiona + sumy (zawsze widoczne)
        header = GridLayout(cols=cols, size_hint=(None, None), width=total_w,
                            height=self.ROW_H * 2, row_force_default=True,
                            row_default_height=self.ROW_H)
        header.add_widget(Cell(text="", bg=C["surface"], size_hint_x=None,
                               width=self.ROWNUM_W))
        for i, p in enumerate(self.game.players):
            header.add_widget(Cell(text=p, bg=player_color(i), fg=C["dark"],
                                   size_hint_x=None, width=col_w))
        header.add_widget(Cell(text="Σ", bg=C["surface"], fg=C["muted"],
                               size_hint_x=None, width=self.ROWNUM_W))
        self.sum_cells = []
        for i in range(n):
            c = Cell(text="0", bg=C["surface2"], size_hint_x=None, width=col_w,
                     font_size="18sp")
            self.sum_cells.append(c)
            header.add_widget(c)
        table.add_widget(header)

        # treść: przewijane wiersze wyników
        self.body_sv = ScrollView(do_scroll_x=False, size_hint=(None, 1), width=total_w,
                                  bar_width=dp(4), bar_color=C["gold"])
        self.body = GridLayout(cols=cols, size_hint=(None, None), width=total_w,
                               row_force_default=True, row_default_height=self.ROW_H)
        self.body.bind(minimum_height=self.body.setter("height"))
        self.body_sv.add_widget(self.body)
        table.add_widget(self.body_sv)

        self.cells = []
        for _ in range(INITIAL_ROWS):
            self._add_row()

        if total_w > avail + 1:
            outer = ScrollView(do_scroll_y=False, bar_width=dp(4), bar_color=C["gold"])
            table.size_hint_y = 1
            outer.add_widget(table)
            self.table_holder.add_widget(outer)
        else:
            self.table_holder.add_widget(table)

    def _add_row(self):
        r = len(self.cells)
        self.body.add_widget(Cell(text=str(r + 1), bg=C["bg"], fg=C["muted"],
                                  size_hint_x=None, width=self.ROWNUM_W,
                                  font_size="13sp", bold=False))
        row = []
        for c in range(len(self.game.players)):
            f = ScoreField(size_hint_x=None, width=self.col_w, height=self.ROW_H)
            f.bind(text=lambda inst, val, r=r: self._on_cell_text(inst, r))
            self.body.add_widget(f)
            row.append(f)
        self.cells.append(row)

    def _on_cell_text(self, field, r):
        try:
            parse_number(field.text)
            field.invalid = False
        except ValueError:
            field.invalid = True
        if not self._loading:
            self.dirty = True
        if r == len(self.cells) - 1 and field.text.strip():
            self._add_row()
        self._recalc()

    def _collect(self):
        """Zwraca (scores, liczba_błędnych)."""
        scores = {}
        bad = 0
        for r, row in enumerate(self.cells):
            for c, f in enumerate(row):
                try:
                    v = parse_number(f.text)
                except ValueError:
                    bad += 1
                    continue
                if v is not None:
                    scores[(r, c)] = v
        return scores, bad

    def _recalc(self):
        if not getattr(self, "sum_cells", None):
            return
        scores, _bad = self._collect()
        n = len(self.game.players)
        tmp = storage.Round(scores=scores)
        totals = tmp.totals(n)
        winners = set(self.game.round_winners(tmp))
        for i, cell in enumerate(self.sum_cells):
            cell.text = fmt_number(totals[i])
            if i in winners:
                cell.bg = C["gold"]
                cell.fg = C["dark"]
            else:
                cell.bg = C["surface2"]
                cell.fg = C["text"]

    # ---- akcje ----
    def rename(self):
        def done(v):
            self.round_name = v
            self.dirty = True
            self._update_title()
        ask_text("Nazwa rozgrywki", "Nazwa tej rozgrywki:", self.round_name, done,
                 ok_text="OK")

    def save_round(self):
        scores, bad = self._collect()
        if bad:
            message("Błędne wartości",
                    "W tabeli jest %d błędnych wartości (zaznaczone na czerwono). "
                    "Popraw je przed zapisaniem." % bad)
            return False
        if self.is_new:
            rnd = storage.Round(name=self.round_name, scores=scores)
            self.game.rounds.append(rnd)
        else:
            self.rnd.name = self.round_name
            self.rnd.scores = scores
        self.dirty = False
        app().save()
        app().go("game", "right")
        return True

    def discard(self):
        self.dirty = False
        app().go("game", "right")

    def on_back(self):
        if not self.dirty:
            self.discard()
            return
        ask("Zapisać?",
            "Rozgrywka zawiera niezapisane zmiany. Zapisać je?",
            [("Zapisz", self.save_round, "gold"),
             ("Nie zapisuj", self.discard, "red"),
             ("Anuluj", None, "plain")])


# ==========================================================================
# Aplikacja
# ==========================================================================
class SpisGierApp(App):
    title = APP_TITLE

    def build(self):
        Builder.load_string(KV)
        Window.clearcolor = C["bg"]
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self._on_key)

        self.data = storage.StatsData()
        self.path = None

        self.sm = ScreenManager(transition=SlideTransition(duration=0.22))
        self.sm.add_widget(Screen(name="blank"))
        self.sm.add_widget(StartScreen(name="start"))
        self.sm.add_widget(MainScreen(name="main"))
        self.sm.add_widget(GameScreen(name="game"))
        self.sm.add_widget(RoundScreen(name="round"))
        return self.sm

    def on_start(self):
        if platform == "android":
            try:
                from android.permissions import Permission, request_permissions
                request_permissions(
                    [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE],
                    lambda perms, grants: Clock.schedule_once(lambda dt: self.startup(), 0))
                return
            except Exception:
                pass
        Clock.schedule_once(lambda dt: self.startup(), 0)

    # ---- konfiguracja: ostatni plik ----
    def config_path(self):
        return os.path.join(self.user_data_dir, "spis_gier_config.json")

    def read_cfg(self):
        try:
            with open(self.config_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def write_cfg(self, **kw):
        cfg = self.read_cfg()
        cfg.update(kw)
        try:
            with open(self.config_path(), "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False)
        except Exception:
            pass

    def last_dir(self):
        p = self.read_cfg().get("last_file")
        if p and os.path.isdir(os.path.dirname(p)):
            return os.path.dirname(p)
        return None

    # ---- foldery ----
    def default_dir(self):
        candidates = []
        if platform == "android":
            try:
                from android.storage import primary_external_storage_path
                candidates.append(os.path.join(primary_external_storage_path(),
                                               "Documents", "SpisGier"))
            except Exception:
                pass
        else:
            candidates.append(os.path.join(os.path.expanduser("~"), "SpisGier"))
        candidates.append(os.path.join(self.user_data_dir, "statystyki"))
        for d in candidates:
            try:
                if not os.path.isdir(d):
                    os.makedirs(d)
                test = os.path.join(d, ".test_zapisu")
                with open(test, "w") as f:
                    f.write("ok")
                os.remove(test)
                return d
            except Exception:
                continue
        return self.user_data_dir

    def quick_dirs(self):
        dirs = [("Spis gier", self.default_dir())]
        if platform == "android":
            try:
                from android.storage import primary_external_storage_path
                base = primary_external_storage_path()
                dirs.append(("Pobrane", os.path.join(base, "Download")))
                dirs.append(("Pamięć", base))
            except Exception:
                pass
        else:
            dirs.append(("Katalog domowy", os.path.expanduser("~")))
        return dirs

    # ---- start ----
    def startup(self):
        last = self.read_cfg().get("last_file")
        if last and os.path.isfile(last):
            if self.open_path(last, quiet=True):
                return
            msg = "Nie udało się odczytać ostatniego pliku:\n%s" % last
        elif last:
            msg = "Nie znaleziono ostatnio używanego pliku:\n%s\n\nWskaż plik albo utwórz nowy." % last
        else:
            msg = "Witaj! Wskaż plik ze statystykami albo utwórz nowy."
        self.sm.get_screen("start").set_message(msg)
        self.go("start", "left")

    def open_file_dialog(self):
        FileDialog("open", lambda path, **kw: self.open_path(path))

    def new_file_dialog(self):
        FileDialog("new", lambda path, **kw: self.create_path(path))

    def open_path(self, path, quiet=False):
        try:
            data = storage.load(path)
        except Exception as e:
            if not quiet:
                message("Błąd odczytu", "Nie można otworzyć pliku:\n%s\n\n%s" % (path, e))
            return False
        if self.path and self.data is not None:
            self.save()
        self.data = data
        self.path = path
        self.write_cfg(last_file=path)
        self.go("main", "left")
        self.sm.get_screen("main").refresh()
        return True

    def create_path(self, path):
        data = storage.StatsData()
        try:
            storage.save(data, path)
        except Exception as e:
            message("Błąd zapisu", "Nie można utworzyć pliku:\n%s\n\n%s" % (path, e))
            return False
        if self.path:
            self.save()
        self.data = data
        self.path = path
        self.write_cfg(last_file=path)
        self.go("main", "left")
        self.sm.get_screen("main").refresh()
        return True

    # ---- dane ----
    def save(self):
        if not self.path:
            return False
        try:
            storage.save(self.data, self.path)
            return True
        except Exception as e:
            message("Błąd zapisu", "Nie udało się zapisać pliku:\n%s\n\n%s" % (self.path, e))
            return False

    def add_game(self, name, players, mode):
        g = storage.Game(name=name, players=players, win_mode=mode)
        self.data.games.append(g)
        self.save()
        self.open_game(g)

    # ---- nawigacja ----
    def go(self, name, direction="left"):
        self.sm.transition.direction = direction
        self.sm.current = name

    def open_game(self, game):
        self.sm.get_screen("game").set_game(game)
        if self.sm.current == "game":
            self.sm.get_screen("game").refresh()
        self.go("game", "left")

    def open_round(self, game, rnd):
        self.sm.get_screen("round").load(game, rnd)
        self.go("round", "left")

    def quit(self):
        self.save()
        self.stop()

    def _on_key(self, window, key, *args):
        if key != 27:  # 27 = Esc / przycisk "wstecz" w Androidzie
            return False
        if any(isinstance(w, ModalView) for w in Window.children):
            return True
        scr = self.sm.current_screen
        if hasattr(scr, "on_back"):
            scr.on_back()
        return True

    def on_pause(self):
        self.save()
        return True

    def on_stop(self):
        if self.path:
            try:
                storage.save(self.data, self.path)
            except Exception:
                pass


if __name__ == "__main__":
    SpisGierApp().run()
