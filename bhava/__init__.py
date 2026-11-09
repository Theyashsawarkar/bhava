"""bhava (भाव, "feeling"): the emoji picker for Vyom.

A grid of every Unicode 16 emoji (names and groups from Unicode,
keywords from wofi-emoji, MIT), your recent ones first, a rail of
categories on the left, a skin tone remembered per emoji, and a big
preview. Enter types it into the window you were in (wtype) and copies it.

Vim modes are Vyom's (ADR 0008): INSERT types into the search box; NORMAL
(Esc) moves around the grid with h/j/k/l and friends, letters don't type,
Space is the leader. bhava/vim.py is its keys. `[plugin.bhava] start_mode =
"normal"` opens in NORMAL.
"""
import json
import os
import subprocess

from gi.repository import GLib, Gtk, Pango

from vyom import Hint, Row, ui, util
from vyom import Plugin as Base
from vyom.panel import keycap_markup

from . import vim

# KEYBINDS (generated from bhava/vim.py by scripts/keybinds.py; don't edit by hand)
# keybind: Vyom/bhava:insert | Enter | Send the emoji to the window you were in (types it, and copies it)
# keybind: Vyom/bhava:insert | Ctrl+Enter | Copy the emoji only
# keybind: Vyom/bhava:insert | Ctrl+t | Cycle the skin tone of this emoji (remembered per emoji)
# keybind: Vyom/bhava:normal | h | Move left in the row (a count repeats: 3h)
# keybind: Vyom/bhava:normal | l | Move right in the row (a count repeats: 3l)
# keybind: Vyom/bhava:normal | j | Move down a row (a count repeats: 5j)
# keybind: Vyom/bhava:normal | k | Move up a row (a count repeats: 5k)
# keybind: Vyom/bhava:normal | 0 | Jump to the start of the row
# keybind: Vyom/bhava:normal | $ | Jump to the end of the row
# keybind: Vyom/bhava:normal | Enter | Send the emoji to the window you were in (types it, and copies it)
# keybind: Vyom/bhava:normal | y | Copy the emoji only (yank)
# keybind: Vyom/bhava:normal | t | Cycle the skin tone of this emoji (remembered per emoji)
# keybind: Vyom/bhava:normal | H / L | Switch to the previous / next category (w / b too)
# keybind: Vyom/bhava:normal | g g / G | Jump to the first / last emoji (5gg or 5G: row 5)
# keybind: Vyom/bhava leader:normal | Space t 1..9 | Switch to that category
# keybind: Vyom/bhava leader:normal | Space y y | Copy the emoji only
# keybind: Vyom/bhava leader:normal | Space y c | Copy the emoji's shortcode (:grinning_face:)
# keybind: Vyom/bhava leader:normal | Space d d | Remove the emoji from Recent
# END KEYBINDS


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


def shortcode(e):
    return ":" + "".join(c if c.isalnum() else "_" for c in e["n"].lower()).strip("_").replace("__", "_") + ":"


class Plugin(Base):
    name, title, icon, color = "bhava", "Emoji", "\U000f0785", "yellow"
    layout = "grid"
    grid_columns = 8
    preview = True
    preview_width = 260
    placeholder = "Search emoji…   e.g. wind, party, heart"
    hints = [Hint("hjkl", "move"), Hint("Enter", "type"), Hint("y", "copy"),
             Hint("t", "skin tone"), Hint("i", "search")]
    insert_hints = [Hint("Ctrl+J/K", "move"), Hint("Enter", "type"), Hint("Ctrl+Enter", "copy"),
                    Hint("Ctrl+T", "skin tone"), Hint("Esc", "normal mode")]
    modal = True        # Vyom's vim keys (ADR 0008); bhava/vim.py
    start_mode = "insert"
    key_groups = vim.GROUPS
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
        self.rail_buttons = {}
        self.found = None

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

    tabs_in_rail = True        # the rail shows the categories: no tab bar on top

    def build_rail(self):
        """The rail of categories on the left (Vyom's side-rail slot), once
        per panel."""
        p = self.panel
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
            b.set_tooltip_text(f"{name} (Space t {i + 1})" if i < 9 else f"{name} (H / L)")
            b.connect("clicked", lambda _b, k=key: self.select_tab(k))
            self.rail_buttons[key] = b
            rail.append(b)
        if p is not None and getattr(p, "grid", None) is not None:
            p.grid.set_column_spacing(6)
            p.grid.set_row_spacing(6)
        return side

    def mark_rail(self):
        for k, b in self.rail_buttons.items():
            (b.add_css_class if k == self.tab else b.remove_css_class)("on")

    # ------------------------------------------------------------ lifecycle
    def opened(self, args):
        super().opened(args)
        # Recent first if there are any, else everything.
        if self.tab in ("recent", "all"):
            self.select_tab("recent" if self.state().get("recent") else "all")
        self.mark_rail()

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
        normal = self.vim_mode() == "normal"
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

    def say(self, text, kind=None):
        # A passing note: it clears itself, so the footer's keys come back
        # (before Vyom's keys, the next key press cleared it).
        self.set_status(text, kind, clear_after=4)

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

    # ================================================================ keys
    # The modes, counts and sequences are Vyom's; bhava/vim.py is its keys.
    def keys(self, tab):
        return vim.keys(tab)

    def mode_changed(self, mode):
        if self.panel is not None:
            self.panel.update_preview()   # its key caps follow the mode

    def selected(self):
        return self.panel.selected_row() if self.panel else None

    def v_move(self, times, arg):
        """Grid moves that stay in their row (h / l) and stop at the edges."""
        p = self.panel
        cols = self.grid_columns
        n = len(p.items)
        if not n:
            return
        s = max(p.sel, 0)
        col = s % cols
        if arg == "h":
            self.goto(max(s - times, s - col))
        elif arg == "l":
            self.goto(min(s + times, s - col + cols - 1, n - 1))
        elif arg == "j":
            t = s + times * cols
            last_row_start = (n - 1) - (n - 1) % cols
            self.goto(t if t < n else (n - 1 if last_row_start > s - col else s))
        elif arg == "k":
            self.goto(max(s - times * cols, col))
        elif arg == "0":
            self.goto(s - col)
        elif arg == "$":
            self.goto(min(s - col + cols - 1, n - 1))

    def v_copy(self, _n, arg):
        row = self.selected()
        if row is None:
            return
        if arg == "code":
            util.copy(shortcode(row.data))
            self.say(f"copied {shortcode(row.data)}", kind="ok")
            return
        self.pick(row.data, True)

    def v_tone(self, _n, _a):
        self.cycle_tone(self.selected())

    def v_forget(self, _n, _a):
        row = self.selected()
        if row is None:
            return
        st = self.state()
        if row.data["e"] not in st.get("recent", []):
            self.say("That emoji isn't in Recent")
            return
        st["recent"] = [c for c in st["recent"] if c != row.data["e"]]
        util.save_state(STATE, st)
        self.say("Removed it from Recent")
        self.refresh()
