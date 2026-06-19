# Tutorial: Sheet Music Rendering

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

This tutorial covers notation workflows from quick SVG output to LilyPond-backed
rendering and notebook integration.

## 1) Render SVG with Built-In Backend

```python
from chordelia import Note, Sequence, SheetMusic

phrase = Sequence(((Note("C4"), 1), (Note("D4"), 1), (Note("E4"), 2)))
sheet = SheetMusic(phrase, scale="C")
sheet.to_file("phrase.svg")
```

Notes:

- Input can be any `Sequenceable` value or an existing `Score`.
- Clef defaults to `"auto"` and resolves from the median of unique pitches: below middle C (MIDI 60) chooses bass; middle C or above chooses treble.
- In notebooks, evaluating `sheet` displays SVG inline.

Explicit clef examples:

```python
from chordelia import Note, Sequence, SheetMusic

bass_line = Sequence(((Note("E2"), 1), (Note("A2"), 1), (Note("B2"), 2)))
SheetMusic(bass_line, clef="bass").to_file("bass_phrase.svg")
SheetMusic(bass_line, clef="auto").to_file("auto_phrase.svg")
```

## 2) Use LilyPond as the Rendering Backend

```python
from chordelia.sheetmusic_runtime import configure_sheetmusic_rendering

configure_sheetmusic_rendering(
    backend_name="lilypond",
    lilypond_executable="C:/path/to/lilypond.exe",
    crop=True,
    background="white",
)
```

After configuration, `SheetMusic(...).to_file(..., format="svg")` routes through LilyPond.
Set `background="transparent"` to keep the LilyPond SVG background transparent.

## 3) Enable Notebook Hooks for Sequenceable Values

```python
from chordelia.sheetmusic_runtime import configure_sheetmusic_rendering

configure_sheetmusic_rendering(
    backend_name="lilypond",
    lilypond_executable="C:/path/to/lilypond.exe",
    scale="D",
    clef="auto",
    enable_notebook_hooks=True,
)
```

Now evaluating `Note`, `Chord`, `Sequence`, or `Rest` in a notebook can render as sheet music.
The `clef` setting in `configure_sheetmusic_rendering(...)` is applied globally to those
hook-driven renders (`"treble"`, `"bass"`, or `"auto"`, default `"auto"`).

To update only scale later:

```python
from chordelia.sheetmusic_runtime import configure_sheetmusic_rendering
configure_sheetmusic_rendering(scale="Eb")
```

## 4) Temporary Rendering Overrides

```python
from chordelia.sheetmusic_runtime import with_sheetmusic_rendering
from chordelia import SheetMusic

with with_sheetmusic_rendering(backend_name="builtin_svg", scale="C"):
    SheetMusic(phrase).to_file("phrase_builtin.svg")
```

## Related

- [Quickstart](../quickstart.md)
- [API Overview](../api-overview.md#sheet-music-and-rendering)
- [Song Form from a Motif](song-form-from-motif.md)
