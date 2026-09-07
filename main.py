__version__ = "3.0.0"

from itertools import combinations
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget


# ============================================================
# BOOLEAN / QUINE-MCCLUSKEY
# ============================================================

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


def expression(term, n):
    names = "ABCD"
    parts = []
    for i, bit in enumerate(term):
        if bit == "1":
            parts.append(names[i])
        elif bit == "0":
            parts.append(names[i] + "'")
    return "".join(parts) or "1"


def prime_implicants(ones, dcs, n):
    current = {format(m, f"0{n}b") for m in ones + dcs}
    primes = set()

    while current:
        nxt = set()
        used = set()
        items = sorted(current)

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                c = combine(items[i], items[j])
                if c is not None:
                    used.add(items[i])
                    used.add(items[j])
                    nxt.add(c)

        primes.update(x for x in current if x not in used)
        current = nxt

    return sorted(primes)


def choose_groups(ones, dcs, n):
    if not ones:
        return []

    if len(ones) == (1 << n):
        return []

    primes = prime_implicants(ones, dcs, n)
    chosen = []
    covered = set()

    # Essential prime implicants
    for m in ones:
        hits = [p for p in primes if covers(p, m, n)]
        if len(hits) == 1 and hits[0] not in chosen:
            chosen.append(hits[0])

    for p in chosen:
        covered.update(m for m in ones if covers(p, m, n))

    remaining = [m for m in ones if m not in covered]
    available = [p for p in primes if p not in chosen]

    if remaining:
        # Find the smallest complete cover.
        found = None
        for r in range(1, len(available) + 1):
            for combo in combinations(available, r):
                test = chosen + list(combo)
                if all(any(covers(p, m, n) for p in test) for m in ones):
                    found = list(combo)
                    break
            if found is not None:
                break

        if found:
            chosen.extend(found)

    return chosen


# ============================================================
# COLORS / UI
# ============================================================

BG = (0.94, 0.96, 0.99, 1)
NAVY = (0.055, 0.12, 0.24, 1)
BLUE = (0.08, 0.39, 0.86, 1)
CYAN = (0.03, 0.62, 0.82, 1)
GREEN = (0.08, 0.65, 0.36, 1)
RED = (0.90, 0.20, 0.25, 1)
ORANGE = (0.95, 0.55, 0.08, 1)
PURPLE = (0.48, 0.25, 0.80, 1)
TEAL = (0.00, 0.55, 0.55, 1)
WHITE = (1, 1, 1, 1)
TEXT = (0.10, 0.13, 0.19, 1)
MUTED = (0.40, 0.45, 0.52, 1)
LIGHT_BLUE = (0.88, 0.94, 1, 1)
LIGHT_GREEN = (0.87, 0.97, 0.90, 1)
LIGHT_YELLOW = (1.0, 0.95, 0.76, 1)


def rounded(widget, color, radius=12):
    with widget.canvas.before:
        Color(*color)
        widget._rounded = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[dp(radius)]
        )

    def update(*_):
        widget._rounded.pos = widget.pos
        widget._rounded.size = widget.size

    widget.bind(pos=update, size=update)


