"""Canonical MIDI interface playback examples for Chordelia.

This script demonstrates:
1. Loading/analyzing a MIDI file with MidiFile
2. Playing a file to a MIDI output interface with MidiFile.play_to_interface
3. Playing an in-memory score to a MIDI output interface with MidiPlayback

Dependencies:
- mido
"""

import os
import sys
from pathlib import Path
from typing import Optional


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


try:
    from chordelia import Chord, MidiFile, MidiPlayback, Score, Sequence
    from chordelia.midi_playback import get_midi_ports

    MIDI_AVAILABLE = True
except ImportError as exc:
    MIDI_AVAILABLE = False
    IMPORT_ERROR = exc


def safe_input(prompt: str, default: str = "") -> str:
    """Read input and return default if stdin is unavailable."""
    try:
        return input(prompt)
    except EOFError:
        return default


def create_sample_midi(sample_path: Path) -> Optional[Path]:
    """Create a simple single-track MIDI file for local demo use."""
    try:
        import mido
    except ImportError:
        print("Could not import mido to create sample MIDI file.")
        return None

    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))

    for note in [60, 62, 64, 65, 67, 69, 71, 72]:
        track.append(mido.Message("note_on", channel=0, note=note, velocity=80, time=0))
        track.append(mido.Message("note_off", channel=0, note=note, velocity=0, time=480))

    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(str(sample_path))
    print(f"Created sample MIDI file: {sample_path}")
    return sample_path


def choose_output_port(non_interactive: bool) -> Optional[str]:
    """Select a MIDI output port name or None to use the transport default."""
    ports = get_midi_ports().get("output", [])

    if not ports:
        print("No MIDI output ports were detected on this machine.")
        return None

    print("Available MIDI output ports:")
    for idx, name in enumerate(ports, start=1):
        print(f"  {idx}. {name}")

    if non_interactive:
        print("Non-interactive mode: using the first available output port.")
        return ports[0]

    choice = safe_input("Select output port number (Enter for default): ").strip()
    if not choice:
        return None

    if not choice.isdigit():
        print("Invalid choice; using transport default output.")
        return None

    selected = int(choice) - 1
    if 0 <= selected < len(ports):
        return ports[selected]

    print("Choice out of range; using transport default output.")
    return None


def analyze_midi_file(filepath: Path) -> Optional[MidiFile]:
    """Load and print metadata for a MIDI file."""
    try:
        midi = MidiFile.load_from_file(filepath)
    except Exception as exc:
        print(f"Failed to load MIDI file {filepath}: {exc}")
        return None

    print(f"\nAnalyzing: {filepath}")
    print("=" * 50)
    midi.print_info()
    return midi


def play_file_to_interface(filepath: Path, output_name: Optional[str]) -> None:
    """Play an on-disk MIDI file to a MIDI output interface."""
    midi = MidiFile.load_from_file(filepath)
    midi.play_to_interface(output_name=output_name, blocking=True)


def play_generated_score_to_interface(output_name: Optional[str]) -> None:
    """Play an in-memory score directly through MidiPlayback."""
    score = Score.from_sequenceable(
        Sequence(
            (
                (Chord("C4"), 1),
                (Chord("A4", "minor"), 1),
                (Chord("F4"), 1),
                (Chord("G4"), 1),
            )
        ),
        tempo=104,
    )

    with MidiPlayback(output_name=output_name) as playback:
        playback.play_score(score, blocking=True)


def find_candidate_midi_files() -> list[Path]:
    """Return discovered MIDI files from project root and examples directory."""
    root = Path(".")
    examples = Path("examples")
    candidates = list(root.glob("*.mid")) + list(root.glob("*.midi"))
    candidates += list(examples.glob("*.mid")) + list(examples.glob("*.midi"))
    return sorted(set(candidates))


def main() -> None:
    """Run an interactive MIDI interface playback demo."""
    print("Chordelia MIDI Interface Playback Example")
    print("=" * 42)

    if not MIDI_AVAILABLE:
        print(f"MIDI module unavailable: {IMPORT_ERROR}")
        print("Install dependencies with: pip install chordelia[midi]")
        return

    non_interactive = (
        not sys.stdin.isatty()
        or not sys.stdout.isatty()
        or os.environ.get("CHORDELIA_NONINTERACTIVE") == "1"
    )

    output_name = choose_output_port(non_interactive)
    if output_name is None and not get_midi_ports().get("output"):
        return

    created_sample = False
    midi_file: Optional[Path] = None
    available_files = find_candidate_midi_files()

    if available_files:
        print("\nDetected MIDI files:")
        for idx, path in enumerate(available_files[:8], start=1):
            print(f"  {idx}. {path}")

        if non_interactive:
            midi_file = available_files[0]
            print(f"Non-interactive mode: selected {midi_file}")
        else:
            choice = safe_input("Select file number (Enter to create sample): ").strip()
            if choice.isdigit():
                selected = int(choice) - 1
                if 0 <= selected < len(available_files):
                    midi_file = available_files[selected]

    if midi_file is None:
        sample_path = Path("sample_scale.mid")
        midi_file = create_sample_midi(sample_path)
        created_sample = midi_file is not None

    if midi_file is None:
        print("No MIDI file available for playback.")
        return

    loaded = analyze_midi_file(midi_file)
    if loaded is None:
        return

    if non_interactive:
        print("\nNon-interactive mode: skipping playback actions.")
    else:
        while True:
            print("\nDemo options")
            print("1. Play selected MIDI file through interface")
            print("2. Play generated score through interface")
            print("3. Re-print MIDI analysis")
            print("4. Quit")

            choice = safe_input("Select option (1-4): ").strip()

            try:
                if choice == "1":
                    play_file_to_interface(midi_file, output_name)
                elif choice == "2":
                    play_generated_score_to_interface(output_name)
                elif choice == "3":
                    analyze_midi_file(midi_file)
                elif choice == "4":
                    break
                else:
                    print("Invalid choice.")
            except Exception as exc:
                print(f"Playback error: {exc}")

    if created_sample and midi_file.exists():
        try:
            midi_file.unlink()
            print(f"Removed temporary sample file: {midi_file}")
        except OSError:
            pass


if __name__ == "__main__":
    main()
