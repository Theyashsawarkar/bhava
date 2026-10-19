"""bhava (भाव, "feeling"): the emoji picker for Vyom.

A grid of every Unicode 16 emoji (names and groups from Unicode,
keywords from wofi-emoji, MIT), your recent ones first, a tab per
category, one skin-tone setting for every emoji that has tones, and a big
preview. Enter types it into the window you were in (wtype) and copies it.
"""
import json
import os
import subprocess

from gi.repository import Gtk

from vyom import Hint, Row, ui, util
from vyom import Plugin as Base

# keybind: Vyom/emoji | Arrows | Move around the emoji grid
# keybind: Vyom/emoji | Enter | Type the emoji into the window you were in (and copy it)
# keybind: Vyom/emoji | Ctrl+Enter | Copy the emoji only
# keybind: Vyom/emoji | Ctrl+T | Change the skin tone
# keybind: Vyom/emoji | Ctrl+0..9 | Show recent, all, or one category

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = "bhava"
TONES = ["", "🏻", "🏼", "🏽", "🏾", "🏿"]
TONE_HANDS = ["✋", "✋🏻", "✋🏼", "✋🏽", "✋🏾", "✋🏿"]
GROUPS = [("recent", "🕘"), ("all", "✱"), ("Smileys & Emotion", "😀"), ("People & Body", "👋"),
          ("Animals & Nature", "🐶"), ("Food & Drink", "🍕"), ("Activities", "⚽"), ("Travel & Places", "✈️"),
          ("Objects", "💡"), ("Symbols", "🔣"), ("Flags", "🏳️")]


class Plugin(Base):
    name, title, icon, color = "bhava", "Emoji", "\U000f0785", "yellow"
    layout = "grid"
    grid_columns = 9
    width = 780
    height = 500
    preview = True
    preview_width = 240
    placeholder = "Search emoji…   e.g. wind, party, heart"
    hints = [Hint("Enter", "type it"), Hint("Ctrl+Enter", "copy"), Hint("Ctrl+T", "skin tone")]
    empty_text = "No emoji for that"

    def __init__(self, vyom, conf):
        super().__init__(vyom, conf)
        with open(os.path.join(HERE, "emoji.json"), encoding="utf-8") as f:
            self.emoji = json.load(f)
        self.by_char = {e["e"]: e for e in self.emoji}
        self.group = "recent"
        self.tab_buttons = {}
        self.tone_label = None

    def state(self):
        return util.load_state(STATE, {"recent": [], "tone": 0})

    def header_extra(self):
        box = Gtk.Box(spacing=2)
        group = None
        for key, glyph in GROUPS:
            b = Gtk.ToggleButton(label=glyph)
            b.add_css_class("cat")
            b.set_tooltip_text("Recent" if key == "recent" else "All" if key == "all" else key)
            b.set_can_focus(False)
            if group is None:
                group = b
                b.set_active(True)
            else:
                b.set_group(group)
            b.connect("toggled", lambda btn, k=key: btn.get_active() and self.set_group(k))
            self.tab_buttons[key] = b
            box.append(b)
        self.tone_label = Gtk.Button(label=TONE_HANDS[self.state().get("tone", 0)])
        self.tone_label.add_css_class("cat")
        self.tone_label.set_tooltip_text("Skin tone (Ctrl+T)")
        self.tone_label.set_can_focus(False)
        self.tone_label.connect("clicked", lambda *_: self.cycle_tone())
        box.append(self.tone_label)
        return box

    def set_group(self, key):
        self.group = key
        self.refresh()

    def opened(self, args):
        super().opened(args)
        # Recent first if there are any, else everything.
        has_recent = bool(self.state().get("recent"))
        key = "recent" if has_recent else "all"
        if self.tab_buttons and self.group in ("recent", "all"):
            self.tab_buttons[key].set_active(True)
            self.group = key

    def toned(self, e):
        tone = self.state().get("tone", 0)
        return e["t"][tone - 1] if tone and e.get("t") and e["t"][tone - 1] else e["e"]

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
        elif self.group == "recent":
            items = [self.by_char[c] for c in st.get("recent", []) if c in self.by_char] or self.emoji
        elif self.group == "all":
            items = self.emoji
        else:
            items = [e for e in self.emoji if e["g"] == self.group]
        return [Row(self.toned(e), e["n"], data=e) for e in items[:400]]

    def build_preview(self, row):
        e = row.data
        ch = self.toned(e)
        big = ui.label(ch, "bhava-big")
        cps = " ".join(f"U+{ord(c):04X}" for c in ch if ord(c) not in (0xFE0F,))
        parts = [big, ui.title(e["n"]), ui.meta(f":{e['n'].replace(' ', '_').replace(':', '')}:"),
                 ui.kv([("Group", e["g"]), ("Code", cps)])]
        if e.get("k"):
            parts.append(ui.body(e["k"]))
        parts.append(ui.buttons([("Type it", lambda: self.pick(e, False), "primary"),
                                 ("Copy", lambda: self.pick(e, True))]))
        box = ui.vbox(*parts, spacing=10)
        big.set_halign(Gtk.Align.CENTER)
        return box

    def pick(self, e, copy_only):
        ch = self.toned(e)
        st = self.state()
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

    def cycle_tone(self):
        st = self.state()
        st["tone"] = (st.get("tone", 0) + 1) % len(TONES)
        util.save_state(STATE, st)
        if self.tone_label:
            self.tone_label.set_label(TONE_HANDS[st["tone"]])
        self.refresh()

    def key(self, name, row, mods):
        if "ctrl" in mods and name == "t":
            self.cycle_tone()
            return True
        if "ctrl" in mods and len(name) == 1 and name.isdigit():
            i = int(name)
            if i < len(GROUPS):
                self.tab_buttons[GROUPS[i][0]].set_active(True)
            return True
        return False
