# bhava

**bhava** (भाव, "feeling, emotion") — The emoji picker. A tool for [Vyom](https://github.com/Theyashsawarkar/vyom), the keyboard-driven panels of [Vayu](https://github.com/Theyashsawarkar/vayu); in Vayu it replaces wofi-emoji.

> Emoji picker: a grid with recents first, categories, skin tones, a big preview; types the emoji into the window you were in.

## Features

- Every Unicode 16 emoji in a **grid**, your recent ones first.
- A tab per category, and **one skin-tone setting** (`Ctrl+T`) applied to every emoji that has tones.
- A big preview with the name, shortcode, code points and keywords.
- `Enter` **types the emoji into the window you were in** (and copies it); `Ctrl+Enter` only copies.
- Names and groups from Unicode's emoji-test.txt, keywords from wofi-emoji (MIT): see NOTICE and tools/build-data.py.

## Keys

| Key | Action |
|---|---|
| `Arrows` | Move around the emoji grid |
| `Enter` | Type the emoji into the window you were in (and copy it) |
| `Ctrl+Enter` | Copy the emoji only |
| `Ctrl+T` | Change the skin tone |
| `Ctrl+0..9` | Show recent, all, or one category |
| `Esc` | close |

Every Vyom panel also has: `Up`/`Down` (or `Ctrl+K`/`Ctrl+J`) to move, `Page Up`/`Page Down`, `Tab` to switch to the next tool.

## Requirements

- [Vyom](https://github.com/Theyashsawarkar/vyom) 0.2 or newer (Python 3.11+, GTK 4, gtk4-layer-shell, a layer-shell compositor)
- optional: wtype (typing the emoji)

## Install

```sh
git clone https://github.com/Theyashsawarkar/bhava ~/.local/share/vyom/plugins/bhava
vyom reload        # or log out and in
vyom bhava         # open it (again: close it)
```

Bind it to a key, e.g. in sway:

```
bindsym $mod+<key> exec vyom bhava
```

Update: `git -C ~/.local/share/vyom/plugins/bhava pull && vyom reload`. `vyom list` shows every installed tool and why one would be skipped.

## License

MIT. See NOTICE for the emoji data.
