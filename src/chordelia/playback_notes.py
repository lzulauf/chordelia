"""PlaybackNote conversion helpers shared across playback entry points."""

from typing import Dict, List, Optional

from chordelia.accidentals import Accidental
from chordelia.audio_playback import PlaybackNote
from chordelia.notes import Note, NoteName
from chordelia.rhythm import Duration
from chordelia.score import Score

_SUPPORTED_RETRIGGER_POLICIES = {"delta", "retrigger_all"}


def midi_note_to_note(midi_note: int) -> Note:
    """Convert a MIDI note number (0-127) to a Note instance."""
    octave = (midi_note // 12) - 1
    semitone = midi_note % 12

    note_mapping = [
        (NoteName.C, Accidental.NATURAL),
        (NoteName.C, Accidental.SHARP),
        (NoteName.D, Accidental.NATURAL),
        (NoteName.D, Accidental.SHARP),
        (NoteName.E, Accidental.NATURAL),
        (NoteName.F, Accidental.NATURAL),
        (NoteName.F, Accidental.SHARP),
        (NoteName.G, Accidental.NATURAL),
        (NoteName.G, Accidental.SHARP),
        (NoteName.A, Accidental.NATURAL),
        (NoteName.A, Accidental.SHARP),
        (NoteName.B, Accidental.NATURAL),
    ]

    note_name, accidental = note_mapping[semitone]
    return Note(note_name, accidental, octave)


def validate_retrigger_policy(policy: str) -> None:
    """Validate supported score-backed audio retrigger policy values."""
    if policy not in _SUPPORTED_RETRIGGER_POLICIES:
        raise ValueError(
            "retrigger_policy must be 'delta' or 'retrigger_all', "
            f"got {policy!r}"
        )


def _duration_to_seconds(duration: Duration, *, tempo_bpm: int) -> float:
    """Convert beat/time Duration values into wall-clock seconds."""
    if duration.mode == "seconds":
        return float(duration.as_seconds())
    beats = float(duration.as_beats())
    return beats * 60.0 / float(tempo_bpm)


def score_to_playback_notes(
    score: Score,
    *,
    velocity_scale: float = 1.0,
    retrigger_policy: Optional[str] = None,
) -> List[PlaybackNote]:
    """Convert score-backed state into playback notes."""
    playback_notes: list[PlaybackNote] = []
    tempo_bpm = score.metadata.tempo
    effective_policy = (
        score.metadata.retrigger_policy if retrigger_policy is None else retrigger_policy
    )
    validate_retrigger_policy(effective_policy)

    if effective_policy == "retrigger_all":
        for event in score.events:
            start_time = _duration_to_seconds(event.beat, tempo_bpm=tempo_bpm)
            duration = _duration_to_seconds(event.duration, tempo_bpm=tempo_bpm)
            velocity = (event.velocity / 127.0) * velocity_scale

            for pitch in event.pitches:
                playback_notes.append(
                    PlaybackNote(
                        start_time=start_time,
                        note=midi_note_to_note(pitch),
                        duration=duration,
                        velocity=velocity,
                    )
                )

        playback_notes.sort(key=lambda note: note.start_time)
        return playback_notes

    active_notes: dict[tuple[int, int], dict[str, float | Note]] = {}

    def flush_finished_notes(before_time: float) -> None:
        for key, note_info in tuple(active_notes.items()):
            end_time = note_info["end_time"]
            if end_time < before_time:
                start_time = note_info["start_time"]
                duration = end_time - start_time
                if duration > 0:
                    playback_notes.append(
                        PlaybackNote(
                            start_time=start_time,
                            note=note_info["note"],
                            duration=duration,
                            velocity=note_info["velocity"],
                        )
                    )
                del active_notes[key]

    for event in score.events:
        start_time = _duration_to_seconds(event.beat, tempo_bpm=tempo_bpm)
        duration = _duration_to_seconds(event.duration, tempo_bpm=tempo_bpm)
        end_time = start_time + duration
        velocity = (event.velocity / 127.0) * velocity_scale

        flush_finished_notes(start_time)

        for pitch in event.pitches:
            key = (event.channel, pitch)
            note_info = active_notes.get(key)
            if note_info is not None and note_info["end_time"] >= start_time:
                if end_time > note_info["end_time"]:
                    note_info["end_time"] = end_time
                continue

            active_notes[key] = {
                "note": midi_note_to_note(pitch),
                "start_time": start_time,
                "end_time": end_time,
                "velocity": velocity,
            }

    for note_info in active_notes.values():
        duration = note_info["end_time"] - note_info["start_time"]
        if duration <= 0:
            continue
        playback_notes.append(
            PlaybackNote(
                start_time=note_info["start_time"],
                note=note_info["note"],
                duration=duration,
                velocity=note_info["velocity"],
            )
        )

    playback_notes.sort(key=lambda note: note.start_time)
    return playback_notes


def midi_tracks_to_playback_notes(
    midi_file: object,
    *,
    tempo_bpm: int,
    track_indices: Optional[List[int]] = None,
    velocity_scale: float = 1.0,
) -> List[PlaybackNote]:
    """Convert a mido-style MIDI file object into playback notes."""
    playback_notes = []
    safe_tempo_bpm = max(1, int(tempo_bpm))
    ticks_per_beat = midi_file.ticks_per_beat
    seconds_per_tick = 60.0 / float(safe_tempo_bpm) / float(ticks_per_beat)

    if track_indices is None:
        tracks_to_process = enumerate(midi_file.tracks)
    else:
        tracks_to_process = [
            (i, midi_file.tracks[i])
            for i in track_indices
            if i < len(midi_file.tracks)
        ]

    for _track_idx, track in tracks_to_process:
        active_notes: Dict[int, Dict[str, float | Note]] = {}
        current_time = 0.0

        for message in track:
            current_time += float(message.time) * seconds_per_tick

            if message.type == "note_on" and message.velocity > 0:
                active_notes[message.note] = {
                    "note": midi_note_to_note(message.note),
                    "start_time": current_time,
                    "velocity": (message.velocity / 127.0) * velocity_scale,
                }
                continue

            is_note_off = message.type == "note_off" or (
                message.type == "note_on" and message.velocity == 0
            )
            if not is_note_off:
                continue

            if message.note not in active_notes:
                continue

            note_info = active_notes.pop(message.note)
            duration = current_time - note_info["start_time"]
            playback_notes.append(
                PlaybackNote(
                    start_time=note_info["start_time"],
                    note=note_info["note"],
                    duration=duration,
                    velocity=note_info["velocity"],
                )
            )

        for note_info in active_notes.values():
            duration = current_time - note_info["start_time"]
            if duration <= 0:
                continue
            playback_notes.append(
                PlaybackNote(
                    start_time=note_info["start_time"],
                    note=note_info["note"],
                    duration=duration,
                    velocity=note_info["velocity"],
                )
            )

    playback_notes.sort(key=lambda note: note.start_time)
    return playback_notes


__all__ = [
    "midi_note_to_note",
    "midi_tracks_to_playback_notes",
    "score_to_playback_notes",
    "validate_retrigger_policy",
]
