# Changelog

Newest first. Releases are tags (`vX.Y.Z`).

## v0.1.1 -- 2026-10-19

- Keys are spelled out (Ctrl+Enter, Shift+Enter, Backspace) instead of symbols
  (⌃↵, ⇧↵, ⌫) in the footer and on rows and buttons.

## v0.1.0 -- 2026-10-19

- First release, as its own repository: the emoji picker. Replaces wofi-emoji in Vayu.
- Every Unicode 16 emoji in a **grid**, your recent ones first.
- A tab per category, and **one skin-tone setting** (`Ctrl+T`) applied to every emoji that has tones.
- A big preview with the name, shortcode, code points and keywords.
- `Enter` **types the emoji into the window you were in** (and copies it); `Ctrl+Enter` only copies.
- Names and groups from Unicode's emoji-test.txt, keywords from wofi-emoji (MIT): see NOTICE and tools/build-data.py.
