"""Focused tests for playback note conversion helpers."""

from dataclasses import dataclass

import pytest

from chordelia.playback_notes import midi_tracks_to_playback_notes, score_to_playback_notes
from chordelia.rhythm import Duration
from chordelia.score import Score, ScoreEvent, ScoreMetadata


@dataclass
class _FakeMessage:
    type: str
    time: int
    note: int = 60
    velocity: int = 0


@dataclass
class _FakeMidiFile:
    ticks_per_beat: int
    tracks: list[list[_FakeMessage]]


class TestScoreToPlaybackNotes:
    def test_seconds_mode_durations_are_preserved(self):
        score = Score(
            source="manual",
            metadata=ScoreMetadata(tempo=90, retrigger_policy="retrigger_all"),
            events=(
                ScoreEvent(
                    beat=Duration.from_seconds(1.5),
                    duration=Duration.from_seconds(0.25),
                    pitches=(60,),
                    channel=0,
                    velocity=100,
                ),
            ),
        )

        notes = score_to_playback_notes(score)

        assert len(notes) == 1
        assert notes[0].start_time == pytest.approx(1.5)
        assert notes[0].duration == pytest.approx(0.25)

    def test_delta_mode_flushes_finished_windows(self):
        score = Score(
            source="manual",
            metadata=ScoreMetadata(tempo=120, gate_width=1.0, retrigger_policy="delta"),
            events=(
                ScoreEvent(beat=0, duration=1, pitches=(60,), channel=0),
                ScoreEvent(beat=3, duration=1, pitches=(62,), channel=0),
            ),
        )

        notes = score_to_playback_notes(score)

        assert len(notes) == 2
        assert notes[0].start_time == pytest.approx(0.0)
        assert notes[0].duration == pytest.approx(0.5)
        assert notes[1].start_time == pytest.approx(1.5)
        assert notes[1].duration == pytest.approx(0.5)


class TestMidiTracksToPlaybackNotes:
    def test_out_of_range_track_indices_are_ignored(self):
        midi_file = _FakeMidiFile(
            ticks_per_beat=480,
            tracks=[
                [
                    _FakeMessage(type="note_on", time=0, note=60, velocity=100),
                    _FakeMessage(type="note_off", time=480, note=60, velocity=0),
                ],
                [
                    _FakeMessage(type="note_on", time=0, note=62, velocity=100),
                    _FakeMessage(type="note_off", time=480, note=62, velocity=0),
                ],
            ],
        )

        notes = midi_tracks_to_playback_notes(midi_file, tempo_bpm=120, track_indices=[1, 99])

        assert len(notes) == 1
        assert str(notes[0].note) == "D4"

    def test_ignores_orphan_note_off_and_closes_active_note_at_track_end(self):
        midi_file = _FakeMidiFile(
            ticks_per_beat=480,
            tracks=[
                [
                    _FakeMessage(type="note_off", time=120, note=60, velocity=0),
                    _FakeMessage(type="note_on", time=0, note=61, velocity=100),
                    _FakeMessage(type="control_change", time=240),
                ],
            ],
        )

        notes = midi_tracks_to_playback_notes(midi_file, tempo_bpm=120)

        assert len(notes) == 1
        assert str(notes[0].note) == "C#4"
        assert notes[0].duration == pytest.approx(0.25)
