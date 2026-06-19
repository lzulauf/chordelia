"""Runtime MIDI monitor example for Chordelia.

This script demonstrates:
1. Creating a score for playback
2. Starting a MIDI monitor session with JSONL logging enabled
3. Playing the score and inspecting captured monitor events

Dependencies:
- chordelia[midi]
"""

from pathlib import Path


try:
    from chordelia import Chord, MidiMonitorSession, MidiPlayback, Score, Sequence
except ImportError as exc:
    raise SystemExit(f"MIDI monitor example requires chordelia[midi]: {exc}")


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


def main() -> None:
    score = build_score()
    log_file = Path("midi_monitor_runtime.jsonl")

    with MidiPlayback() as playback:
        monitor = MidiMonitorSession(
            playback=playback,
            max_events=2000,
            tempo_bpm=score.metadata.tempo,
            log_file=log_file,
            include_wall_time=True,
            include_elapsed_seconds=True,
            include_elapsed_beats=True,
        ).start()

        playback.play_score(score, blocking=True)

        latest = monitor.snapshot(limit=12)
        print(f"Captured {len(monitor.events)} total events")
        print("Most recent events:")
        for event in latest:
            print(
                f"#{event.event_index} {event.message_type} "
                f"ch={event.channel} note={event.note} vel={event.velocity} "
                f"elapsed={event.elapsed_seconds_from_session_start}"
            )

        monitor.stop()

    print(f"JSONL monitor log: {log_file}")


if __name__ == "__main__":
    main()
