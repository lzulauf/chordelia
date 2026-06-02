# Rhythm and Timing

Back links: [Project README](../../README.md) | [Docs Index](../README.md)

## Durations, Time Signatures, and Tempo

```python
from chordelia import (
    Duration, TimeSignature, Tempo, Beat, NoteValue,
    quarter_note, dotted, triplet,
    COMMON_TIME, WALTZ_TIME, COMPOUND_DUPLE,
)

quarter = Duration(NoteValue.QUARTER)
dotted_quarter = dotted(quarter_note())
quarter_triplet = triplet(quarter_note())

print(quarter)          # quarter
print(dotted_quarter)   # dotted quarter
print(quarter_triplet)  # quarter triplet

four_four = COMMON_TIME
six_eight = COMPOUND_DUPLE
print(four_four.is_simple_time())
print(six_eight.is_compound_time())

tempo = Tempo(120)
print(f"Beat duration: {tempo.beat_duration_ms():.1f}ms")
```

## Beat Tracking

```python
from chordelia import Beat, COMMON_TIME, dotted, quarter_note

beat = Beat(0, 0, COMMON_TIME)
beat = beat.add_duration(dotted(quarter_note()))
print(beat)
```

## Real-Time Conversion

```python
from chordelia import Tempo, TimeSignature, quarter_note

tempo = Tempo(120)
time_sig = TimeSignature(4, 4)
quarter_ms = quarter_note().to_milliseconds(tempo.bpm, time_sig)
print(f"Quarter note at 120 BPM: {quarter_ms:.0f}ms")
```

## Practice Metronome Example

```python
from chordelia import Tempo
import time

def practice_metronome(bpm, beats_per_measure=4, num_measures=2):
    tempo = Tempo(bpm)
    beat_duration = tempo.beat_duration_ms() / 1000

    for measure in range(1, num_measures + 1):
        for beat in range(1, beats_per_measure + 1):
            click = "CLICK" if beat == 1 else "click"
            print(f"Measure {measure}, Beat {beat}: {click}")
            time.sleep(beat_duration)
```

## Next Steps

- Return to [Quickstart](../quickstart.md)
- Continue with [Sequences and Score](sequences-and-score.md)
- Review [Development Guide](../development.md)
