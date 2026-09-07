__version__ = "1.1.0"

from itertools import combinations
from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Line, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


# ---------------------------------------------------------------------------
# COLOR THEME (explicit everywhere so nothing depends on OS/platform defaults)
# ---------------------------------------------------------------------------
BG = (0.97, 0.97, 0.98, 1)             # app background (light, not black)
PANEL_BG = (1, 1, 1, 1)                # card/panel background
TEXT_DARK = (0.10, 0.10, 0.12, 1)      # main text
TEXT_MUTED = (0.40, 0.40, 0.45, 1)     # secondary/small text
HEADER_BG = (0.20, 0.30, 0.55, 1)      # title bar / header background
HEADER_TEXT = (1, 1, 1, 1)
ACCENT = (0.16, 0.45, 0.85, 1)         # primary buttons
ACCENT_TEXT = (1, 1, 1, 1)
DANGER = (0.75, 0.20, 0.20, 1)         # clear button
TABLE_HEADER_BG = (0.85, 0.89, 0.98, 1)
TABLE_ROW_ALT = (0.94, 0.95, 0.98, 1)
BORDER = (0.65, 0.65, 0.70, 1)
RESULT_BG = (0.87, 0.96, 0.86, 1)      # highlighted boolean-expression box
RESULT_BORDER = (0.20, 0.55, 0.25, 1)
ERROR_BG = (1.0, 0.90, 0.90, 1)
ERROR_TEXT = (0.6, 0.05, 0.05, 1)

Window.clearcolor = BG


def combine_terms(a, b):
    diff = 0
    out = []
    for x, y in zip(a, b):
        if x != y:
            diff += 1
            out.append("-")
        else:
            out.append(x)
    return "".join(out) if diff == 1 else None


def covers(term, m, n):
    bits = format(m, f"0{n}b")
    return all(a == "-" or a == b for a, b in zip(term, bits))


def term_expr(term, n):
    out = []
    for i, bit in enumerate(term):
        v = chr(ord("A") + i)
        if bit == "1":
            out.append(v)
        elif bit == "0":
            out.append(v + "'")
    return "".join(out) if out else "1"


def primes_for(ones, dc, n):
    current = {format(m, f"0{n}b") for m in ones + dc}
    primes = set()
    while current:
        nxt = set()
        used = set()
        items = list(current)
        for a in items:
            for b in items:
                c = combine_terms(a, b)
                if c is not None:
                    used.add(a)
                    used.add(b)
                    nxt.add(c)
        for x in current:
            if x not in used:
                primes.add(x)
        current = nxt
    return sorted(primes)


def minimum_cover(ones, primes, n):
    selected = []
    covered = set()

    changed = True
    while changed:
        changed = False
        for m in ones:
            possible = [p for p in primes if p not in selected and covers(p, m, n)]
            if len(possible) == 1:
                selected.append(possible[0])
                changed = True

    for p in selected:
        for m in ones:
            if covers(p, m, n):
                covered.add(m)

    remaining = [m for m in ones if m not in covered]
    if not remaining:
        return selected

    available = [p for p in primes if p not in selected]
    for r in range(1, len(available) + 1):
        for combo in combinations(available, r):
            if all(any(covers(p, m, n) for p in combo + tuple(selected)) for m in ones):
                selected.extend(combo)
                return selected
    return selected


def layout(n):
    if n == 2:
        return [0, 1], [0, 1]
    if n == 3:
        return [0, 1], [0, 1, 3, 2]
    return [0, 1, 3, 2], [0, 1, 3, 2]


def minterm_at(n, r, c):
    if n == 2:
        return r * 2 + c
    if n == 3:
        return r * 4 + c
    return r * 4 + c


class BgWidget(BoxLayout):
    """A BoxLayout with an explicit, resizable background color."""

    def __init__(self, bg_color=PANEL_BG, radius=0, **kwargs):
        super().__init__(**kwargs)
        self._bg_color = bg_color
        self._radius = radius
        with self.canvas.before:
            Color(*bg_color)
            if radius:
                self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
            else:
                self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


