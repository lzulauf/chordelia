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
event = Chord("F#4").score_events_for_context(context)[0]
print(event.beat, event.duration)

# Helper conversion
note_score = score_from_sequenceable(Note("F#4"), time_signature=(3, 4))
print(note_score.events[0].beat, note_score.events[0].duration)
```

## Where to Go Next

- [Notes and Intervals](guides/notes-and-intervals.md)
- [Scales and Chords](guides/scales-and-chords.md)
- [Rhythm and Timing](guides/rhythm-and-timing.md)
- [Immutability](immutability.md)
