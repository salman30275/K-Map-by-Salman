__version__ = "1.0.0"

from itertools import combinations
from kivy.app import App
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


class KMapWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.n = 4
        self.values = ["0"] * 16
        self.groups = []
        self.bind(size=lambda *_: self.draw())

    def set_data(self, n, values, groups):
        self.n = n
        self.values = values
        self.groups = groups
        self.draw()

    def draw(self):
        self.canvas.clear()
        rows, cols = layout(self.n)
        left = dp(42)
        top = dp(20)
        cw = max(dp(65), (self.width - left - dp(8)) / len(cols))
        ch = max(dp(58), (self.height - top - dp(8)) / len(rows))

        with self.canvas:
            Color(0.15, 0.15, 0.15, 1)
            # column labels
            col_labels = ["0", "1"] if self.n == 2 else (["00", "01", "11", "10"])
            for j, txt in enumerate(col_labels):
                pass

            # grid
            for i, rv in enumerate(rows):
                for j, cv in enumerate(cols):
                    m = minterm_at(self.n, rv, cv)
                    x = left + j * cw
                    y = self.height - top - (i + 1) * ch
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(x, y), size=(cw, ch))
                    Color(0.15, 0.15, 0.15, 1)
                    Line(rectangle=(x, y, cw, ch), width=1.2)

        # K-map text is drawn as labels in a separate overlay-like grid.
        self._draw_text_overlay(left, top, cw, ch, rows, cols)

        # Group loops
        colors = [
            (0.90, 0.15, 0.15, 1),
            (0.10, 0.45, 0.90, 1),
            (0.10, 0.65, 0.25, 1),
            (0.95, 0.55, 0.05, 1),
            (0.55, 0.15, 0.75, 1),
            (0.05, 0.60, 0.55, 1),
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
            with self.canvas:
                Color(*color)
                x = left + c0 * cw + dp(5)
                y = self.height - top - (r1 + 1) * ch + dp(5)
                w = (c1 - c0 + 1) * cw - dp(10)
                h = (r1 - r0 + 1) * ch - dp(10)
                Line(rounded_rectangle=(x, y, w, h, dp(12)), width=2.8)

    def _draw_text_overlay(self, left, top, cw, ch, rows, cols):
        # Remove old text children and rebuild.
        for child in list(self.children):
            if getattr(child, "_kmap_text", False):
                self.remove_widget(child)

        col_labels = ["0", "1"] if self.n == 2 else ["00", "01", "11", "10"]
        row_labels = ["0", "1"] if self.n < 4 else ["00", "01", "11", "10"]

        for j, txt in enumerate(col_labels):
            lab = Label(text=txt, font_size=dp(11), bold=True, color=(0.1,0.1,0.1,1),
                        size_hint=(None,None), size=(cw,dp(20)),
                        pos=(left+j*cw, self.height-dp(20)))
            lab._kmap_text = True
            self.add_widget(lab)

        for i, txt in enumerate(row_labels):
            y = self.height - top - (i+1)*ch
            lab = Label(text=txt, font_size=dp(11), bold=True, color=(0.1,0.1,0.1,1),
                        size_hint=(None,None), size=(left-dp(5),ch),
                        pos=(0,y))
            lab._kmap_text = True
            self.add_widget(lab)

        for i, rv in enumerate(rows):
            for j, cv in enumerate(cols):
                m = minterm_at(self.n, rv, cv)
                x = left+j*cw
                y = self.height-top-(i+1)*ch
                lab = Label(text=f"m{m}\n{self.values[m]}",
                            font_size=dp(12), color=(0.05,0.05,0.05,1),
                            halign="center", valign="middle",
                            size_hint=(None,None), size=(cw,ch),
                            pos=(x,y))
                lab._kmap_text = True
                lab.text_size = lab.size
                self.add_widget(lab)


class KMapApp(App):
    def build(self):
        self.n = 4
        self.inputs = []
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        title = Label(text="VISUAL K-MAP SOLVER", font_size=dp(24), bold=True,
                      size_hint_y=None, height=dp(45))
        root.add_widget(title)

        root.add_widget(Label(text="Truth Table → K-Map → Group Loops → Boolean Expression",
                              font_size=dp(12), size_hint_y=None, height=dp(30)))

        controls = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(7))
        controls.add_widget(Label(text="Variables:", size_hint_x=None, width=dp(85)))
        self.spinner = Spinner(text="4", values=("2","3","4"), size_hint_x=None, width=dp(70))
        self.spinner.bind(text=self.change_vars)
        controls.add_widget(self.spinner)

        solve = Button(text="SOLVE K-MAP", size_hint_x=None, width=dp(135))
        solve.bind(on_release=lambda *_: self.solve())
        controls.add_widget(solve)

        clear = Button(text="CLEAR", size_hint_x=None, width=dp(90))
        clear.bind(on_release=lambda *_: self.create_table())
        controls.add_widget(clear)
        root.add_widget(controls)

        body = ScrollView(do_scroll_x=False)
        inside = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        inside.bind(minimum_height=inside.setter("height"))
        body.add_widget(inside)

        inside.add_widget(Label(text="TRUTH TABLE", bold=True, size_hint_y=None, height=dp(28)))

        self.table = GridLayout(cols=5, spacing=dp(2), size_hint_y=None)
        self.table.bind(minimum_height=self.table.setter("height"))
        inside.add_widget(self.table)

        inside.add_widget(Label(text="K-MAP", bold=True, size_hint_y=None, height=dp(28)))
        self.kmap = KMapWidget(size_hint_y=None, height=dp(300))
        inside.add_widget(self.kmap)

        inside.add_widget(Label(text="GROUPS / SIMPLIFICATION", bold=True, size_hint_y=None, height=dp(28)))
        self.result_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        self.result_box.bind(minimum_height=self.result_box.setter("height"))
        inside.add_widget(self.result_box)

        root.add_widget(body)
        self.create_table()
        return root

    def change_vars(self, spinner, value):
        self.n = int(value)
        self.create_table()

    def create_table(self):
        self.table.clear_widgets()
        self.inputs = []
        headers = [chr(ord("A")+i) for i in range(self.n)] + ["F"]
        self.table.cols = self.n + 1
        for h in headers:
            self.table.add_widget(Label(text=h, bold=True, size_hint_y=None, height=dp(30)))
        for m in range(1 << self.n):
            bits = format(m, f"0{self.n}b")
            for b in bits:
                self.table.add_widget(Label(text=b, size_hint_y=None, height=dp(32)))
            e = TextInput(text="0", multiline=False, halign="center", size_hint_y=None, height=dp(32))
            self.inputs.append(e)
            self.table.add_widget(e)

        self.result_box.clear_widgets()
        self.result_box.add_widget(Label(text="Enter 0, 1, or X, then press SOLVE K-MAP.",
                                          size_hint_y=None, height=dp(35)))
        self.kmap.set_data(self.n, ["0"]*(1<<self.n), [])

    def solve(self):
        vals = []
        for e in self.inputs:
            s = e.text.strip().upper()
            if s not in ("0","1","X"):
                self.result_box.clear_widgets()
                self.result_box.add_widget(Label(text="Invalid input: use only 0, 1, or X.",
                                                  color=(1,0,0,1), size_hint_y=None, height=dp(40)))
                return
            vals.append(s)

        ones = [i for i,v in enumerate(vals) if v == "1"]
        dc = [i for i,v in enumerate(vals) if v == "X"]
        primes = primes_for(ones, dc, self.n)
        groups = minimum_cover(ones, primes, self.n)
        self.kmap.set_data(self.n, vals, groups)

        self.result_box.clear_widgets()
        if not ones:
            expr = "0"
        elif len(ones) == (1<<self.n):
            expr = "1"
        else:
            expr = " + ".join(term_expr(g,self.n) for g in groups)

        self.result_box.add_widget(Label(text=f"F = {expr}", bold=True, font_size=dp(18),
                                         size_hint_y=None, height=dp(45)))
        if dc:
            self.result_box.add_widget(Label(text="Don't-care minterms: "+", ".join(map(str,dc)),
                                             size_hint_y=None, height=dp(32)))
        for i,g in enumerate(groups,1):
            ms=[m for m in range(1<<self.n) if covers(g,m,self.n)]
            self.result_box.add_widget(Label(
                text=f"Group {i}: {len(ms)} cells   m({', '.join(map(str,ms))})   → {term_expr(g,self.n)}",
                size_hint_y=None, height=dp(35)))


if __name__ == "__main__":
    KMapApp().run()
