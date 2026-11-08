"""bhava (भाव, "feeling"): the emoji picker for Vyom.

A grid of every Unicode 16 emoji (names and groups from Unicode,
keywords from wofi-emoji, MIT), your recent ones first, a rail of
categories on the left, a skin tone remembered per emoji, and a big
preview. Enter types it into the window you were in (wtype) and copies it.

Vim modes: INSERT types into the search box; NORMAL (Esc) moves around
the grid with h/j/k/l and friends, letters don't type. Esc in NORMAL
closes. `[plugin.bhava] start_mode = "normal"` opens in NORMAL.
"""
import json
import os
import subprocess

from gi.repository import GLib, Gtk, Pango

from vyom import Hint, Row, ui, util
from vyom import Plugin as Base
from vyom.panel import keycap_markup

# Both modes
# keybind: Vyom/bhava | Arrows | Move around the emoji grid
# keybind: Vyom/bhava | Enter | Send the emoji to the window you were in (types it, and copies it)
# keybind: Vyom/bhava | Ctrl+C | Copy the emoji only (Ctrl+Enter too)
# keybind: Vyom/bhava | Ctrl+Enter | Copy the emoji only
# keybind: Vyom/bhava | Ctrl+T | Cycle the skin tone of this emoji (remembered per emoji)
# keybind: Vyom/bhava | Tab / Shift+Tab | Switch to the next / previous category
# keybind: Vyom/bhava | Ctrl+1..9 | Switch to that numbered category (Ctrl+0: the tenth)
# keybind: Vyom/bhava insert mode | Esc | Enter normal mode (letters stop typing; move with h/j/k/l)
# NORMAL mode
# keybind: Vyom/bhava normal mode | h / j / k / l | Move left / down / up / right in the grid (a count first repeats: 5j)
# keybind: Vyom/bhava normal mode | w / b | Switch to the next / previous category
# keybind: Vyom/bhava normal mode | gg / G | Jump to the first / last emoji (5gg or 5G: row 5)
# keybind: Vyom/bhava normal mode | 0 / $ | Jump to the start / end of the row
# keybind: Vyom/bhava normal mode | Ctrl+D / Ctrl+U | Scroll half a page down / up
# keybind: Vyom/bhava normal mode | 1..9 | Set a count for the next move (5j, 3l)
# keybind: Vyom/bhava normal mode | y | Copy the emoji only (yank)
# keybind: Vyom/bhava normal mode | t / s | Cycle the skin tone of this emoji
# keybind: Vyom/bhava normal mode | i / a | Enter insert mode (type to search)
# keybind: Vyom/bhava normal mode | / | Search again (clears the search, insert mode)
# keybind: Vyom/bhava normal mode | q | Close the panel
# keybind: Vyom/bhava normal mode | Esc | Close the panel (or cancel a pending count)

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = "bhava"
# Pango markup can't read CSS colours: the theme's peach if it defines one.
PEACH = "#fab387"
TONES = ["", "🏻", "🏼", "🏽", "🏾", "🏿"]
# (key, glyph, name on the rail)
GROUPS = [("recent", "🕘", "Recent"), ("all", "✱", "All"), ("Smileys & Emotion", "😀", "Smileys"),
          ("People & Body", "👋", "People"), ("Animals & Nature", "🐶", "Animals"), ("Food & Drink", "🍕", "Food"),
          ("Activities", "⚽", "Activity"), ("Travel & Places", "✈️", "Travel"), ("Objects", "💡", "Objects"),
          ("Symbols", "🔣", "Symbols"), ("Flags", "🏳️", "Flags")]
NAMES = {k: n for k, _, n in GROUPS}
HINTS = {
    "insert": [("Arrows", "move"), ("Enter", "type"), ("Ctrl+C", "copy"), ("Ctrl+T", "skin tone")],
    "normal": [("hjkl", "move"), ("w/b", "category"), ("Enter", "type"), ("y", "copy"),
               ("t", "skin tone"), ("i", "search")],
}


def shortcode(e):
    return ":" + "".join(c if c.isalnum() else "_" for c in e["n"].lower()).strip("_").replace("__", "_") + ":"