def make_label(text, color=TEXT_DARK, size=14, bold=False, halign="left", **kwargs):
    lab = Label(
        text=text,
        color=color,
        font_size=dp(size),
        bold=bold,
        halign=halign,
        valign="middle",
        **kwargs,
    )
    lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
    return lab


def make_button(text, bg=ACCENT, fg=ACCENT_TEXT, **kwargs):
    btn = Button(
        text=text,
        background_normal="",
        background_down="",
        background_color=bg,
        color=fg,
        bold=True,
        **kwargs,
    )
    return btn


class KMapWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.n = 4
        self.values = ["0"] * 16
        self.groups = []
        with self.canvas.before:
            Color(*PANEL_BG)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        self.bind(size=lambda *_: self.draw())

    def _sync_bg(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self.draw()

    def set_data(self, n, values, groups):
        self.n = n
        self.values = values
        self.groups = groups
        self.draw()

    def draw(self):
        self.canvas.after.clear()
        for child in list(self.children):
            if getattr(child, "_kmap_text", False):
                self.remove_widget(child)

        rows, cols = layout(self.n)
        left = dp(46)
        top = dp(26)
        cw = max(dp(65), (self.width - left - dp(8)) / len(cols))
        ch = max(dp(58), (self.height - top - dp(8)) / len(rows))

        with self.canvas.after:
            for i, rv in enumerate(rows):
                for j, cv in enumerate(cols):
                    x = left + j * cw
                    y = self.height - top - (i + 1) * ch
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(x, y), size=(cw, ch))
                    Color(*BORDER)
                    Line(rectangle=(x, y, cw, ch), width=1.2)

        self._draw_text_overlay(left, top, cw, ch, rows, cols)

        colors = [
            (0.85, 0.10, 0.10, 1),
            (0.08, 0.40, 0.85, 1),
            (0.10, 0.60, 0.20, 1),
            (0.90, 0.50, 0.02, 1),
            (0.55, 0.15, 0.75, 1),
            (0.02, 0.55, 0.55, 1),
        ]
        for gi, term in enumerate(self.groups):
            cells = []
            for i, rv in enumerate(rows):
                for j, cv in enumerate(cols):
                    m = minterm_at(self.n, rv, cv)
                    if covers(term, m, self.n):
                        cells.append((i, j))
            if not cells:
                continue
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            r0, r1 = min(rs), max(rs)
            c0, c1 = min(cs), max(cs)
            color = colors[gi % len(colors)]
            inset = dp(6) + dp(3) * (gi % 3)  # stagger overlapping loops apart
            with self.canvas.after:
                Color(*color)
                x = left + c0 * cw + inset
                y = self.height - top - (r1 + 1) * ch + inset
                w = (c1 - c0 + 1) * cw - inset * 2
                h = (r1 - r0 + 1) * ch - inset * 2
                Line(rounded_rectangle=(x, y, w, h, dp(10)), width=2.6)

    def _draw_text_overlay(self, left, top, cw, ch, rows, cols):
        col_labels = ["0", "1"] if self.n == 2 else ["00", "01", "11", "10"]
        row_labels = ["0", "1"] if self.n < 4 else ["00", "01", "11", "10"]

        for j, txt in enumerate(col_labels):
            lab = Label(text=txt, font_size=dp(12), bold=True, color=TEXT_DARK,
                        size_hint=(None, None), size=(cw, dp(22)),
                        pos=(left + j * cw, self.height - dp(22)))
            lab._kmap_text = True
            self.add_widget(lab)

        for i, txt in enumerate(row_labels):
            y = self.height - top - (i + 1) * ch
            lab = Label(text=txt, font_size=dp(12), bold=True, color=TEXT_DARK,
                        size_hint=(None, None), size=(left - dp(6), ch),
                        pos=(0, y))
            lab._kmap_text = True
            self.add_widget(lab)

        for i, rv in enumerate(rows):
            for j, cv in enumerate(cols):
                m = minterm_at(self.n, rv, cv)
                x = left + j * cw
                y = self.height - top - (i + 1) * ch
                val = self.values[m]
                val_color = (0.75, 0.10, 0.10, 1) if val == "1" else TEXT_MUTED
                lab = Label(text=f"m{m}\n[b]{val}[/b]", markup=True,
                            font_size=dp(13), color=TEXT_DARK,
                            halign="center", valign="middle",
                            size_hint=(None, None), size=(cw, ch),
                            pos=(x, y))
                lab._kmap_text = True
                lab.text_size = lab.size
                self.add_widget(lab)


