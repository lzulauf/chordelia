"""Notebook-oriented MIDI monitor example for Chordelia.

Run these snippets in notebook cells to keep a live MIDI monitor view active while
executing playback in later cells.

Dependencies:
- chordelia[midi]
- IPython (for rich live display mode)
"""

from chordelia import Chord, MidiMonitorSession, MidiPlayback, Score, Sequence


def build_score() -> Score:
    progression = Sequence(
        (
            (Chord("C4"), 1),
            (Chord("A4", "minor"), 1),
            (Chord("F4"), 1),
            (Chord("G4"), 1),
        )
    )
    return Score.from_sequenceable(progression, tempo=104, time_signature=(4, 4), key_signature="C")


# Cell 1: create score and playback once.
score = build_score()
playback = MidiPlayback()


# Cell 2: start monitor and open live display.
monitor_context = MidiMonitorSession(
    playback=playback,
    max_events=3000,
    tempo_bpm=score.metadata.tempo,
    include_elapsed_beats=True,
)
monitor = monitor_context.start()
live_handle = monitor.display_live(refresh_hz=8.0, max_rows=30)


# Cell 3: run playback as many times as needed.
playback.play_score(score, blocking=True)


# Cell 4: inspect snapshots in later cells.
recent_events = monitor.snapshot(limit=20)
recent_rows = monitor.to_rows(limit=20)


# Cell 5: cleanup.
live_handle.stop()
monitor.stop()
playback.stop()