class Plugin(Base):
    name, title, icon, color = "bhava", "Emoji", "\U000f0785", "yellow"
    layout = "grid"
    grid_columns = 8
    preview = True
    preview_width = 260
    placeholder = "Search emoji…   e.g. wind, party, heart"
    hints = []          # per mode: tab_hints()
    empty_text = "No emoji for that"
    # Categories: the panel's tabs (Tab, Ctrl+1..9), drawn as a rail on the left.
    tabs = [(k, glyph, n) for k, glyph, n in GROUPS]
    tab_class = "cat"

    def __init__(self, vyom, conf):
        super().__init__(vyom, conf)
        with open(os.path.join(HERE, "emoji.json"), encoding="utf-8") as f:
            self.emoji = json.load(f)
        self.by_char = {e["e"]: e for e in self.emoji}
        self.tab = "recent"
        self.mode = "insert"
        self.count = ""        # a typed count (NORMAL): "5"
        self.pending = ""      # a half-typed key (NORMAL): "g"
        self.dressed = None    # the panel the rail and footer were added to
        self.rail_buttons = {}
        self.found = None
        self.our_status = False

    # ------------------------------------------------------------ state
    def state(self):
        return util.load_state(STATE, {"recent": [], "tone": 0, "tones": {}})

    def tone_of(self, e, st=None):
        st = st or self.state()
        # Per emoji; the old single setting is the default for the rest.
        return int(st.get("tones", {}).get(e["e"], st.get("tone", 0)) or 0) if e.get("t") else 0

    def toned(self, e, st=None):
        tone = self.tone_of(e, st)
        return e["t"][tone - 1] if tone and e.get("t") and e["t"][tone - 1] else e["e"]

    # ------------------------------------------------------------ the frame
    def header_extra(self):
        self.found = ui.chip("", "gray")
        self.found.set_visible(False)
        return self.found

    def dress(self):
        """The rail of categories on the left and the mode pill in the
        footer, once per panel (Vyom core has no slot for them)."""
        p = self.panel
        if p is None or self.dressed is p or getattr(p, "strip_holder", None) is None:
            return
        self.dressed = p
        p.tab_box.set_visible(False)       # the rail shows the categories instead
        body = p.strip_holder.get_parent().get_parent()
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, homogeneous=True, valign=Gtk.Align.START)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side.add_css_class("bhava-rail")
        side.append(rail)
        side.set_size_request(200, -1)
        self.rail_buttons = {}
        for i, (key, glyph, name) in enumerate(GROUPS):
            b = Gtk.Button()
            b.add_css_class("bhava-cat")
            b.set_can_focus(False)
            inner = Gtk.Box(spacing=10)
            inner.append(ui.label(glyph, "bhava-cat-glyph"))
            inner.append(ui.label(name, "bhava-cat-name", xalign=0, hexpand=True))
            b.set_child(inner)
            b.set_tooltip_text(f"{name} (Ctrl+{(i + 1) % 10})" if i < 10 else f"{name} (Tab)")
            b.connect("clicked", lambda _b, k=key: self.select_tab(k))
            self.rail_buttons[key] = b
            rail.append(b)
        side.set_hexpand(False)    # its labels' hexpand must not widen it
        body.prepend(side)
        p.grid.set_column_spacing(6)
        p.grid.set_row_spacing(6)

        foot = p.status.get_parent()
        self.mode_pill = ui.label("", "bhava-mode", valign=Gtk.Align.CENTER)
        self.pending_label = ui.label("", "bhava-pending", valign=Gtk.Align.CENTER)
        foot.prepend(self.pending_label)
        foot.prepend(self.mode_pill)
        p.tab_hint.set_markup(f"{keycap_markup('Tab')} category")
        self.esc_hint = foot.get_last_child()
        # Clicking the search box is a way into INSERT too.
        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_: self.mode == "normal" and self.set_mode("insert"))
        p.entry.add_controller(click)

    def tab_hints(self):
        return [Hint(keys, what) for keys, what in HINTS[self.mode]]

    def mark_rail(self):
        for k, b in self.rail_buttons.items():
            (b.add_css_class if k == self.tab else b.remove_css_class)("on")

    def set_mode(self, mode):
        self.mode = mode
        self.count = self.pending = ""
        p = self.panel
        if p is None or self.dressed is not p:
            return
        normal = mode == "normal"
        e = p.entry
        e.set_editable(not normal)
        (e.add_css_class if normal else e.remove_css_class)("bhava-normal")
        e.set_placeholder_text("Press i to search,  / to start over" if normal else self.placeholder)
        if not normal:
            e.grab_focus()
            e.set_position(-1)
        pill = self.mode_pill
        pill.set_label("NORMAL" if normal else "INSERT")
        pill.remove_css_class("normal" if not normal else "insert")
        pill.add_css_class(mode)
        p.refresh_hints()
        self.esc_hint.set_markup(f"{keycap_markup('Esc')} {'close' if normal else 'normal mode'}")
        self.show_pending()
        p.update_preview()

    def show_pending(self):
        if self.dressed is self.panel and self.panel is not None:
            text = self.count + self.pending
            self.pending_label.set_label(text)
            self.pending_label.set_visible(bool(text))

    # ------------------------------------------------------------ lifecycle
    def opened(self, args):
        super().opened(args)
        self.dress()
        # Recent first if there are any, else everything.
        if self.tab in ("recent", "all"):
            self.select_tab("recent" if self.state().get("recent") else "all")
        self.mark_rail()
        start = str(self.conf.get("start_mode", "insert")).lower()
        self.set_mode("normal" if start == "normal" else "insert")

    def tab_changed(self, key):
        self.mark_rail()
        # Picking a category is browsing: leave the search for it.
        if self.panel is not None and self.panel.query():
            self.panel.entry.set_text("")
        self.refresh()

    # ------------------------------------------------------------ results
    def search(self, q):
        st = self.state()
        if q:
            scored = []
            for i, e in enumerate(self.emoji):
                s = util.fuzzy(q, e["n"], loose=False)
                k = util.fuzzy(q, e.get("k", ""), loose=False) if e.get("k") else None
                best = max(x for x in (s and s * 2, k) if x is not None) if (s is not None or k is not None) else None
                if best is not None:
                    scored.append((-best, i, e))
            scored.sort()
            items = [e for _, _, e in scored]
        elif self.tab == "recent":
            items = [self.by_char[c] for c in st.get("recent", []) if c in self.by_char] or self.emoji
        elif self.tab == "all":
            items = self.emoji
        else:
            items = [e for e in self.emoji if e["g"] == self.tab]
        return [Row(self.toned(e, st), e["n"], data=e) for e in items[:400]]

    def build_strip(self):
        p = self.panel
        n = len(p.items) if p else 0
        q = p.query() if p else ""
        if self.found is not None:
            self.found.set_label(f"{n} found")
            self.found.set_visible(bool(q))
        if q:
            return ui.section("Matches", n, "best first")
        if self.tab == "recent" and not self.state().get("recent"):
            return ui.section("All", n, "nothing recent yet")
        return ui.section(NAMES.get(self.tab, self.tab), n)

    def build_preview(self, row):
        e = row.data
        st = self.state()
        ch = self.toned(e, st)
        normal = self.mode == "normal"
        big = ui.label(ch, "bhava-big")
        big.set_halign(Gtk.Align.CENTER)
        terms = [t for t in (self.panel.query().lower().split() if self.panel else []) if t]
        name = ui.label(self.marked((e["n"][:1].upper() + e["n"][1:]).split(), terms, " "), "p-title", markup=True,
                        wrap=True, justify=Gtk.Justification.CENTER, wrap_mode=Pango.WrapMode.WORD_CHAR)
        code = ui.label(shortcode(e), "bhava-code", wrap=True, wrap_mode=Pango.WrapMode.CHAR,
                        justify=Gtk.Justification.CENTER)
        cps = " ".join(f"U+{ord(c):04X}" for c in ch if ord(c) != 0xFE0F)
        where = ui.label(f"{e['g']} · {cps}", "p-meta", wrap=True, justify=Gtk.Justification.CENTER)
        parts = [big, name, code, where]
        if e.get("k"):
            words = list(dict.fromkeys(e["k"].split()))
            kw = ui.label("keywords: " + self.marked(words, terms, ", "), "bhava-keywords", markup=True, wrap=True,
                          wrap_mode=Pango.WrapMode.WORD_CHAR, justify=Gtk.Justification.CENTER)
            parts.append(kw)
        if e.get("t"):
            tones = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
            tones.add_css_class("bhava-tones")
            cur = self.tone_of(e, st)
            for i, t in enumerate([e["e"]] + e["t"]):
                b = Gtk.Button(label=t)
                b.add_css_class("bhava-tone")
                if i == cur:
                    b.add_css_class("on")
                b.set_can_focus(False)
                b.set_tooltip_text("Default" if i == 0 else f"Skin tone {i}")
                b.connect("clicked", lambda _b, i=i: self.set_tone(e, i))
                tones.append(b)
            parts.append(tones)
            parts.append(ui.label(f"{keycap_markup('t' if normal else 'Ctrl+T')} skin tone, kept for this emoji",
                                  "p-meta", markup=True, justify=Gtk.Justification.CENTER))
        btns = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        btns.append(ui.button("Type it", lambda: self.pick(e, False), "primary", key="Enter"))
        btns.append(ui.button("Copy", lambda: self.pick(e, True), key="y" if normal else "Ctrl+C"))
        parts.append(btns)
        box = ui.vbox(*parts, spacing=8)
        box.add_css_class("bhava-preview")
        for w in parts:
            w.set_halign(Gtk.Align.CENTER)
        return box

    @staticmethod
    def marked(words, terms, sep):
        """The words that match the search, in peach (what to look for) and bold."""
        out = []
        for w in words:
            esc = GLib.markup_escape_text(w)
            out.append(f"<span foreground='{PEACH}' weight='bold'>{esc}</span>"
                       if any(t in w.lower() for t in terms) else esc)
        return sep.join(out)

    # ------------------------------------------------------------ actions
    def pick(self, e, copy_only):
        st = self.state()
        ch = self.toned(e, st)
        st["recent"] = [e["e"]] + [c for c in st.get("recent", []) if c != e["e"]][:47]
        util.save_state(STATE, st)
        util.copy(ch)
        self.close()
        if not copy_only and util.have("wtype"):
            # After the panel closes, so the keystrokes reach the window you were in.
            subprocess.Popen(["sh", "-c", 'sleep 0.15; wtype "$1"', "sh", ch])

    def activate(self, row, mods):
        self.pick(row.data, "ctrl" in mods)
        return False

    def set_tone(self, e, i):
        st = self.state()
        st.setdefault("tones", {})[e["e"]] = i
        util.save_state(STATE, st)
        p = self.panel
        if p is None:
            return
        # Just this cell and the preview: a new search would lose your place.
        ch = self.toned(e, st)
        for row, w in p.items:
            if row.data is e:
                row.title = ch
                cell = w.get_child()
                if cell is not None:
                    cell.set_label(ch)
        p.update_preview()

    def cycle_tone(self, row):
        if row is None:
            return
        e = row.data
        if not e.get("t"):
            self.say("This emoji has no skin tones")
            return
        self.set_tone(e, (self.tone_of(e) + 1) % len(TONES))

    def say(self, text):
        self.set_status(text)
        self.our_status = True

    # ------------------------------------------------------------ moving
    def goto(self, i):
        p = self.panel
        if p.items:
            p.select(max(0, min(i, len(p.items) - 1)))

    def half_page(self):
        p = self.panel
        cols = self.grid_columns
        rows = 4
        if p.items:
            h = p.items[0][1].get_height()
            page = p.scroll.get_vadjustment().get_page_size()
            if h > 0 and page > 0:
                rows = max(1, int(page / (h + 6)) // 2)
        return rows * cols

    def normal_key(self, name, row, mods):
        p = self.panel
        cols = self.grid_columns
        n = len(p.items)
        s = max(p.sel, 0)
        ctrl = "ctrl" in mods
        if ctrl:
            if name in ("d", "u"):
                self.goto(s + (1 if name == "d" else -1) * self.half_page())
                return True
            return False            # Ctrl+1..9, Ctrl+J/K and the rest: the panel's
        if name in ("Tab", "ISO_Left_Tab", "Up", "Down", "Left", "Right", "Page_Up", "Page_Down", "F11"):
            self.count = self.pending = ""
            return False
        if name in ("Return", "KP_Enter"):
            self.count = self.pending = ""
            p.activate(p.sel, mods)
            return True
        if name == "Escape":
            if self.count or self.pending:
                self.count = self.pending = ""
                return True
            self.close()
            return True
        # A count: 1..9, then digits (0 alone is "start of row").
        if name.isdigit() and len(name) == 1 and (name != "0" or self.count):
            self.count = (self.count + name)[-3:]
            return True
        times = int(self.count or 1)
        had_count = bool(self.count)
        if self.pending == "g":
            self.count = self.pending = ""
            if name == "g":
                self.goto((times - 1) * cols if had_count else 0)
            return True
        self.count = ""
        col = s % cols
        if name == "h":
            self.goto(max(s - times, s - col))
        elif name == "l":
            self.goto(min(s + times, s - col + cols - 1, n - 1))
        elif name == "j":
            t = s + times * cols
            last_row_start = (n - 1) - (n - 1) % cols
            self.goto(t if t < n else (n - 1 if last_row_start > s - col else s))
        elif name == "k":
            self.goto(max(s - times * cols, col))
        elif name == "w":
            p.step_tab(delta=times)
        elif name == "b":
            p.step_tab(delta=-times)
        elif name == "g":
            self.pending = "g"
            self.count = str(times) if had_count else ""
        elif name == "G":
            self.goto((times - 1) * cols if had_count else n - 1)
        elif name == "0":
            self.goto(s - col)
        elif name == "dollar":
            self.goto(min(s - col + cols - 1, n - 1))
        elif name == "y":
            if row is not None:
                self.pick(row.data, True)
        elif name in ("t", "s"):
            self.cycle_tone(row)
        elif name in ("i", "a"):
            self.set_mode("insert")
        elif name == "slash":
            p.entry.set_text("")
            self.set_mode("insert")
        elif name == "q":
            self.close()
        # Anything else: nothing (letters don't type in NORMAL).
        return True

    def key(self, name, row, mods):
        if self.panel is None or self.dressed is not self.panel:
            return False
        if self.our_status:
            self.set_status("")
            self.our_status = False
        ctrl = "ctrl" in mods
        if ctrl and name == "t":
            self.cycle_tone(row)
            return True
        if ctrl and name == "c" and row is not None:
            self.pick(row.data, True)
            return True
        if self.mode == "insert":
            if name == "Escape":
                self.set_mode("normal")
                return True
            return False
        handled = self.normal_key(name, row, mods)
        self.show_pending()
        return handled
