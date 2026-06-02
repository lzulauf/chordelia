"""Build a musical song form from one shifted melody segment.

This example demonstrates a practical songwriting workflow:
1. Write a short motif once.
2. Use diatonic shift to derive related phrases.
3. Assemble those phrases into a full song form.
"""

import argparse
from fractions import Fraction

from chordelia import Note, Score, Sequence, with_global_scale_context


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create an AABA song from a shifted melody motif and optionally play it."
        )
    )
    playback_group = parser.add_mutually_exclusive_group()
    playback_group.add_argument(
        "--audio",
        action="store_true",
        help="Play the generated song through the audio backend.",
    )
    playback_group.add_argument(
        "--midi-port",
        type=str,
        metavar="PORT_NAME",
        help="Play the generated song to the specified MIDI output port.",
    )
    parser.add_argument(
        "--list-midi-ports",
        action="store_true",
        help="List MIDI output ports and exit.",
    )
    args = parser.parse_args()

    if args.list_midi_ports:
        try:
            from chordelia import get_midi_ports
        except ImportError:
            print("MIDI playback is unavailable. Install with: pip install chordelia[midi]")
            return

        ports = get_midi_ports().get("output", [])
        if not ports:
            print("No MIDI output ports were detected.")
            return

        print("Available MIDI output ports:")
        for index, port_name in enumerate(ports, start=1):
            print(f"  {index}. {port_name}")
        return

    half_beat = Fraction(1, 2)
    motif = Sequence(
        (
            (Note("E4"), half_beat),
            (Note("G4"), half_beat),
            (Note("A4"), half_beat),
            (Note("G4"), half_beat),
            (Note("E4"), half_beat),
            (Note("D4"), half_beat),
            (Note("E4"), half_beat),
            (Note("G4"), half_beat),
        )
    )

    with with_global_scale_context("C"):
        phrase_a = motif
        phrase_a_answer = motif.shift(2)
        phrase_b = motif.shift(4)
        turnaround = motif.shift(-1)

    verse = phrase_a.appended(*phrase_a_answer.entries)
    bridge = phrase_b.appended(*turnaround.entries)
    song = verse.appended(*verse.entries, *bridge.entries, *verse.entries)

    print("=== Shifted Melody Song Example ===")
    print("Global scale context: C major")
    print()
    print("Section melodies:")
    print("A:         ", " ".join(str(entry.payload) for entry in phrase_a.entries))
    print(
        "A answer:  ",
        " ".join(str(entry.payload) for entry in phrase_a_answer.entries),
    )
    print("B:         ", " ".join(str(entry.payload) for entry in phrase_b.entries))
    print(
        "Turnaround:",
        " ".join(str(entry.payload) for entry in turnaround.entries),
    )
    print()

    score = Score.from_sequenceable(song, tempo=120, time_signature=(4, 4), key_signature="C")
    print("Song form: A A B A")
    print("Total events:", len(score.events))
    print("Total duration:", score.duration)
    print()
    print("First 12 melody events:")
    for event in score.events[:12]:
        spelling = event.spelling[0] if event.spelling else event.pitches[0]
        print(f"{event.beat} -> {spelling}")

    if args.audio:
        try:
            from chordelia import Playback, Tempo, score_to_playback_notes
        except ImportError:
            print("Audio playback is unavailable. Install with: pip install chordelia[audio]")
            return

        playback_notes = score_to_playback_notes(score)
        print("\nPlaying song via audio backend...")
        with Playback(Tempo(score.metadata.tempo)) as player:
            player.play_sequence(playback_notes, blocking=True)
    elif args.midi_port:
        try:
            from chordelia import MidiPlayback, get_midi_ports
        except ImportError:
            print("MIDI playback is unavailable. Install with: pip install chordelia[midi]")
            return

        available_ports = get_midi_ports().get("output", [])
        if args.midi_port not in available_ports:
            print(f"MIDI output port not found: {args.midi_port!r}")
            if available_ports:
                print("Available ports:")
                for available in available_ports:
                    print(f"  - {available}")
            else:
                print("No MIDI output ports were detected.")
            return

        print(f"\nPlaying song via MIDI output: {args.midi_port}")
        with MidiPlayback(output_name=args.midi_port) as playback:
            playback.play_score(score, blocking=True)
    else:
        print("\nPlayback options:")
        print("  python examples/shifted_melody_song_example.py --audio")
        print("  python examples/shifted_melody_song_example.py --list-midi-ports")
        print("  python examples/shifted_melody_song_example.py --midi-port \"Your MIDI Port\"")


if __name__ == "__main__":
    main()
