# 4. Vim modes and a category rail, inside the plugin

**Status:** Accepted  
**Date:** 2026-11-07

## Context

The user wanted to move around the emoji grid with `h` `j` `k` `l` and the rest of vim's motions, without losing type-to-search. The approved redesign also puts the categories in a rail on the left, with names, and a mode pill in the footer. Vyom core (0.6.0) has neither modes nor a left rail, and other tools must not change because bhava wants them.

## Decision

- Two modes, INSERT and NORMAL, live in bhava's `Plugin.key()` hook, which sees every key before the search box. INSERT passes keys on (they type); NORMAL handles them all, so letters never type. `Esc` goes INSERT to NORMAL, and closes from NORMAL. Counts and `g` are kept in the plugin and shown beside the pill.
- It opens in INSERT (you usually came to type a word); `[plugin.bhava] start_mode = "normal"` opens in NORMAL.
- The categories stay the panel's tabs (so `Tab` and `Ctrl+1..9` work as in every tool), but the top-bar tabs are hidden and a rail with names is added to the left of the grid; the mode pill and per-mode hints are added to the footer. bhava finds these places through the panel's widgets (`strip_holder`, `status`) once per panel.
- A skin tone is remembered per emoji (`tones` in the state file); the old single setting is the default for emoji never changed.

## Consequences

- No core change; other tools are untouched.
- bhava depends on the panel's widget layout (Vyom 0.6.0). If core grows a left-rail slot, a footer slot or modes of its own, bhava should move to them.
