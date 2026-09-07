__version__ = "4.0.0"

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

# ---------- Boolean logic ----------

def combine(a, b):
    diff, out = 0, []
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

def expr(term, n):
    names = "ABCD"
    s = ""
    for i, bit in enumerate(term):
        if bit == "1":
            s += names[i]
        elif bit == "0":
            s += names[i] + "'"
    return s or "1"

def primes(ones, dcs, n):
    current = {format(m, f"0{n}b") for m in ones + dcs}
    result = set()
    while current:
        items = sorted(current)
        nxt, used = set(), set()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                c = combine(items[i], items[j])
                if c:
                    nxt.add(c)
                    used.add(items[i]); used.add(items[j])
        result.update(x for x in current if x not in used)
        current = nxt
    return sorted(result)

def solve_groups(ones, dcs, n):
    if not ones or len(ones) == (1 << n):
        return []
    ps = primes(ones, dcs, n)
    chosen, covered = [], set()

    for m in ones:
        hits = [p for p in ps if covers(p, m, n)]
        if len(hits) == 1 and hits[0] not in chosen:
            chosen.append(hits[0])
    for p in chosen:
        covered.update(m for m in ones if covers(p, m, n))

    rem = [m for m in ones if m not in covered]
    avail = [p for p in ps if p not in chosen]

    for r in range(1, len(avail) + 1):
        found = None
        for combo in combinations(avail, r):
            test = chosen + list(combo)
            if all(any(covers(p, m, n) for p in test) for m in ones):
                found = list(combo); break
        if found is not None:
            chosen.extend(found); break
    return chosen

# ---------- Aesthetic palette ----------
BG = (0.965, 0.955, 0.935, 1)       # warm paper
NAVY = (0.12, 0.16, 0.22, 1)
INK = (0.18, 0.19, 0.20, 1)
MUTED = (0.45, 0.46, 0.47, 1)
CREAM = (0.995, 0.985, 0.96, 1)
SAGE = (0.72, 0.82, 0.70, 1)
SAGE_LIGHT = (0.91, 0.95, 0.88, 1)
BLUE = (0.31, 0.48, 0.67, 1)
BLUE_LIGHT = (0.89, 0.93, 0.97, 1)
TERRACOTTA = (0.78, 0.38, 0.31, 1)
MUSTARD = (0.78, 0.61, 0.28, 1)
PLUM = (0.48, 0.35, 0.49, 1)
TEAL = (0.30, 0.55, 0.53, 1)
WHITE = (1, 1, 1, 1)

LOOP_COLORS = [TERRACOTTA, BLUE, SAGE, MUSTARD, PLUM, TEAL]

def rounded(widget, color, radius=12):
    with widget.canvas.before:
        Color(*color)
        widget._bg = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[dp(radius)]
        )
    def update(*_):
        widget._bg.pos = widget.pos
        widget._bg.size = widget.size
    widget.bind(pos=update, size=update)

