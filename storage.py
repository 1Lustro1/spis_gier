# -*- coding: utf-8 -*-
"""
Warstwa danych aplikacji "Spis gier".

Wszystkie statystyki przechowywane są w jednym pliku CSV (separator ';',
kodowanie UTF-8 z BOM - plik otwiera się poprawnie w Excelu).

Format pliku (każdy wiersz zaczyna się od typu rekordu):

    SPIS_GIER;1                                   - nagłówek i wersja formatu
    GAME;<id_gry>;<nazwa>;<max|min>;<uczestnik 1>;<uczestnik 2>;...
    ROUND;<id_gry>;<id_rozgrywki>;<nazwa>;<data utworzenia>
    SCORE;<id_gry>;<id_rozgrywki>;<wiersz>;<kolumna>;<wartość>

Wartości liczbowe zapisywane są z kropką dziesiętną.
Zapisywane są tylko wypełnione komórki tabeli wyników.
"""
import csv
import datetime
import os
import uuid

FORMAT_TAG = "SPIS_GIER"
FORMAT_VERSION = "1"
EPS = 1e-9


class FileFormatError(Exception):
    pass


# --------------------------------------------------------------------------
# Liczby
# --------------------------------------------------------------------------
def parse_number(text):
    """Zamienia tekst na liczbę. Pusty tekst -> None. Błędny -> ValueError.
    Akceptuje przecinek i kropkę jako separator dziesiętny."""
    t = (text or "").strip().replace(" ", "").replace(",", ".")
    if t == "":
        return None
    if t in ("-", "+", ".", "-.", "+."):
        raise ValueError(text)
    return float(t)


def fmt_number(value):
    """Ładny zapis liczby po polsku: 12, -3,5, 0,25."""
    if value is None:
        return ""
    if abs(value - round(value)) < EPS:
        s = str(int(round(value)))
    else:
        s = ("%.4f" % value).rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    return s.replace(".", ",")


def _num_to_csv(value):
    if abs(value - round(value)) < EPS:
        return str(int(round(value)))
    return repr(value)


def new_id():
    return uuid.uuid4().hex[:10]


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
class Round(object):
    def __init__(self, rid=None, name="", created=None, scores=None):
        self.id = rid or new_id()
        self.name = name
        self.created = created or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        # scores: {(wiersz, kolumna): float}
        self.scores = dict(scores or {})

    def row_count(self):
        if not self.scores:
            return 0
        return max(r for r, _ in self.scores) + 1

    def totals(self, n_players):
        t = [0.0] * n_players
        for (r, c), v in self.scores.items():
            if 0 <= c < n_players:
                t[c] += v
        return t

    def is_empty(self):
        return not self.scores


class Game(object):
    def __init__(self, gid=None, name="", players=None, win_mode="max", rounds=None):
        self.id = gid or new_id()
        self.name = name
        self.players = list(players or [])
        self.win_mode = win_mode if win_mode in ("max", "min") else "max"
        self.rounds = list(rounds or [])

    # --- wyniki ---
    def best_indices(self, values):
        """Indeksy uczestników z najlepszym wynikiem (remis -> kilka)."""
        if not values:
            return []
        best = max(values) if self.win_mode == "max" else min(values)
        return [i for i, v in enumerate(values) if abs(v - best) < EPS]

    def round_winners(self, rnd):
        if rnd.is_empty():
            return []
        return self.best_indices(rnd.totals(len(self.players)))

    def totals(self):
        t = [0.0] * len(self.players)
        for rnd in self.rounds:
            for i, v in enumerate(rnd.totals(len(self.players))):
                t[i] += v
        return t

    def wins(self):
        w = [0] * len(self.players)
        for rnd in self.rounds:
            for i in self.round_winners(rnd):
                w[i] += 1
        return w

    def leaders(self):
        """Lider całej gry - najlepsza suma punktów ze wszystkich rozgrywek."""
        if not any(not r.is_empty() for r in self.rounds):
            return []
        return self.best_indices(self.totals())

    def round_number(self, rnd):
        return self.rounds.index(rnd) + 1

    def default_round_name(self):
        return "Rozgrywka %d" % (len(self.rounds) + 1)


class StatsData(object):
    def __init__(self, games=None):
        self.games = list(games or [])

    def find_game(self, gid):
        for g in self.games:
            if g.id == gid:
                return g
        return None


# --------------------------------------------------------------------------
# Odczyt / zapis
# --------------------------------------------------------------------------
def load(path):
    data = StatsData()
    rounds_by_key = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = [r for r in reader if r and any(x.strip() for x in r)]

    if not rows:
        # pusty plik traktujemy jak nowy
        return data
    if rows[0][0].strip() != FORMAT_TAG:
        raise FileFormatError("To nie jest plik statystyk programu Spis gier.")

    for line_no, row in enumerate(rows[1:], start=2):
        kind = row[0].strip().upper()
        try:
            if kind == "GAME":
                g = Game(gid=row[1], name=row[2], win_mode=row[3],
                         players=[p for p in row[4:]])
                data.games.append(g)
            elif kind == "ROUND":
                g = data.find_game(row[1])
                if g is None:
                    continue
                rnd = Round(rid=row[2], name=row[3],
                            created=row[4] if len(row) > 4 else None)
                g.rounds.append(rnd)
                rounds_by_key[(g.id, rnd.id)] = rnd
            elif kind == "SCORE":
                rnd = rounds_by_key.get((row[1], row[2]))
                if rnd is None:
                    continue
                rnd.scores[(int(row[3]), int(row[4]))] = float(row[5])
        except (IndexError, ValueError):
            raise FileFormatError("Błąd w wierszu %d pliku." % line_no)
    return data


def save(data, path):
    """Zapis atomowy: najpierw plik tymczasowy, potem podmiana."""
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([FORMAT_TAG, FORMAT_VERSION])
        for g in data.games:
            w.writerow(["GAME", g.id, g.name, g.win_mode] + list(g.players))
        for g in data.games:
            for rnd in g.rounds:
                w.writerow(["ROUND", g.id, rnd.id, rnd.name, rnd.created])
                for (r, c) in sorted(rnd.scores):
                    w.writerow(["SCORE", g.id, rnd.id, r, c,
                                _num_to_csv(rnd.scores[(r, c)])])
    try:
        os.replace(tmp, path)
    except OSError:
        # niektóre systemy plików na Androidzie nie wspierają replace
        with open(tmp, "r", encoding="utf-8-sig", newline="") as src:
            content = src.read()
        with open(path, "w", encoding="utf-8-sig", newline="") as dst:
            dst.write(content)
        try:
            os.remove(tmp)
        except OSError:
            pass
