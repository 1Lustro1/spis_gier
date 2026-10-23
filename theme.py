# -*- coding: utf-8 -*-
"""Motyw "Zielone sukno": ciemna zieleń stołu do gry, złote akcenty,
kremowy tekst i osobny kolor dla każdego uczestnika."""
from kivy.utils import get_color_from_hex as hx

C = {
    "bg": hx("#0E2620"),
    "surface": hx("#163A2F"),
    "surface2": hx("#1F4A3D"),
    "field": hx("#0B1F1A"),
    "line": hx("#2D5E4F"),
    "gold": hx("#E3B341"),
    "gold_dark": hx("#B88A22"),
    "text": hx("#F4ECD8"),
    "muted": hx("#9FB5A8"),
    "dark": hx("#0E2620"),
    "red": hx("#C8553D"),
    "red_dark": hx("#9E3F2B"),
    "invalid": hx("#6B2A22"),
    "transparent": (0, 0, 0, 0),
}

PLAYER_COLORS = [
    hx("#E07A5F"),  # koral
    hx("#5DB7C9"),  # turkus
    hx("#F2CC8F"),  # piasek
    hx("#A99AF5"),  # lawenda
    hx("#81C29A"),  # szałwia
    hx("#E86FA5"),  # róż
    hx("#F4A259"),  # pomarańcz
    hx("#8FD0F0"),  # błękit
]


def player_color(i, alpha=1.0):
    c = PLAYER_COLORS[i % len(PLAYER_COLORS)]
    return (c[0], c[1], c[2], alpha)


def darker(color, k=0.75):
    return (color[0] * k, color[1] * k, color[2] * k, color[3] if len(color) > 3 else 1)
