"""Tests for the canonical MidiFile score-backed wrapper behavior."""

from pathlib import Path
from unittest.mock import patch

import pytest

mido = pytest.importorskip("mido")

from chordelia.midifile import MidiFile
from chordelia.notes import Note
from chordelia.playback_notes import midi_tracks_to_playback_notes, score_to_playback_notes
from chordelia.score import Score, ScoreEvent, ScoreMetadata


def _collect_absolute_note_messages(midi_file):
    """Collect note on/off messages with absolute ticks for assertions."""
    absolute_messages = []
    for track in midi_file.tracks:
        absolute_tick = 0
        for message in track:
            absolute_tick += message.time
            if message.type in {"note_on", "note_off"}:
                absolute_messages.append((message.type, message.note, message.velocity, message.channel, absolute_tick))
    return absolute_messages


class TestMidiFileScoreBackedConstruction:
    """Constructor normalization behavior for canonical MidiFile workflows."""

    def test_constructor_normalizes_sequenceable_source_to_score(self):
        midi = MidiFile(Note("C4"))

        assert isinstance(midi.score, Score)
        assert midi.score is not None
        assert midi.score.events[0].pitches == (60,)
        assert midi.score.metadata.tempo == 120

    def test_constructor_accepts_existing_score_instance(self):
        score = Score.from_sequenceable(Note("D4"), tempo=90, time_signature=(3, 4), ppq=960)

        midi = MidiFile(score)

        assert midi.score is score
        assert midi.tempo.bpm == 90
        assert midi.time_signature.beats_per_measure == 3
        assert midi.time_signature.beat_unit == 4


class TestMidiFileWritePath:
    """MIDI file writing behavior from canonical score-backed wrappers."""

    def test_to_file_writes_note_events_from_sequenceable_source(self, tmp_path: Path):
        output_path = tmp_path / "single_note.mid"

        midi = MidiFile(Note("C4"))
        written_path = midi.to_file(output_path)

        assert written_path == output_path
        assert output_path.exists()

        written = mido.MidiFile(str(output_path))
        assert written.ticks_per_beat == 480

        note_messages = _collect_absolute_note_messages(written)
        assert ("note_on", 60, 64, 0, 0) in note_messages
        assert ("note_off", 60, 0, 0, 480) in note_messages

    def test_score_to_file_writes_polyphonic_channel_events(self, tmp_path: Path):
        output_path = tmp_path / "polyphonic.mid"

        score = Score(
            source="manual",
            metadata=ScoreMetadata(tempo=100, time_signature=(3, 4), ppq=960),
            events=(
                ScoreEvent(beat=0, duration=2, pitches=(60, 64), velocity=90, channel=2),
            ),
        )

        written_path = MidiFile.score_to_file(score, output_path)

        assert written_path == output_path
        assert output_path.exists()

        written = mido.MidiFile(str(output_path))
        assert written.ticks_per_beat == 960

        # Verify score metadata messages are present.
        meta_types = [message.type for message in written.tracks[0] if message.is_meta]
        assert "set_tempo" in meta_types
        assert "time_signature" in meta_types

        note_messages = _collect_absolute_note_messages(written)
        assert ("note_on", 60, 90, 2, 0) in note_messages
        assert ("note_on", 64, 90, 2, 0) in note_messages
        assert ("note_off", 60, 0, 2, 1920) in note_messages
        assert ("note_off", 64, 0, 2, 1920) in note_messages


class TestMidiFileReadPath:
    """MIDI file read behavior through the score-backed MidiFile wrapper."""

    def test_load_from_file_keeps_playback_conversion_working(self, tmp_path: Path):
        source_path = tmp_path / "source.mid"

        midi = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.Message("note_on", note=60, velocity=96, channel=0, time=0))
        track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
        track.append(mido.MetaMessage("end_of_track", time=0))
        midi.save(str(source_path))

        loaded = MidiFile.load_from_file(source_path)
        assert loaded.midi_file is not None
        playback_notes = midi_tracks_to_playback_notes(
            loaded.midi_file,
            tempo_bpm=loaded.tempo.bpm,
        )

        assert loaded.filepath == source_path
        assert loaded.score is not None
        assert len(playback_notes) == 1
        assert str(playback_notes[0].note) == "C4"


class TestMidiFileScoreBackedAudioConversion:
    """Score-to-audio note conversion behavior and articulation policy handling."""

    def test_score_backed_playback_notes_default_to_retrigger_all(self):
        score = Score(
            source="manual",
            metadata=ScoreMetadata(tempo=120, retrigger_policy="retrigger_all"),
            events=(
                ScoreEvent(beat=0, duration=1, pitches=(60,), channel=0, velocity=80),
                ScoreEvent(beat=1, duration=1, pitches=(60,), channel=0, velocity=70),
            ),
        )
        playback_notes = score_to_playback_notes(score)

        assert len(playback_notes) == 2
        assert playback_notes[0].start_time == pytest.approx(0.0)
        assert playback_notes[0].duration == pytest.approx(0.5)
        assert playback_notes[1].start_time == pytest.approx(0.5)
        assert playback_notes[1].duration == pytest.approx(0.5)

    def test_score_backed_playback_notes_allow_delta_override(self):
        score = Score(
            source="manual",
            metadata=ScoreMetadata(tempo=120, retrigger_policy="retrigger_all"),
            events=(
                ScoreEvent(beat=0, duration=1, pitches=(60,), channel=0),
                ScoreEvent(beat=1, duration=1, pitches=(60,), channel=0),
            ),
        )
        playback_notes = score_to_playback_notes(score, retrigger_policy="delta")

        assert len(playback_notes) == 1
        assert playback_notes[0].start_time == pytest.approx(0.0)
        assert playback_notes[0].duration == pytest.approx(1.0)

    def test_delta_mode_does_not_merge_across_channels(self):
        score = Score(
            source="manual",
            metadata=ScoreMetadata(tempo=120, retrigger_policy="delta"),
            events=(
                ScoreEvent(beat=0, duration=1, pitches=(60,), channel=0),
                ScoreEvent(beat=1, duration=1, pitches=(60,), channel=1),
            ),
        )
        playback_notes = score_to_playback_notes(score)

        assert len(playback_notes) == 2

    def test_score_backed_playback_notes_reject_bad_policy(self):
        score = Score.from_sequenceable(Note("C4"))

        with pytest.raises(ValueError, match="retrigger_policy"):
            score_to_playback_notes(score, retrigger_policy="bad")


class TestMidiFileInterfacePlayback:
    """Playback-to-interface behavior through the canonical MidiPlayback transport."""

    def test_play_to_interface_delegates_to_midiplayback(self):
        midi = MidiFile(Note("C4"))

        with patch("chordelia.midi_playback.MidiPlayback") as mock_transport:
            transport_instance = mock_transport.return_value.__enter__.return_value

            midi.play_to_interface(
                output_name="Test MIDI Port",
                blocking=False,
                velocity_scale=1.2,
                channel_override=3,
                gate_width=0.8,
                gate_offset=0.1,
                retrigger_policy="retrigger_all",
            )

            mock_transport.assert_called_once_with(output_name="Test MIDI Port")
            transport_instance.play_score.assert_called_once()
            args, kwargs = transport_instance.play_score.call_args
            assert args[0] is midi.score
            assert kwargs["blocking"] is False
            assert kwargs["velocity_scale"] == 1.2
            assert kwargs["channel_override"] == 3
            assert kwargs["gate_width"] == 0.8
            assert kwargs["gate_offset"] == 0.1
            assert kwargs["retrigger_policy"] == "retrigger_all"
