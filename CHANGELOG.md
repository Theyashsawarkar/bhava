# Changelog

Newest first. Releases are tags (`vX.Y.Z`).

## v0.3.0 -- 2026-11-07

- Vim modes. It opens in INSERT, where typing searches as before. `Esc` goes to NORMAL:
  `h` `j` `k` `l` move in the grid, with a count (`5j`, `3l`); `w` / `b` change category;
  `gg` / `G` first / last; `0` / `$` start / end of the row; `Ctrl+D` / `Ctrl+U` half a page;
  `Enter` types, `y` copies, `t` or `s` changes the skin tone; `i`, `a` or `/` (a new search)
  go back to INSERT; `q` or `Esc` closes, so `Esc` twice closes. A pill in the footer says
  NORMAL (accent) or INSERT (green), with a half-typed count or `g` beside it, and the search
  box goes quiet in NORMAL. `[plugin.bhava] start_mode = "normal"` opens in NORMAL.
- A new look: bigger emoji on a calmer grid, the selected one framed in the accent colour; the
  categories in a rail on the left with their names and numbers; a "found" count while you search.
- The skin tone is now remembered per emoji, chosen with a visible picker in the preview
  (`Ctrl+T` cycles it). Your old single setting is the starting tone for the rest.
- The preview shows the name, the `:shortcode:` and the keywords, the words your search matched in
  peach, and "Type it" (`Enter`) and "Copy" buttons with their keys.
- `Ctrl+C` copies the emoji (`Ctrl+Enter` still does).
- Choosing a category while searching clears the search, so the category shows.
- Needs Vyom 0.6.0.
- Every corner is rounded: the website's callouts.
- A logo and a shloka at the top of the README and the website: every Vayu tool has them now.

## v0.2.0 -- 2026-10-24

- Category tabs switch like every Vyom tool's tabs (Vyom 0.3.0): `Ctrl+H` / `Ctrl+L`
  for the previous / next category, `Ctrl+1..9` and `Ctrl+0` by number. The numbers
  moved by one: `Ctrl+1` is Recent, `Ctrl+2` All, `Ctrl+0` Symbols (was `Ctrl+0` Recent);
  Flags is `Ctrl+H` from Recent. Needs Vyom 0.3.0.

## v0.1.4 -- 2026-10-21

- A website (GitHub Pages, https://theyashsawarkar.github.io/bhava/): the README as a home page, the
  changelog, and architecture decision records (`docs/adr/`), built from these files by
  `scripts/build-site.py`; CI checks the site is up to date.

## v0.1.3 -- 2026-10-21

- Documentation for open source: a logo and banner, a full README (features,
  install, usage, configuration, troubleshooting, the whole Vyom family),
  CONTRIBUTING, SECURITY and CODE_OF_CONDUCT, issue and pull request
  templates, and CI (compiles, checks plugin.toml and that every key is
  documented).

## v0.1.2 -- 2026-10-19

- Opens at Vyom's shared panel size (Vyom 0.2.5) like every other tool:
  its own width/height are gone.

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
