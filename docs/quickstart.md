# Quickstart

Back links: [Project README](../README.md) | [Docs Index](README.md)

This guide gives a fast end-to-end walkthrough of the core API.

## Notes and Intervals

```python
from chordelia import Note, Interval, IntervalQuality

c4 = Note("C4")
g4 = c4.transpose(Interval(IntervalQuality.PERFECT, 5))
print(c4, g4)  # C4 G4
print(c4.interval_to(g4))  # P5
```

## Scales

```python
from chordelia import Scale, ScaleType

c_major = Scale("C", ScaleType.MAJOR)
print([str(note) for note in c_major.notes])
# ['C', 'D', 'E', 'F', 'G', 'A', 'B']

ii = c_major.chord_for_degree("ii")
v = c_major.chord_for_degree("V")
i = c_major.chord_for_degree("I")
print([ii.name, v.name, i.name])  # ['Dm', 'G', 'C']
```

## Chords

```python
from chordelia import Chord

c_major = Chord("C")
c_maj7 = c_major.with_extension("maj7")
first_inversion = c_maj7.with_inversion(1)

print(c_major.name)       # C
print(c_maj7.name)        # Cmaj7
print(first_inversion.name)

print(c_maj7.tone_at("III"))          # G
print(c_maj7.degree_for_tone(c_maj7.tone_at(2)))  # 2
```

## Rhythm and Timing

```python
from chordelia import Tempo, TimeSignature, quarter_note

tempo = Tempo(120)
time_sig = TimeSignature(4, 4)
quarter_ms = quarter_note().to_milliseconds(tempo.bpm, time_sig)
print(f"Quarter note length: {quarter_ms:.0f}ms")
```

## Score Conversion

```python
from chordelia import Chord, Note, Score, ScoreEventContext, Duration, score_from_sequenceable

# Classmethod conversion
chord_score = Score.from_sequenceable(Chord("C4"), tempo=100)
print(chord_score.events[0].pitches)  # (60, 64, 67)

# Event-context timing uses Duration values
context = ScoreEventContext(
	start_offset=Duration.from_beats(1, 2),
	default_duration=Duration.from_beats(1),
)
event = Chord("F#4").render_for_context(context).events[0]
print(event.beat, event.duration)

# Helper conversion
note_score = score_from_sequenceable(Note("F#4"), time_signature=(3, 4))
print(note_score.events[0].beat, note_score.events[0].duration)
```

## Sequence Timelines

```python
from chordelia import Chord, Sequence, ScoreEventContext

# Iterable note strings are treated as one chord layer.
single_layer = Sequence(((["C4", "E4", "G4"], 1),))
single_events = single_layer.render_for_context(ScoreEventContext()).events
print(len(single_events), single_events[0].pitches)  # 1, (60, 64, 67)

# Iterable chord-like values preserve simultaneous boundaries.
stacked_layers = Sequence((([
	Chord.from_notes(["C4", "E4"]),
	Chord.from_notes(["G4", "B4"]),
], 1),))
stacked_events = stacked_layers.render_for_context(ScoreEventContext()).events
print(len(stacked_events))  # 2
print([event.pitches for event in stacked_events])  # [(60, 64), (67, 71)]

# Child sequences in constructor input behave like any Sequenceable payload.
motif = Sequence(((Chord("Am4"), 1), (Chord("Dm4"), 1)))
arrangement = Sequence([motif] * 2)
print(len(arrangement.entries))  # 2
```

## Sheet Music Rendering

```python
from chordelia import Note, Sequence, SheetMusic

phrase = Sequence(((Note("C4"), 1), (Note("D4"), 1), (Note("E4"), 2)))

# The optional scale context drives key-signature and accidental rendering.
sheet = SheetMusic(phrase, scale="C")
sheet.to_file("phrase.svg")

# In notebooks, evaluate `sheet` to render inline SVG.
```

`SheetMusic` is write-only in v1: use `to_file(...)` and notebook display, but no parse/load API.

To route all `SheetMusic` SVG rendering through LilyPond, configure the backend once:

```python
from chordelia.sheetmusic_backends import configure_sheet_music_lilypond_backend

configure_sheet_music_lilypond_backend("C:/Users/you/Desktop/lilypond-2.24.4/bin/lilypond.exe")

# Crop to the rendered music bounds (default behavior).
# To keep full-page output instead, pass crop=False.
# configure_sheet_music_lilypond_backend(".../lilypond.exe", crop=False)
```

## MIDI Interface Playback (Optional)

```python
from chordelia import Chord, MidiFile, MidiPlayback, Score, Sequence

progression = Sequence((
	(Chord("C4"), 1),
	(Chord("A4", "minor"), 1),
	(Chord("F4"), 1),
	(Chord("G4"), 1),
))

score = Score.from_sequenceable(progression, tempo=104)
midi = MidiFile(score)
midi.to_file("progression.mid")

# Play score through a MIDI output interface.
# with MidiPlayback(output_name=None) as playback:
#     playback.play_score(score, blocking=True)

# Articulation defaults are gate_width=0.9 and retrigger_policy="retrigger_all".
# To force full-duration playback while keeping delta retrigger behavior:
score = score.with_(gate_width=1.0, retrigger_policy="delta")

# Equivalent playback-call override:
with MidiPlayback(output_name=None) as playback:
    playback.play_score(
        score,
        blocking=True,
        gate_width=1.0,
        retrigger_policy="delta",
    )
```

Requires MIDI extras:

```bash
pip install chordelia[midi]
```

## Where to Go Next

- [Notes and Intervals](guides/notes-and-intervals.md)
- [Scales and Chords](guides/scales-and-chords.md)
- [Rhythm and Timing](guides/rhythm-and-timing.md)
- [Immutability](immutability.md)
- [API Overview](api-overview.md)