class KMapApp(App):
    def build(self):
        self.title = "Visual K-Map Solver"
        self.n = 4
        self.inputs = []

        root = BgWidget(bg_color=BG, orientation="vertical", padding=dp(0), spacing=0)

        # ---------------- Header ----------------
        header = BgWidget(bg_color=HEADER_BG, orientation="vertical",
                           size_hint_y=None, height=dp(78), padding=(dp(12), dp(8)))
        header.add_widget(make_label("VISUAL K-MAP SOLVER", color=HEADER_TEXT,
                                      size=22, bold=True, halign="center",
                                      size_hint_y=None, height=dp(34)))
        header.add_widget(make_label("Truth Table -> K-Map -> Group Loops -> Boolean Expression",
                                      color=(0.9, 0.92, 1, 1), size=11, halign="center",
                                      size_hint_y=None, height=dp(26)))
        root.add_widget(header)

        # ---------------- Controls (two full-width rows so nothing clips) ----------------
        controls = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(96),
                              padding=(dp(10), dp(8)), spacing=dp(6))

        row1 = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        row1.add_widget(make_label("Variables:", color=TEXT_DARK, size=14,
                                    bold=True, size_hint_x=0.35))
        self.spinner = Spinner(text="4", values=("2", "3", "4"),
                                size_hint_x=0.65,
                                background_normal="", background_color=(0.85, 0.87, 0.92, 1),
                                color=TEXT_DARK)
        self.spinner.bind(text=self.change_vars)
        row1.add_widget(self.spinner)
        controls.add_widget(row1)

        row2 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        solve = make_button("SOLVE K-MAP", bg=ACCENT, size_hint_x=0.65)
        solve.bind(on_release=lambda *_: self.solve())
        row2.add_widget(solve)
        clear = make_button("CLEAR", bg=DANGER, size_hint_x=0.35)
        clear.bind(on_release=lambda *_: self.create_table())
        row2.add_widget(clear)
        controls.add_widget(row2)

        root.add_widget(controls)

        # ---------------- Scrollable body ----------------
        body = ScrollView(do_scroll_x=False, bar_width=dp(6))
        inside = BoxLayout(orientation="vertical", spacing=dp(10),
                            padding=(dp(10), dp(6)), size_hint_y=None)
        inside.bind(minimum_height=inside.setter("height"))
        body.add_widget(inside)

        # --- Boolean expression result box (placed right under controls so it is
        #     always immediately visible, before any scrolling is needed) ---
        self.result_box = BgWidget(bg_color=RESULT_BG, orientation="vertical",
                                    size_hint_y=None, radius=dp(10),
                                    padding=(dp(10), dp(8)), spacing=dp(4))
        self.result_box.bind(minimum_height=self.result_box.setter("height"))
        inside.add_widget(self.result_box)

        # --- Truth table ---
        inside.add_widget(make_label("TRUTH TABLE", color=TEXT_DARK, size=15, bold=True,
                                      size_hint_y=None, height=dp(26)))
        self.table_card = BgWidget(bg_color=PANEL_BG, orientation="vertical",
                                    size_hint_y=None, radius=dp(8), padding=dp(6))
        self.table_card.bind(minimum_height=self.table_card.setter("height"))
        self.table = GridLayout(cols=5, spacing=dp(2), size_hint_y=None)
        self.table.bind(minimum_height=self.table.setter("height"))
        self.table_card.add_widget(self.table)
        inside.add_widget(self.table_card)

        # --- K-Map ---
        inside.add_widget(make_label("K-MAP", color=TEXT_DARK, size=15, bold=True,
                                      size_hint_y=None, height=dp(26)))
        self.kmap = KMapWidget(size_hint_y=None, height=dp(320))
        inside.add_widget(self.kmap)

        # --- Groups detail list ---
        inside.add_widget(make_label("GROUPS / SIMPLIFICATION STEPS", color=TEXT_DARK,
                                      size=15, bold=True, size_hint_y=None, height=dp(26)))
        self.groups_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.groups_box.bind(minimum_height=self.groups_box.setter("height"))
        inside.add_widget(self.groups_box)

        root.add_widget(body)

        # ---------------- Footer credit ----------------
        credit = make_label("Developed by Salman  \u2022  md.salmanfarsi.eee@gmail.com",
                             color=TEXT_MUTED, size=10, halign="right",
                             size_hint_y=None, height=dp(24))
        root.add_widget(credit)

        self.create_table()
        return root

    def change_vars(self, spinner, value):
        self.n = int(value)
        self.create_table()

    def create_table(self):
        self.table.clear_widgets()
        self.inputs = []
        headers = [chr(ord("A") + i) for i in range(self.n)] + ["F"]
        self.table.cols = self.n + 1
        for h in headers:
            cell = BgWidget(bg_color=TABLE_HEADER_BG, size_hint_y=None, height=dp(32))
            cell.add_widget(make_label(h, color=TEXT_DARK, size=14, bold=True, halign="center"))
            self.table.add_widget(cell)
        for m in range(1 << self.n):
            bits = format(m, f"0{self.n}b")
            row_bg = PANEL_BG if m % 2 == 0 else TABLE_ROW_ALT
            for b in bits:
                cell = BgWidget(bg_color=row_bg, size_hint_y=None, height=dp(34))
                cell.add_widget(make_label(b, color=TEXT_DARK, size=13, halign="center"))
                self.table.add_widget(cell)
            e = TextInput(text="0", multiline=False, halign="center",
                          size_hint_y=None, height=dp(34),
                          background_color=(1, 1, 1, 1), foreground_color=TEXT_DARK,
                          cursor_color=ACCENT)
            self.inputs.append(e)
            self.table.add_widget(e)

        self.result_box.clear_widgets()
        self.result_box.add_widget(make_label(
            "Enter 0, 1, or X for each row, then press SOLVE K-MAP.",
            color=TEXT_DARK, size=13, size_hint_y=None, height=dp(30)))
        self.groups_box.clear_widgets()
        self.kmap.set_data(self.n, ["0"] * (1 << self.n), [])

    def solve(self):
        vals = []
        for e in self.inputs:
            s = e.text.strip().upper()
            if s not in ("0", "1", "X"):
                self.result_box.clear_widgets()
                self.result_box.add_widget(make_label(
                    "Invalid input: use only 0, 1, or X.",
                    color=ERROR_TEXT, size=14, bold=True,
                    size_hint_y=None, height=dp(36)))
                return
            vals.append(s)

        ones = [i for i, v in enumerate(vals) if v == "1"]
        dc = [i for i, v in enumerate(vals) if v == "X"]
        primes = primes_for(ones, dc, self.n)
        groups = minimum_cover(ones, primes, self.n)
        self.kmap.set_data(self.n, vals, groups)

        if not ones:
            expr = "0"
        elif len(ones) == (1 << self.n):
            expr = "1"
        else:
            expr = " + ".join(term_expr(g, self.n) for g in groups)

        self.result_box.clear_widgets()
        self.result_box.add_widget(make_label(
            f"F = {expr}", color=(0.05, 0.35, 0.10, 1), size=20, bold=True,
            size_hint_y=None, height=dp(40)))
        if dc:
            self.result_box.add_widget(make_label(
                "Don't-care minterms: " + ", ".join(map(str, dc)),
                color=TEXT_DARK, size=12, size_hint_y=None, height=dp(26)))

        self.groups_box.clear_widgets()
        for i, g in enumerate(groups, 1):
            ms = [m for m in range(1 << self.n) if covers(g, m, self.n)]
            self.groups_box.add_widget(make_label(
                f"Group {i}: {len(ms)} cell(s)   m({', '.join(map(str, ms))})   -> {term_expr(g, self.n)}",
                color=TEXT_DARK, size=13, size_hint_y=None, height=dp(30)))


if __name__ == "__main__":
    KMapApp().run()
