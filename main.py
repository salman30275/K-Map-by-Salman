__version__ = "5.0.0"

from itertools import combinations
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout

# ---------------- Boolean logic ----------------

def combine(a, b):
    diff = 0
    out = []
    for x, y in zip(a, b):
        if x != y:
            diff += 1
            out.append("-")
        else:
            out.append(x)
    return "".join(out) if diff == 1 else None

def covers(term, number, n):
    bits = format(number, f"0{n}b")
    return all(a == "-" or a == b for a, b in zip(term, bits))

def term_to_expr(term):
    names = "ABCD"
    out = ""
    for i, bit in enumerate(term):
        if bit == "1":
            out += names[i]
        elif bit == "0":
            out += names[i] + "'"
    return out or "1"

def prime_implicants(ones, dcs, n):
    current = {format(m, f"0{n}b") for m in ones + dcs}
    result = set()
    while current:
        items = sorted(current)
        nxt = set()
        used = set()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                c = combine(items[i], items[j])
                if c:
                    nxt.add(c)
                    used.add(items[i])
                    used.add(items[j])
        result.update(x for x in current if x not in used)
        current = nxt
    return sorted(result)

def find_groups(ones, dcs, n):
    if not ones or len(ones) == (1 << n):
        return []

    primes = prime_implicants(ones, dcs, n)
    chosen = []
    covered = set()

    # Essential prime implicants first.
    for m in ones:
        hits = [p for p in primes if covers(p, m, n)]
        if len(hits) == 1 and hits[0] not in chosen:
            chosen.append(hits[0])

    for p in chosen:
        covered.update(m for m in ones if covers(p, m, n))

    remaining = [m for m in ones if m not in covered]
    available = [p for p in primes if p not in chosen]

    # Prefer fewer, larger groups.
    for r in range(1, len(available) + 1):
        answer = None
        for combo in combinations(available, r):
            trial = chosen + list(combo)
            if all(any(covers(p, m, n) for p in trial) for m in ones):
                answer = list(combo)
                break
        if answer is not None:
            chosen.extend(answer)
            break

    return chosen

# ---------------- Warm, human-designed palette ----------------

BG = (0.955, 0.945, 0.925, 1)
PAPER = (0.995, 0.985, 0.955, 1)
NAVY = (0.12, 0.16, 0.21, 1)
INK = (0.18, 0.18, 0.18, 1)
MUTED = (0.43, 0.44, 0.44, 1)
BLUE = (0.30, 0.46, 0.64, 1)
BLUE_PALE = (0.89, 0.93, 0.96, 1)
SAGE = (0.55, 0.68, 0.53, 1)
SAGE_PALE = (0.90, 0.94, 0.87, 1)
TERRACOTTA = (0.76, 0.34, 0.28, 1)
MUSTARD = (0.73, 0.56, 0.27, 1)
PLUM = (0.47, 0.34, 0.47, 1)
TEAL = (0.29, 0.52, 0.50, 1)
WHITE = (1, 1, 1, 1)

LOOP_COLORS = [TERRACOTTA, BLUE, SAGE, MUSTARD, PLUM, TEAL]

def bg(widget, color, radius=10):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                radius=[dp(radius)])
    def update(*_):
        rect.pos = widget.pos
        rect.size = widget.size
    widget.bind(pos=update, size=update)

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(8)
        bg(self, PAPER, 11)

class CellLabel(Label):
    def __init__(self, fill=PAPER, **kwargs):
        super().__init__(**kwargs)
        self.color = INK
        self.halign = "center"
        self.valign = "middle"
        with self.canvas.before:
            Color(*fill)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[dp(2)])
            Color(0.72, 0.70, 0.65, 1)
            self.border = Line(rounded_rectangle=(self.x, self.y,
                                                   self.width, self.height,
                                                   dp(2)), width=0.7)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width,
                                          self.height, dp(2))

# ---------------- Reliable phone K-map ----------------
# Uses real Kivy widgets instead of relying on a custom canvas layout.
# This prevents the blank K-map seen in the previous build.

