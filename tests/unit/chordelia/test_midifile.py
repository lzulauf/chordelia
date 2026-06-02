"""Tests for the canonical MidiFile score-backed wrapper behavior."""

from pathlib import Path
from unittest.mock import patch

import pytest

mido = pytest.importorskip("mido")

from chordelia.midifile import MidiFile
from chordelia.notes import Note
from chordelia.playback_notes import midi_tracks_to_playback_notes, score_to_playback_notes
from chordelia.rhythm import Duration
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

    def test_to_file_writes_loaded_midi_source_when_score_is_none(self, tmp_path: Path):
        source_path = tmp_path / "source.mid"
        output_path = tmp_path / "copied.mid"

        midi = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.Message("note_on", note=60, velocity=90, channel=0, time=0))
        track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=480))
        track.append(mido.MetaMessage("end_of_track", time=0))
        midi.save(str(source_path))

        loaded = MidiFile.load_from_file(source_path)
        loaded.score = None

        written_path = loaded.to_file(output_path)

        assert written_path == output_path
        assert output_path.exists()

    def test_to_file_raises_when_wrapper_has_no_score_or_midi_data(self, tmp_path: Path):
        midi = MidiFile.__new__(MidiFile)
        midi.score = None
        midi.midi_file = None

        with pytest.raises(ValueError, match="no score or source MIDI data"):
            midi.to_file(tmp_path / "missing.mid")

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

    def test_load_from_file_analyzes_track_metadata_and_duration(self, tmp_path: Path):
        source_path = tmp_path / "analysis.mid"

        midi = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.MetaMessage("track_name", name="Lead", time=0))
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(90), time=0))
        track.append(mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0))
        track.append(mido.Message("program_change", program=12, channel=2, time=0))
        track.append(mido.Message("note_on", note=64, velocity=90, channel=2, time=0))
        track.append(mido.Message("note_off", note=64, velocity=0, channel=2, time=480))
        track.append(mido.MetaMessage("end_of_track", time=0))
        midi.save(str(source_path))

        loaded = MidiFile.load_from_file(source_path)

        assert loaded.tempo.bpm == pytest.approx(90.0)
        assert loaded.time_signature.beats_per_measure == 3
        assert loaded.time_signature.beat_unit == 4
        assert loaded.duration_seconds > 0
        assert len(loaded.tracks_info) == 1
        assert loaded.tracks_info[0].name == "Lead"
        assert loaded.tracks_info[0].channel == 2
        assert loaded.tracks_info[0].instrument == 12
        assert loaded.tracks_info[0].note_count == 1

    def test_score_from_file_loads_metadata_and_ignores_orphan_note_off(self, tmp_path: Path):
        source_path = tmp_path / "metadata.mid"

        midi = mido.MidiFile(ticks_per_beat=960)
        track = mido.MidiTrack()
        midi.tracks.append(track)
        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(90), time=0))
        track.append(mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0))
        track.append(mido.MetaMessage("key_signature", key="G", time=0))
        # Orphan note_off should be ignored.
        track.append(mido.Message("note_off", note=60, velocity=0, channel=0, time=120))
        track.append(mido.Message("note_on", note=62, velocity=70, channel=1, time=0))
        track.append(mido.Message("note_off", note=62, velocity=0, channel=1, time=480))
        track.append(mido.MetaMessage("end_of_track", time=0))
        midi.save(str(source_path))

        score = MidiFile.score_from_file(source_path)

        assert score.metadata.tempo == 90
        assert score.metadata.time_signature == (3, 4)
        assert score.metadata.key_signature == "G"
        assert score.metadata.ppq == 960
        assert len(score.events) == 1
        assert score.events[0].pitches == (62,)
        assert score.events[0].channel == 1

    def test_score_from_file_raises_for_missing_path(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="MIDI file not found"):
            MidiFile.score_from_file(tmp_path / "does-not-exist.mid")

    def test_score_from_file_raises_for_invalid_midi_data(self, tmp_path: Path):
        bad_path = tmp_path / "invalid.mid"
        bad_path.write_text("not a midi file", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid MIDI file"):
            MidiFile.score_from_file(bad_path)

    def test_constructor_raises_for_missing_file_path(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="MIDI file not found"):
            MidiFile(tmp_path / "absent.mid")

    def test_constructor_raises_for_invalid_midi_file(self, tmp_path: Path):
        bad_path = tmp_path / "broken.mid"
        bad_path.write_text("broken midi", encoding="utf-8")

        with patch("chordelia.midifile.mido.MidiFile", side_effect=RuntimeError("bad parse")):
            with pytest.raises(ValueError, match="Invalid MIDI file"):
                MidiFile(bad_path)


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


class TestMidiFileUtilities:
    def test_score_to_file_rejects_non_score_inputs(self, tmp_path: Path):
        with pytest.raises(TypeError, match="score must be a Score instance"):
            MidiFile.score_to_file("not-a-score", tmp_path / "x.mid")

    def test_score_backed_wrapper_with_empty_events_has_no_tracks(self):
        score = Score(source="manual", metadata=ScoreMetadata(), events=())
        midi = MidiFile(score)

        assert midi.tracks_info == []
        assert midi.duration_seconds == 0.0

    def test_duration_helpers_support_seconds_mode(self):
        midi = MidiFile(Note("C4"))
        seconds_duration = Duration.from_seconds(0.5)

        assert midi._duration_to_ticks(seconds_duration, tempo_bpm=120, ppq=480) == 480
        assert midi._duration_to_seconds(seconds_duration, tempo_bpm=120) == pytest.approx(0.5)

    def test_mido_from_score_includes_key_signature_meta_message(self):
        score = Score(
            source="manual",
            metadata=ScoreMetadata(key_signature="G"),
            events=(ScoreEvent(beat=0, duration=1, pitches=(60,), channel=0),),
        )
        midi = MidiFile(score)

        rendered = midi._mido_from_score(score)

        meta_types = [message.type for message in rendered.tracks[0] if message.is_meta]
        assert "key_signature" in meta_types

    def test_analyze_file_requires_loaded_midi(self):
        midi = MidiFile.__new__(MidiFile)
        midi.midi_file = None

        with pytest.raises(ValueError, match="No MIDI file is loaded"):
            midi._analyze_file()

    def test_print_info_emits_summary_lines(self, capsys):
        midi = MidiFile(Note("C4"))

        midi.print_info()

        captured = capsys.readouterr().out
        assert "MIDI File:" in captured
        assert "Tempo:" in captured
        assert "Tracks:" in captured