class Card(BoxLayout):
    def __init__(self, color=WHITE, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(9)
        rounded(self, color, 12)


class KMapWidget(Widget):
    """A 100% width-responsive 2/3/4-variable K-map."""

    LOOP_COLORS = [RED, BLUE, GREEN, ORANGE, PURPLE, CYAN, TEAL]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.n = 4
        self.values = ["0"] * 16
        self.groups = []
        self._labels = []
        self.bind(size=self.redraw, pos=self.redraw)

    def set_data(self, n, values, groups):
        self.n = n
        self.values = list(values)
        self.groups = list(groups)
        self.redraw()

    def layout(self):
        if self.n == 2:
            return ["0", "1"], ["0", "1"], [[0, 1], [2, 3]]
        if self.n == 3:
            return ["0", "1"], ["00", "01", "11", "10"], [
                [0, 1, 3, 2],
                [4, 5, 7, 6]
            ]
        return ["00", "01", "11", "10"], ["00", "01", "11", "10"], [
            [0, 1, 3, 2],
            [4, 5, 7, 6],
            [12, 13, 15, 14],
            [8, 9, 11, 10]
        ]

    def clear_labels(self):
        for lab in self._labels:
            if lab.parent:
                self.remove_widget(lab)
        self._labels = []

    def make_label(self, **kwargs):
        lab = Label(**kwargs)
        self._labels.append(lab)
        self.add_widget(lab)
        return lab

    def redraw(self, *_):
        self.clear_labels()
        self.canvas.clear()

        row_labels, col_labels, cells = self.layout()
        rows = len(cells)
        cols = len(cells[0])

        # Safe phone margins. The K-map NEVER uses more than available width.
        left = dp(34)
        right = dp(7)
        top = dp(28)
        bottom = dp(8)

        grid_width = max(dp(120), self.width - left - right)
        cell_w = grid_width / cols

        grid_height_available = max(dp(120), self.height - top - bottom)
        cell_h = min(dp(55), grid_height_available / rows)

        grid_height = cell_h * rows
        grid_x = left
        grid_y = max(bottom, (self.height - grid_height) / 2)

        # K-map white background
        with self.canvas:
            Color(WHITE[0], WHITE[1], WHITE[2], WHITE[3])
            Rectangle(pos=(0, 0), size=self.size)

        # Cells
        for r in range(rows):
            for c in range(cols):
                m = cells[r][c]
                val = self.values[m] if m < len(self.values) else "0"
                x = grid_x + c * cell_w
                y = grid_y + (rows - 1 - r) * cell_h

                if val == "1":
                    fill = LIGHT_GREEN
                elif val == "X":
                    fill = LIGHT_YELLOW
                else:
                    fill = WHITE

                with self.canvas:
                    Color(*fill)
                    Rectangle(pos=(x, y), size=(cell_w, cell_h))
                    Color(0.55, 0.60, 0.68, 1)
                    Line(rectangle=(x, y, cell_w, cell_h), width=1.0)

                lab = self.make_label(
                    text=f"m{m}\n{val}",
                    color=TEXT,
                    bold=(val == "1"),
                    font_size=dp(11),
                    halign="center",
                    valign="middle",
                    size_hint=(None, None),
                    size=(cell_w, cell_h),
                    pos=(x, y)
                )
                lab.text_size = lab.size

        # Column labels
        for c, txt in enumerate(col_labels):
            self.make_label(
                text=txt,
                color=NAVY,
                bold=True,
                font_size=dp(9),
                size_hint=(None, None),
                size=(cell_w, dp(20)),
                pos=(grid_x + c * cell_w, grid_y + grid_height + dp(2))
            )

        # Row labels
        for r, txt in enumerate(row_labels):
            y = grid_y + (rows - 1 - r) * cell_h
            self.make_label(
                text=txt,
                color=NAVY,
                bold=True,
                font_size=dp(9),
                size_hint=(None, None),
                size=(left - dp(5), cell_h),
                pos=(0, y)
            )

        # Axis names
        self.make_label(
            text="CD" if self.n == 4 else ("BC" if self.n == 3 else "B"),
            color=BLUE,
            bold=True,
            font_size=dp(9),
            size_hint=(None, None),
            size=(dp(30), dp(20)),
            pos=(grid_x, grid_y + grid_height + dp(16))
        )

        if self.n == 4:
            self.make_label(
                text="AB",
                color=BLUE,
                bold=True,
                font_size=dp(9),
                size_hint=(None, None),
                size=(dp(30), dp(20)),
                pos=(dp(1), grid_y + grid_height / 2)
            )

        # Group loops.
        # Loop is drawn around the actual selected rectangle.
        for gi, term in enumerate(self.groups):
            selected = []
            for r in range(rows):
                for c in range(cols):
                    m = cells[r][c]
                    if covers(term, m, self.n):
                        selected.append((r, c))

            if not selected:
                continue

            rs = [x[0] for x in selected]
            cs = [x[1] for x in selected]

            r0, r1 = min(rs), max(rs)
            c0, c1 = min(cs), max(cs)

            x = grid_x + c0 * cell_w + dp(3)
            y = grid_y + (rows - 1 - r1) * cell_h + dp(3)
            w = (c1 - c0 + 1) * cell_w - dp(6)
            h = (r1 - r0 + 1) * cell_h - dp(6)

            col = self.LOOP_COLORS[gi % len(self.LOOP_COLORS)]

            with self.canvas:
                Color(*col)
                Line(
                    rounded_rectangle=(x, y, w, h, dp(10)),
                    width=2.7
                )

            # Small group number tag inside top-left of loop.
            tag = self.make_label(
                text=f"G{gi + 1}",
                color=WHITE,
                bold=True,
                font_size=dp(8),
                size_hint=(None, None),
                size=(dp(23), dp(18)),
                pos=(x + dp(3), y + h - dp(20))
            )
            with tag.canvas.before:
                Color(*col)
                tag._tagbg = RoundedRectangle(
                    pos=tag.pos, size=tag.size, radius=[dp(6)]
                )
            tag.bind(
                pos=lambda w, *_: setattr(w._tagbg, "pos", w.pos),
                size=lambda w, *_: setattr(w._tagbg, "size", w.size)
            )


# ============================================================
# APP
# ============================================================

class KMapSolverApp(App):

    def build(self):
        Window.clearcolor = BG
        self.n = 4
        self.inputs = []

        root = BoxLayout(
            orientation="vertical",
            padding=(dp(7), dp(5), dp(7), dp(3)),
            spacing=dp(4)
        )

        # Header
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(61),
            padding=(dp(10), dp(3))
        )
        rounded(header, NAVY, 13)

        header.add_widget(Label(
            text="K-MAP SOLVER",
            color=WHITE,
            bold=True,
            font_size=dp(20),
            size_hint_y=None,
            height=dp(31)
        ))
        header.add_widget(Label(
            text="Truth Table  •  K-Map  •  Group Loops  •  SOP",
            color=(0.78, 0.89, 1, 1),
            font_size=dp(8.5),
            size_hint_y=None,
            height=dp(19)
        ))
        root.add_widget(header)

        # Main content scrolls vertically only.
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(4)
        )

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter("height"))

        # Controls
        control = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(78),
            spacing=dp(5)
        )

        row1 = BoxLayout(spacing=dp(6), size_hint_y=None, height=dp(34))
        row1.add_widget(Label(
            text="Variables",
            color=TEXT,
            bold=True,
            font_size=dp(12),
            size_hint_x=0.30
        ))

        self.spinner = Spinner(
            text="4",
            values=("2", "3", "4"),
            font_size=dp(13),
            background_normal="",
            background_color=LIGHT_BLUE,
            color=NAVY
        )
        self.spinner.bind(text=self.change_vars)
        row1.add_widget(self.spinner)

        solve = Button(
            text="SOLVE",
            bold=True,
            font_size=dp(12),
            background_normal="",
            background_color=BLUE,
            color=WHITE
        )
        solve.bind(on_release=lambda *_: self.solve())
        row1.add_widget(solve)

        clear = Button(
            text="CLEAR",
            bold=True,
            font_size=dp(12),
            background_normal="",
            background_color=(0.45, 0.50, 0.58, 1),
            color=WHITE
        )
        clear.bind(on_release=lambda *_: self.create_table())
        row1.add_widget(clear)

        control.add_widget(row1)
        control.add_widget(Label(
            text="Enter 0, 1 or X in the F column",
            color=MUTED,
            font_size=dp(9),
            size_hint_y=None,
            height=dp(20)
        ))
        content.add_widget(control)

        # Truth table
        truth = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(222),
            spacing=dp(3)
        )
        truth.add_widget(Label(
            text="① TRUTH TABLE",
            color=NAVY,
            bold=True,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(25)
        ))

        table_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint_y=None,
            height=dp(180),
            bar_width=dp(3)
        )
        self.table = GridLayout(
            cols=5,
            spacing=dp(1),
            size_hint_y=None
        )
        self.table.bind(minimum_height=self.table.setter("height"))
        table_scroll.add_widget(self.table)
        truth.add_widget(table_scroll)
        content.add_widget(truth)

        # K-map
        kcard = Card(
            orientation="vertical",
            size_hint_y=None,
            height=dp(300),
            spacing=dp(2)
        )
        kcard.add_widget(Label(
            text="② K-MAP & GROUP LOOPS",
            color=NAVY,
            bold=True,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(25)
        ))
        self.kmap = KMapWidget(
            size_hint_y=None,
            height=dp(264)
        )
        kcard.add_widget(self.kmap)
        content.add_widget(kcard)

        # Result / simplification steps
        self.steps_card = Card(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4)
        )
        self.steps_card.add_widget(Label(
            text="③ GROUP SIMPLIFICATION",
            color=NAVY,
            bold=True,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(25)
        ))

        self.steps_box = BoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None
        )
        self.steps_box.bind(minimum_height=self.steps_box.setter("height"))
        self.steps_card.add_widget(self.steps_box)

        content.add_widget(self.steps_card)

        scroll.add_widget(content)
        root.add_widget(scroll)

        # Fixed footer. It never overlaps content.
        footer = Label(
            text="Developed by Salman  •  md.salmanfarsi.eee@gmail.com",
            color=MUTED,
            font_size=dp(7.5),
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(18)
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

        cols = self.n + 1
        self.table.cols = cols

        # Fit table exactly to phone width.
        table_width = max(dp(250), Window.width - dp(30))
        col_w = table_width / cols
        row_h = dp(26)

        headers = [chr(ord("A") + i) for i in range(self.n)] + ["F"]

        for h in headers:
            lab = Label(
                text=h,
                color=WHITE,
                bold=True,
                font_size=dp(10),
                size_hint=(None, None),
                size=(col_w, row_h)
            )
            with lab.canvas.before:
                Color(*BLUE)
                bg = Rectangle(pos=lab.pos, size=lab.size)
            lab.bind(
                pos=lambda w, *_: setattr(bg, "pos", w.pos),
                size=lambda w, *_: setattr(bg, "size", w.size)
            )
            self.table.add_widget(lab)

        for m in range(1 << self.n):
            bits = format(m, f"0{self.n}b")

            for bit in bits:
                self.table.add_widget(Label(
                    text=bit,
                    color=TEXT,
                    font_size=dp(10),
                    size_hint=(None, None),
                    size=(col_w, row_h)
                ))

            field = TextInput(
                text="0",
                multiline=False,
                halign="center",
                font_size=dp(11),
                size_hint=(None, None),
                size=(col_w, row_h),
                background_normal="",
                background_color=LIGHT_BLUE,
                foreground_color=TEXT,
                cursor_color=BLUE
            )
            self.inputs.append(field)
            self.table.add_widget(field)

        self.steps_box.clear_widgets()
        self.steps_box.add_widget(Label(
            text="Fill the F column and press SOLVE.",
            color=MUTED,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(34)
        ))
        self.steps_card.height = dp(72)

        self.kmap.set_data(self.n, ["0"] * (1 << self.n), [])

    def add_step(self, number, term, minterms, color):
        card = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(7),
            padding=(dp(5), dp(3))
        )
        rounded(card, (0.98, 0.99, 1, 1), 9)

        badge = Label(
            text=f"G{number}",
            color=WHITE,
            bold=True,
            font_size=dp(11),
            size_hint_x=None,
            width=dp(38)
        )
        with badge.canvas.before:
            Color(*color)
            bg = RoundedRectangle(
                pos=badge.pos, size=badge.size, radius=[dp(7)]
            )
        badge.bind(
            pos=lambda w, *_: setattr(bg, "pos", w.pos),
            size=lambda w, *_: setattr(bg, "size", w.size)
        )

        info = Label(
            text=f"m({', '.join(map(str, minterms))})  →  {term}",
            color=TEXT,
            bold=True,
            font_size=dp(11),
            halign="left",
            valign="middle"
        )
        info.text_size = (0, None)

        card.add_widget(badge)
        card.add_widget(info)
        self.steps_box.add_widget(card)

    def solve(self):
        vals = []

        for field in self.inputs:
            value = field.text.strip().upper()
            if value not in ("0", "1", "X"):
                self.show_error("Use only 0, 1 or X in the F column.")
                return
            vals.append(value)

        ones = [i for i, v in enumerate(vals) if v == "1"]
        dcs = [i for i, v in enumerate(vals) if v == "X"]

        if not ones:
            groups = []
            final = "0"
        elif len(ones) == (1 << self.n):
            groups = []
            final = "1"
        else:
            groups = choose_groups(ones, dcs, self.n)
            final = " + ".join(expression(g, self.n) for g in groups)

        self.kmap.set_data(self.n, vals, groups)

        self.steps_box.clear_widgets()

        # Final expression banner
        result = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(62),
            padding=(dp(8), dp(3))
        )
        rounded(result, LIGHT_BLUE, 10)

        result.add_widget(Label(
            text="FINAL BOOLEAN EXPRESSION",
            color=BLUE,
            bold=True,
            font_size=dp(10),
            size_hint_y=None,
            height=dp(20)
        ))
        result.add_widget(Label(
            text=f"F = {final}",
            color=NAVY,
            bold=True,
            font_size=dp(17),
            size_hint_y=None,
            height=dp(31)
        ))
        self.steps_box.add_widget(result)

        if groups:
            self.steps_box.add_widget(Label(
                text="Individual groups:",
                color=NAVY,
                bold=True,
                font_size=dp(12),
                size_hint_y=None,
                height=dp(25)
            ))

            colors = [RED, BLUE, GREEN, ORANGE, PURPLE, CYAN, TEAL]

            for i, g in enumerate(groups):
                ms = [m for m in ones if covers(g, m, self.n)]
                self.add_step(
                    i + 1,
                    expression(g, self.n),
                    ms,
                    colors[i % len(colors)]
                )
        else:
            self.steps_box.add_widget(Label(
                text="No grouping is required.",
                color=MUTED,
                font_size=dp(11),
                size_hint_y=None,
                height=dp(30)
            ))

        if dcs:
            self.steps_box.add_widget(Label(
                text="Don't-care cells: " + ", ".join(map(str, dcs)),
                color=ORANGE,
                font_size=dp(10),
                size_hint_y=None,
                height=dp(24)
            ))

        # Let the card grow ONLY as much as its content needs.
        self.steps_card.height = max(
            dp(75),
            dp(34) + len(self.steps_box.children) * dp(53)
        )

    def show_error(self, message):
        self.steps_box.clear_widgets()
        self.steps_box.add_widget(Label(
            text=message,
            color=RED,
            bold=True,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(40)
        ))
        self.steps_card.height = dp(72)


if __name__ == "__main__":
    KMapSolverApp().run()