class KMapView(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.n = 4
        self.values = ["0"] * 16
        self.groups = []
        self.bind(size=lambda *_: self.rebuild())

    def set_data(self, n, values, groups):
        self.n = n
        self.values = list(values)
        self.groups = list(groups)
        self.rebuild()

    def map_data(self):
        if self.n == 2:
            return ["0", "1"], ["0", "1"], [[0, 1], [2, 3]]
        if self.n == 3:
            return ["0", "1"], ["00", "01", "11", "10"], [
                [0, 1, 3, 2],
                [4, 5, 7, 6],
            ]
        return ["00", "01", "11", "10"], ["00", "01", "11", "10"], [
            [0, 1, 3, 2],
            [4, 5, 7, 6],
            [12, 13, 15, 14],
            [8, 9, 11, 10],
        ]

    def rebuild(self):
        self.clear_widgets()
        rows_lbl, cols_lbl, cells = self.map_data()
        rows = len(cells)
        cols = len(cells[0])

        # Geometry always fits inside the phone width.
        left = dp(31)
        right = dp(3)
        top = dp(27)
        bottom = dp(4)
        cell_w = max(dp(45), (self.width - left - right) / cols)
        cell_h = min(dp(45), max(dp(35), (self.height - top - bottom) / rows))
        map_w = cell_w * cols
        map_h = cell_h * rows
        x0 = left
        y0 = bottom + max(0, (self.height - top - bottom - map_h) / 2)

        # Column labels.
        for c, text in enumerate(cols_lbl):
            lab = Label(text=text, color=NAVY, bold=True, font_size=dp(9),
                        size_hint=(None, None), size=(cell_w, dp(18)),
                        pos=(x0 + c * cell_w, y0 + map_h + dp(2)))
            self.add_widget(lab)

        # Row labels and cells.
        for r in range(rows):
            y = y0 + (rows - 1 - r) * cell_h
            row_lab = Label(text=rows_lbl[r], color=NAVY, bold=True,
                            font_size=dp(9), size_hint=(None, None),
                            size=(left - dp(3), cell_h), pos=(0, y))
            self.add_widget(row_lab)

            for c in range(cols):
                x = x0 + c * cell_w
                m = cells[r][c]
                v = self.values[m] if m < len(self.values) else "0"
                fill = SAGE_PALE if v == "1" else (
                    (0.98, 0.94, 0.78, 1) if v == "X" else PAPER
                )
                cell = CellLabel(
                    fill=fill,
                    text=f"m{m}\n{v}",
                    bold=(v == "1"),
                    font_size=dp(10),
                    size_hint=(None, None),
                    size=(cell_w, cell_h),
                    pos=(x, y),
                )
                self.add_widget(cell)

        if self.n == 4:
            self.add_widget(Label(text="CD", color=BLUE, bold=True,
                                  font_size=dp(9), size_hint=(None, None),
                                  size=(dp(25), dp(18)),
                                  pos=(x0, y0 + map_h + dp(20))))
            self.add_widget(Label(text="AB", color=BLUE, bold=True,
                                  font_size=dp(9), size_hint=(None, None),
                                  size=(dp(27), dp(18)),
                                  pos=(0, y0 + map_h / 2 - dp(9))))
        elif self.n == 3:
            self.add_widget(Label(text="BC", color=BLUE, bold=True,
                                  font_size=dp(9), size_hint=(None, None),
                                  size=(dp(25), dp(18)),
                                  pos=(x0, y0 + map_h + dp(20))))

        # Exact group outlines. Each exposed edge is drawn separately,
        # so wrap-around groups do not create giant rectangles over 0-cells.
        overlay = Widget(size_hint=(1, 1), pos=(0, 0))
        with overlay.canvas:
            pass
        self.add_widget(overlay)

        for gi, term in enumerate(self.groups):
            selected = set()
            for r in range(rows):
                for c in range(cols):
                    m = cells[r][c]
                    if covers(term, m, self.n):
                        selected.add((r, c))
            if not selected:
                continue

            col = LOOP_COLORS[gi % len(LOOP_COLORS)]

            # Draw exposed edges only.
            with overlay.canvas:
                Color(*col)
                for r, c in selected:
                    x = x0 + c * cell_w
                    y = y0 + (rows - 1 - r) * cell_h
                    if (r, (c - 1) % cols) not in selected:
                        Line(points=[x+dp(2), y+dp(3),
                                     x+dp(2), y+cell_h-dp(3)], width=2.0)
                    if (r, (c + 1) % cols) not in selected:
                        Line(points=[x+cell_w-dp(2), y+dp(3),
                                     x+cell_w-dp(2), y+cell_h-dp(3)], width=2.0)
                    if ((r - 1) % rows, c) not in selected:
                        Line(points=[x+dp(3), y+dp(2),
                                     x+cell_w-dp(3), y+dp(2)], width=2.0)
                    if ((r + 1) % rows, c) not in selected:
                        Line(points=[x+dp(3), y+cell_h-dp(2),
                                     x+cell_w-dp(3), y+cell_h-dp(2)], width=2.0)

            # Small group tag.
            rr, cc = min(selected)
            tx = x0 + cc * cell_w + dp(3)
            ty = y0 + (rows - 1 - rr) * cell_h + cell_h - dp(18)
            tag = Label(text=f"G{gi+1}", color=WHITE, bold=True,
                        font_size=dp(7), size_hint=(None, None),
                        size=(dp(22), dp(15)), pos=(tx, ty))
            with tag.canvas.before:
                Color(*col)
                tag.bg = RoundedRectangle(pos=tag.pos, size=tag.size,
                                          radius=[dp(4)])
            tag.bind(pos=lambda w, *_: setattr(w.bg, "pos", w.pos),
                     size=lambda w, *_: setattr(w.bg, "size", w.size))
            self.add_widget(tag)

# ---------------- Main app ----------------

class KMapSolver(App):
    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = "below_target"
        self.n = 4
        self.inputs = []

        root = BoxLayout(
            orientation="vertical",
            padding=(dp(7), dp(5), dp(7), dp(3)),
            spacing=dp(5),
        )

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(64),
            padding=(dp(6), dp(3)),
        )
        bg(header, NAVY, 13)
        header.add_widget(Label(
            text="K-MAP SOLVER",
            color=WHITE, bold=True, font_size=dp(20),
            size_hint_y=None, height=dp(35),
        ))
        header.add_widget(Label(
            text="Truth Table  |  K-Map  |  Group Loops  |  SOP",
            color=(0.78, 0.81, 0.82, 1), font_size=dp(8.5),
            size_hint_y=None, height=dp(17),
        ))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True,
                            bar_width=dp(3))
        content = BoxLayout(
            orientation="vertical", spacing=dp(7),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        # Controls
        controls = Card(
            orientation="horizontal", size_hint_y=None,
            height=dp(58), spacing=dp(6),
        )
        controls.add_widget(Label(
            text="Variables", color=INK, bold=True, font_size=dp(11),
            size_hint_x=0.27,
        ))
        self.spinner = Spinner(
            text="4", values=("2", "3", "4"),
            font_size=dp(12), background_normal="",
            background_color=BLUE_PALE, color=NAVY,
            size_hint_x=0.20,
        )
        self.spinner.bind(text=self.change_vars)
        controls.add_widget(self.spinner)

        solve = Button(
            text="SOLVE", bold=True, font_size=dp(11),
            background_normal="", background_color=BLUE, color=WHITE,
            size_hint_x=0.265,
        )
        solve.bind(on_release=lambda *_: self.solve())
        controls.add_widget(solve)

        clear = Button(
            text="CLEAR", bold=True, font_size=dp(11),
            background_normal="", background_color=(0.47, 0.47, 0.45, 1),
            color=WHITE, size_hint_x=0.265,
        )
        clear.bind(on_release=lambda *_: self.create_table())
        controls.add_widget(clear)
        content.add_widget(controls)

        # Truth table card
        truth = Card(
            orientation="vertical", size_hint_y=None,
            height=dp(285), spacing=dp(3),
        )
        truth.add_widget(Label(
            text="TRUTH TABLE", color=NAVY, bold=True, font_size=dp(14),
            size_hint_y=None, height=dp(25),
        ))
        truth.add_widget(Label(
            text="Enter 0, 1 or X in F",
            color=MUTED, font_size=dp(8.5),
            size_hint_y=None, height=dp(17),
        ))

        ts = ScrollView(
            do_scroll_x=False, do_scroll_y=True,
            bar_width=dp(3), size_hint_y=None, height=dp(225),
        )
        self.table = GridLayout(
            cols=5, spacing=dp(1),
            size_hint_y=None, size_hint_x=1,
            row_default_height=dp(29),
            row_force_default=True,
        )
        self.table.bind(minimum_height=self.table.setter("height"))
        ts.add_widget(self.table)
        truth.add_widget(ts)
        content.add_widget(truth)

        # K-map card -- deliberately large enough for the whole map.
        kcard = Card(
            orientation="vertical", size_hint_y=None,
            height=dp(270), spacing=dp(2),
        )
        kcard.add_widget(Label(
            text="K-MAP & GROUP LOOPS", color=NAVY, bold=True,
            font_size=dp(14), size_hint_y=None, height=dp(27),
        ))
        self.kmap = KMapView(size_hint_y=None, height=dp(230))
        kcard.add_widget(self.kmap)
        content.add_widget(kcard)

        # Simplification
        self.steps_card = Card(
            orientation="vertical", size_hint_y=None, spacing=dp(5),
        )
        self.steps_card.add_widget(Label(
            text="GROUP SIMPLIFICATION", color=NAVY, bold=True,
            font_size=dp(14), size_hint_y=None, height=dp(27),
        ))
        self.steps = BoxLayout(
            orientation="vertical", spacing=dp(5), size_hint_y=None,
        )
        self.steps.bind(minimum_height=self.steps.setter("height"))
        self.steps_card.add_widget(self.steps)
        content.add_widget(self.steps_card)

        scroll.add_widget(content)
        root.add_widget(scroll)

        footer = Label(
            text="Developed by Salman  •  md.salmanfarsi.eee@gmail.com",
            color=MUTED, font_size=dp(7.2),
            halign="right", valign="middle",
            size_hint_y=None, height=dp(18),
        )
        footer.bind(size=lambda w, s: setattr(w, "text_size", s))
        root.add_widget(footer)

        self.create_table()
        return root

    def change_vars(self, _, value):
        self.n = int(value)
        self.create_table()

    def create_table(self):
        self.table.clear_widgets()
        self.inputs = []
        self.table.cols = self.n + 1

        heads = [chr(ord("A") + i) for i in range(self.n)] + ["F"]

        for h in heads:
            lab = Label(
                text=h, color=WHITE, bold=True, font_size=dp(10),
                size_hint_x=1, size_hint_y=None, height=dp(29),
            )
            with lab.canvas.before:
                Color(*BLUE)
                lab.bg = RoundedRectangle(pos=lab.pos, size=lab.size,
                                          radius=[dp(2)])
            lab.bind(pos=lambda w, *_: setattr(w.bg, "pos", w.pos),
                     size=lambda w, *_: setattr(w.bg, "size", w.size))
            self.table.add_widget(lab)

        for m in range(1 << self.n):
            bits = format(m, f"0{self.n}b")
            for b in bits:
                self.table.add_widget(Label(
                    text=b, color=INK, font_size=dp(10),
                    size_hint_x=1, size_hint_y=None, height=dp(29),
                ))

            e = TextInput(
                text="0", multiline=False, halign="center",
                font_size=dp(10), size_hint_x=1, size_hint_y=None,
                height=dp(29),
                background_normal="", background_active="",
                background_color=BLUE_PALE,
                foreground_color=INK,
                selection_color=(0, 0, 0, 0),
                cursor_color=BLUE,
                padding=[0, 0],
            )
            self.inputs.append(e)
            self.table.add_widget(e)

        self.kmap.set_data(self.n, ["0"] * (1 << self.n), [])
        self.show_message("Fill the F column and press SOLVE.")

    def show_message(self, message):
        self.steps.clear_widgets()
        self.steps.add_widget(Label(
            text=message, color=MUTED, font_size=dp(10.5),
            size_hint_y=None, height=dp(34),
        ))
        self.steps_card.height = dp(73)

    def add_group_row(self, number, mins, expression, color):
        row = BoxLayout(
            orientation="horizontal", size_hint_y=None,
            height=dp(48), spacing=dp(7),
            padding=(dp(3), dp(2)),
        )
        bg(row, (0.985, 0.975, 0.945, 1), 8)

        badge = Label(
            text=f"G{number}", color=WHITE, bold=True, font_size=dp(10),
            size_hint_x=None, width=dp(38),
        )
        with badge.canvas.before:
            Color(*color)
            badge.bg = RoundedRectangle(pos=badge.pos, size=badge.size,
                                        radius=[dp(6)])
        badge.bind(pos=lambda w, *_: setattr(w.bg, "pos", w.pos),
                   size=lambda w, *_: setattr(w.bg, "size", w.size))

        info = Label(
            text=f"m({', '.join(map(str, mins))})    →    {expression}",
            color=INK, bold=True, font_size=dp(9.5),
            halign="left", valign="middle",
        )
        info.bind(size=lambda w, s: setattr(w, "text_size", s))
        row.add_widget(badge)
        row.add_widget(info)
        self.steps.add_widget(row)

    def solve(self):
        vals = []
        for e in self.inputs:
            v = e.text.strip().upper()
            if v not in ("0", "1", "X"):
                self.show_message("Only 0, 1 or X are allowed in F.")
                return
            vals.append(v)

        ones = [i for i, v in enumerate(vals) if v == "1"]
        dcs = [i for i, v in enumerate(vals) if v == "X"]

        if not ones:
            groups = []
            final = "0"
        elif len(ones) == (1 << self.n):
            groups = []
            final = "1"
        else:
            groups = find_groups(ones, dcs, self.n)
            final = " + ".join(term_to_expr(g) for g in groups)

        self.kmap.set_data(self.n, vals, groups)
        self.steps.clear_widgets()

        banner = BoxLayout(
            orientation="vertical", size_hint_y=None,
            height=dp(60), padding=(dp(6), dp(2)),
        )
        bg(banner, BLUE_PALE, 9)
        banner.add_widget(Label(
            text="FINAL BOOLEAN EXPRESSION", color=BLUE, bold=True,
            font_size=dp(9), size_hint_y=None, height=dp(18),
        ))
        banner.add_widget(Label(
            text=f"F = {final}", color=NAVY, bold=True,
            font_size=dp(15), size_hint_y=None, height=dp(30),
        ))
        self.steps.add_widget(banner)

        if groups:
            self.steps.add_widget(Label(
                text="Individual groups",
                color=NAVY, bold=True, font_size=dp(11),
                size_hint_y=None, height=dp(24),
            ))
            for i, g in enumerate(groups):
                mins = [m for m in ones if covers(g, m, self.n)]
                self.add_group_row(
                    i + 1, mins, term_to_expr(g),
                    LOOP_COLORS[i % len(LOOP_COLORS)],
                )
        else:
            self.steps.add_widget(Label(
                text="No grouping is required.",
                color=MUTED, font_size=dp(10.5),
                size_hint_y=None, height=dp(28),
            ))

        if dcs:
            self.steps.add_widget(Label(
                text="Don't-care cells: " + ", ".join(map(str, dcs)),
                color=MUSTARD, font_size=dp(9.5),
                size_hint_y=None, height=dp(23),
            ))

        total = dp(36)
        for child in self.steps.children:
            total += child.height + dp(5)
        self.steps_card.height = max(dp(80), total)

if __name__ == "__main__":
    KMapSolver().run()