class Card(BoxLayout):
    def __init__(self, color=CREAM, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(9)
        rounded(self, color, 11)

# ---------- K-map: compact, no overlap ----------

class KMap(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.n = 4
        self.values = ["0"] * 16
        self.groups = []
        self.labels = []
        self.bind(size=self.redraw, pos=self.redraw)

    def set_data(self, n, values, groups):
        self.n, self.values, self.groups = n, list(values), list(groups)
        self.redraw()

    def clear_labels(self):
        for x in self.labels:
            if x.parent:
                self.remove_widget(x)
        self.labels = []

    def lab(self, **kw):
        x = Label(**kw)
        self.labels.append(x)
        self.add_widget(x)
        return x

    def layout(self):
        if self.n == 2:
            return ["0","1"], ["0","1"], [[0,1],[2,3]]
        if self.n == 3:
            return ["0","1"], ["00","01","11","10"], [[0,1,3,2],[4,5,7,6]]
        return ["00","01","11","10"], ["00","01","11","10"], [
            [0,1,3,2],[4,5,7,6],[12,13,15,14],[8,9,11,10]
        ]

    def redraw(self, *_):
        self.clear_labels()
        self.canvas.clear()
        rows_lbl, cols_lbl, cells = self.layout()
        rows, cols = len(cells), len(cells[0])

        # Compact geometry: map sits near the top of its card.
        left = dp(30)
        top = dp(25)
        bottom = dp(5)
        grid_w = max(dp(120), self.width - left - dp(5))
        cw = grid_w / cols
        ch = min(dp(48), max(dp(35), (self.height - top - bottom) / rows))
        grid_h = ch * rows
        gx = left
        gy = bottom + max(0, (self.height - top - bottom - grid_h) * 0.15)

        with self.canvas:
            Color(*CREAM)
            Rectangle(pos=(0,0), size=self.size)

        for r in range(rows):
            for c in range(cols):
                m = cells[r][c]
                v = self.values[m]
                fill = SAGE_LIGHT if v == "1" else (1.0,0.96,0.80,1) if v == "X" else CREAM
                x = gx + c*cw
                y = gy + (rows-1-r)*ch
                with self.canvas:
                    Color(*fill)
                    Rectangle(pos=(x,y), size=(cw,ch))
                    Color(0.65,0.64,0.60,1)
                    Line(rectangle=(x,y,cw,ch), width=0.9)
                t = self.lab(text=f"m{m}\n{v}", color=INK, bold=(v=="1"),
                             font_size=dp(10), halign="center", valign="middle",
                             size_hint=(None,None), size=(cw,ch), pos=(x,y))
                t.text_size = t.size

        for c, s in enumerate(cols_lbl):
            self.lab(text=s, color=NAVY, bold=True, font_size=dp(9),
                     size_hint=(None,None), size=(cw,dp(18)),
                     pos=(gx+c*cw, gy+grid_h+dp(1)))
        for r, s in enumerate(rows_lbl):
            y = gy+(rows-1-r)*ch
            self.lab(text=s, color=NAVY, bold=True, font_size=dp(9),
                     size_hint=(None,None), size=(left-dp(3),ch), pos=(0,y))

        self.lab(text="CD" if self.n==4 else ("BC" if self.n==3 else "B"),
                 color=BLUE, bold=True, font_size=dp(9),
                 size_hint=(None,None), size=(dp(25),dp(18)),
                 pos=(gx, gy+grid_h+dp(17)))
        if self.n == 4:
            self.lab(text="AB", color=BLUE, bold=True, font_size=dp(9),
                     size_hint=(None,None), size=(dp(28),dp(18)),
                     pos=(0,gy+grid_h/2))

        # Loops are drawn AFTER cells, but labels remain readable.
        for i, term in enumerate(self.groups):
            selected = [(r,c) for r in range(rows) for c in range(cols)
                        if covers(term, cells[r][c], self.n)]
            if not selected: continue
            rs, cs = zip(*selected)
            r0,r1,c0,c1=min(rs),max(rs),min(cs),max(cs)
            x=gx+c0*cw+dp(3); y=gy+(rows-1-r1)*ch+dp(3)
            w=(c1-c0+1)*cw-dp(6); h=(r1-r0+1)*ch-dp(6)
            col=LOOP_COLORS[i % len(LOOP_COLORS)]
            with self.canvas:
                Color(*col)
                Line(rounded_rectangle=(x,y,w,h,dp(9)), width=2.4)
            tag=self.lab(text=f"G{i+1}", color=WHITE, bold=True, font_size=dp(7.5),
                         size_hint=(None,None), size=(dp(21),dp(16)),
                         pos=(x+dp(2),y+h-dp(18)))
            with tag.canvas.before:
                Color(*col)
                tag.bg=RoundedRectangle(pos=tag.pos,size=tag.size,radius=[dp(5)])
            tag.bind(pos=lambda w,*_: setattr(w.bg,"pos",w.pos),
                     size=lambda w,*_: setattr(w.bg,"size",w.size))

# ---------- App ----------

class KMapSolver(App):
    def build(self):
        Window.clearcolor = BG
        self.n=4; self.inputs=[]

        root=BoxLayout(orientation="vertical", padding=(dp(7),dp(5),dp(7),dp(3)), spacing=dp(5))

        header=BoxLayout(orientation="vertical", size_hint_y=None, height=dp(63), padding=(dp(8),dp(3)))
        rounded(header,NAVY,13)
        header.add_widget(Label(text="K-MAP SOLVER",color=WHITE,bold=True,font_size=dp(20),
                                size_hint_y=None,height=dp(33)))
        header.add_widget(Label(text="Truth Table  •  K-Map  •  Group Loops  •  SOP",
                                color=(0.78,0.82,0.84,1),font_size=dp(8.5),
                                size_hint_y=None,height=dp(18)))
        root.add_widget(header)

        scroll=ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(3))
        content=BoxLayout(orientation="vertical",spacing=dp(7),size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        controls=Card(orientation="horizontal",size_hint_y=None,height=dp(58),spacing=dp(6))
        controls.add_widget(Label(text="Variables",color=INK,bold=True,font_size=dp(11),size_hint_x=.25))
        self.spinner=Spinner(text="4",values=("2","3","4"),font_size=dp(12),
                             background_normal="",background_color=BLUE_LIGHT,color=NAVY)
        self.spinner.bind(text=self.change_vars)
        controls.add_widget(self.spinner)
        solve=Button(text="SOLVE",bold=True,font_size=dp(11),background_normal="",
                     background_color=BLUE,color=WHITE)
        solve.bind(on_release=lambda *_: self.solve())
        controls.add_widget(solve)
        clear=Button(text="CLEAR",bold=True,font_size=dp(11),background_normal="",
                     background_color=(0.48,0.48,0.47,1),color=WHITE)
        clear.bind(on_release=lambda *_: self.create_table())
        controls.add_widget(clear)
        content.add_widget(controls)

        truth=Card(orientation="vertical",size_hint_y=None,height=dp(390),spacing=dp(3))
        truth.add_widget(Label(text="①  TRUTH TABLE",color=NAVY,bold=True,font_size=dp(14),
                               size_hint_y=None,height=dp(25)))
        ts=ScrollView(do_scroll_x=False,do_scroll_y=True,bar_width=dp(3),size_hint_y=None,height=dp(345))
        self.table=GridLayout(cols=5,spacing=dp(1),size_hint_y=None)
        self.table.bind(minimum_height=self.table.setter("height"))
        ts.add_widget(self.table); truth.add_widget(ts)
        content.add_widget(truth)

        kcard=Card(orientation="vertical",size_hint_y=None,height=dp(255),spacing=dp(2))
        kcard.add_widget(Label(text="②  K-MAP & GROUP LOOPS",color=NAVY,bold=True,font_size=dp(14),
                               size_hint_y=None,height=dp(25)))
        self.kmap=KMap(size_hint_y=None,height=dp(220))
        kcard.add_widget(self.kmap); content.add_widget(kcard)

        self.steps_card=Card(orientation="vertical",size_hint_y=None,spacing=dp(5))
        self.steps_card.add_widget(Label(text="③  GROUP SIMPLIFICATION",color=NAVY,bold=True,font_size=dp(14),
                                         size_hint_y=None,height=dp(25)))
        self.steps=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None)
        self.steps.bind(minimum_height=self.steps.setter("height"))
        self.steps_card.add_widget(self.steps)
        content.add_widget(self.steps_card)

        scroll.add_widget(content); root.add_widget(scroll)

        footer=Label(text="Developed by Salman  •  md.salmanfarsi.eee@gmail.com",color=MUTED,
                     font_size=dp(7.2),halign="right",valign="middle",
                     size_hint_y=None,height=dp(18))
        footer.bind(size=lambda w,s:setattr(w,"text_size",s))
        root.add_widget(footer)

        self.create_table()
        return root

    def change_vars(self,_,v):
        self.n=int(v); self.create_table()

    def create_table(self):
        self.table.clear_widgets(); self.inputs=[]
        self.table.cols=self.n+1
        width=max(dp(220),Window.width-dp(30)); cw=width/(self.n+1); rh=dp(25)
        heads=[chr(ord("A")+i) for i in range(self.n)]+["F"]
        for h in heads:
            x=Label(text=h,color=WHITE,bold=True,font_size=dp(10),size_hint=(None,None),size=(cw,rh))
            with x.canvas.before:
                Color(*BLUE); bg=Rectangle(pos=x.pos,size=x.size)
            x.bind(pos=lambda w,*_:setattr(bg,"pos",w.pos),size=lambda w,*_:setattr(bg,"size",w.size))
            self.table.add_widget(x)
        for m in range(1<<self.n):
            for b in format(m,f"0{self.n}b"):
                self.table.add_widget(Label(text=b,color=INK,font_size=dp(10),size_hint=(None,None),size=(cw,rh)))
            e=TextInput(text="0",multiline=False,halign="center",font_size=dp(11),
                        size_hint=(None,None),size=(cw,rh),background_normal="",
                        background_color=BLUE_LIGHT,foreground_color=INK,
                        selection_color=(0,0,0,0),cursor_color=BLUE)
            self.inputs.append(e); self.table.add_widget(e)

        self.kmap.set_data(self.n,["0"]*(1<<self.n),[])
        self.show_message("Fill the F column and press SOLVE.")

    def show_message(self,msg):
        self.steps.clear_widgets()
        self.steps.add_widget(Label(text=msg,color=MUTED,font_size=dp(11),
                                    size_hint_y=None,height=dp(35)))
        self.steps_card.height=dp(73)

    def group_card(self,i,term,mins,col):
        row=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(49),spacing=dp(7),padding=(dp(4),dp(3)))
        rounded(row,(0.985,0.98,0.95,1),8)
        badge=Label(text=f"G{i}",color=WHITE,bold=True,font_size=dp(10),size_hint_x=None,width=dp(36))
        with badge.canvas.before:
            Color(*col); bg=RoundedRectangle(pos=badge.pos,size=badge.size,radius=[dp(6)])
        badge.bind(pos=lambda w,*_:setattr(bg,"pos",w.pos),size=lambda w,*_:setattr(bg,"size",w.size))
        info=Label(text=f"m({', '.join(map(str,mins))})   →   {term}",
                   color=INK,bold=True,font_size=dp(10),halign="left",valign="middle")
        row.add_widget(badge); row.add_widget(info); self.steps.add_widget(row)

    def solve(self):
        vals=[]
        for e in self.inputs:
            v=e.text.strip().upper()
            if v not in ("0","1","X"):
                self.show_message("Use only 0, 1 or X in the F column."); return
            vals.append(v)
        ones=[i for i,v in enumerate(vals) if v=="1"]
        dcs=[i for i,v in enumerate(vals) if v=="X"]

        if not ones: groups=[]; final="0"
        elif len(ones)==(1<<self.n): groups=[]; final="1"
        else:
            groups=solve_groups(ones,dcs,self.n)
            final=" + ".join(expr(g,self.n) for g in groups)

        self.kmap.set_data(self.n,vals,groups)
        self.steps.clear_widgets()

        banner=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(58),padding=(dp(6),dp(2)))
        rounded(banner,BLUE_LIGHT,9)
        banner.add_widget(Label(text="FINAL BOOLEAN EXPRESSION",color=BLUE,bold=True,font_size=dp(9),
                                size_hint_y=None,height=dp(18)))
        banner.add_widget(Label(text=f"F = {final}",color=NAVY,bold=True,font_size=dp(16),
                                size_hint_y=None,height=dp(29)))
        self.steps.add_widget(banner)

        if groups:
            self.steps.add_widget(Label(text="Individual groups",color=NAVY,bold=True,font_size=dp(11),
                                        size_hint_y=None,height=dp(23)))
            for i,g in enumerate(groups):
                mins=[m for m in ones if covers(g,m,self.n)]
                self.group_card(i+1,expr(g,self.n),mins,LOOP_COLORS[i%len(LOOP_COLORS)])
        else:
            self.steps.add_widget(Label(text="No grouping is required.",color=MUTED,font_size=dp(11),
                                        size_hint_y=None,height=dp(28)))
        if dcs:
            self.steps.add_widget(Label(text="Don't-care cells: "+", ".join(map(str,dcs)),
                                        color=MUSTARD,font_size=dp(10),size_hint_y=None,height=dp(23)))

        # Exact content height; no overlap with the next section.
        self.steps_card.height=max(dp(80), dp(36)+sum(
            child.height+dp(5) for child in self.steps.children
        ))

if __name__=="__main__":
    KMapSolver().run()
