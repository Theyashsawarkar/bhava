"""bhava's vim keys, as data. The modes, counts, sequences, which-key strip,
help (?) and palette (Space Space) are Vyom's (vyom/keys.py, vyom/modal.py;
Vyom ADR 0008); this file is only what bhava adds: grid moves that stay in
their row, categories, skin tones, copy. Space groups follow Vayu's shared
letters: t tabs (Vyom's: Space t 1..9 for the categories), y copy, d delete,
u toggles.

An action "verb:arg" runs Plugin.v_<verb>(count, arg) in bhava/__init__.py,
or Vyom's own (tab, activate, insert...).
"""
from vyom.keys import Bind

B = Bind

GROUPS = {}

INSERT = [
    ("Enter", "Send the emoji to the window you were in (types it, and copies it)"),
    ("Ctrl+Enter", "Copy the emoji only"),
    B("<C-t>", "tone", "Cycle the skin tone of this emoji (remembered per emoji)", mode="insert"),
]

NORMAL = [
    B("h", "move:h", "Move left in the row (a count repeats: 3h)"),
    B("l", "move:l", "Move right in the row (a count repeats: 3l)"),
    B("j", "move:j", "Move down a row (a count repeats: 5j)"),
    B("k", "move:k", "Move up a row (a count repeats: 5k)"),
    B("0", "move:0", "Jump to the start of the row"),
    B("$", "move:$", "Jump to the end of the row"),
    B("w", "tab:+1", "", hidden=True), B("b", "tab:-1", "", hidden=True),   # bhava's old category keys
    B("<CR>", "activate", "Send the emoji to the window you were in (types it, and copies it)"),
    B("y", "copy", "Copy the emoji only (yank)"),
    B("t", "tone", "Cycle the skin tone of this emoji (remembered per emoji)"),
    B("s", "tone", "", hidden=True), B("<C-t>", "tone", "", hidden=True),
    B("<C-c>", "copy", "", hidden=True),
]

LEADER = [
    B(" yy", "copy", "Copy the emoji only"),
    B(" yc", "copy:code", "Copy the emoji's shortcode (:grinning_face:)"),
    B(" dd", "forget", "Remove the emoji from Recent"),
]


def keys(tab):
    return [b for b in INSERT if isinstance(b, Bind)] + NORMAL + LEADER


SECTIONS = [
    ("bhava", "insert", "Insert mode (typing; bhava opens in it)", INSERT),
    ("bhava", "normal", "Normal mode", NORMAL + [("H / L", "Switch to the previous / next category (w / b too)"),
                                                 ("g g / G", "Jump to the first / last emoji (5gg or 5G: row 5)")]),
    ("bhava leader", "normal", "Leader (Space)", [("Space t 1..9", "Switch to that category")] + LEADER),
]
