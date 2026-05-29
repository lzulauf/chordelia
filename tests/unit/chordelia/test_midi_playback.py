"""Tests for the canonical MidiPlayback API."""

from unittest.mock import Mock, patch

import pytest

from chordelia.chords import Chord
from chordelia.notes import C, D, E, Note
from chordelia.rhythm import Duration, Tempo, half_note
from chordelia.score import Score, ScoreEvent, ScoreMetadata


@pytest.fixture
def mock_midi():
    """Fixture providing mocked MIDI module and output port."""
    with patch("chordelia.midi_playback.mido") as mock_mido, patch(
        "chordelia.midi_playback._MIDI_AVAILABLE", True
    ):
        mock_port = Mock()
        mock_port.closed = False
        mock_mido.get_output_names.return_value = ["Test MIDI Port"]
        mock_mido.get_input_names.return_value = ["Test MIDI In"]
        mock_mido.open_output.return_value = mock_port
        mock_mido.Message = Mock(side_effect=lambda msg_type, **kwargs: {"type": msg_type, **kwargs})

        yield {"mido": mock_mido, "port": mock_port}


@pytest.fixture
def midi_unavailable():
    with patch("chordelia.midi_playback._MIDI_AVAILABLE", False):
        yield


class TestMidiPlayback:
    def test_creation_and_context_manager(self, mock_midi):
        from chordelia.midi_playback import MidiPlayback

        with MidiPlayback(channel=5, default_velocity=80) as playback:
            assert playback.channel == 5
            assert playback.default_velocity == 80
            assert playback.is_connected

        mock_midi["port"].close.assert_called_once()

    def test_update_chord_delta_behavior(self, mock_midi):
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        port = mock_midi["port"]

        playback.update_chord(Chord.from_string("C"))
        assert port.send.call_count == 3

        port.send.reset_mock()
        playback.update_chord(Chord.from_string("F"))

        note_off_count = sum(1 for call in port.send.call_args_list if call[0][0]["type"] == "note_off")
        note_on_count = sum(1 for call in port.send.call_args_list if call[0][0]["type"] == "note_on")
        assert note_off_count == 2
        assert note_on_count == 2

        playback.stop()

    def test_play_note_uses_base_octave_when_missing(self, mock_midi):
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback(base_octave=5)
        playback.play_note(C, duration=None)

        sent = mock_midi["port"].send.call_args_list[-1][0][0]
        assert sent["type"] == "note_on"
        assert sent["note"] == 72

        playback.stop()

    def test_play_score_sends_note_on_off_messages(self, mock_midi):
        from chordelia.midi_playback import MidiPlayback

        score = Score(
            source="x",
            metadata=ScoreMetadata(tempo=120, time_signature=(4, 4), ppq=480),
            events=(
                ScoreEvent(beat=0, duration=1, pitches=(60,), velocity=100, channel=0),
                ScoreEvent(beat=1, duration=1, pitches=(62,), velocity=90, channel=1),
            ),
        )

        playback = MidiPlayback()
        playback._sleep_until = lambda _target_time: None
        playback.play_score(score)

        message_types = [call[0][0]["type"] for call in mock_midi["port"].send.call_args_list]
        assert "note_on" in message_types
        assert "note_off" in message_types

        playback.stop()

    def test_parameter_validation(self, mock_midi):
        from chordelia.midi_playback import MidiPlayback

        with pytest.raises(ValueError):
            MidiPlayback(channel=16)
        with pytest.raises(ValueError):
            MidiPlayback(default_velocity=128)

        playback = MidiPlayback()
        with pytest.raises(ValueError):
            playback.set_channel(16)
        with pytest.raises(ValueError):
            playback.set_velocity(128)
        with pytest.raises(ValueError, match="velocity_scale"):
            playback.play_score(
                Score(
                    source="x",
                    metadata=ScoreMetadata(),
                    events=(ScoreEvent(beat=0, duration=1, pitches=(60,)),),
                ),
                velocity_scale=0,
            )
        playback.stop()

    def test_midi_unavailable_error(self, midi_unavailable):
        from chordelia.midi_playback import MidiPlayback

        with pytest.raises(ImportError, match="mido"):
            MidiPlayback()

    def test_missing_output_port_raises(self):
        with patch("chordelia.midi_playback.mido") as mock_mido, patch(
            "chordelia.midi_playback._MIDI_AVAILABLE", True
        ):
            from chordelia.midi_playback import MidiPlayback

            mock_mido.get_output_names.return_value = []
            with pytest.raises(RuntimeError, match="No MIDI output ports"):
                MidiPlayback()


class TestMidiConvenienceFunctions:
    @patch("chordelia.midi_playback.time.sleep")
    def test_play_chord_function(self, mock_sleep, mock_midi):
        from chordelia.midi_playback import play_chord
        from chordelia.rhythm import TimeSignature

        chord = Chord.from_string("G")
        tempo = Tempo(120)
        duration = half_note()
        play_chord(chord, tempo=tempo, duration=duration, velocity=80)

        assert mock_midi["port"].send.called

        time_sig = TimeSignature(4, 4)
        expected_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0
        mock_sleep.assert_called_with(expected_seconds)

    @patch("chordelia.midi_playback.time.sleep")
    def test_play_melody_function(self, _mock_sleep, mock_midi):
        from chordelia.midi_playback import play_melody

        notes = [C.with_octave(4), D.with_octave(4), E.with_octave(4)]
        play_melody(notes)

        assert mock_midi["port"].send.call_count >= 3


class TestMidiUtilityFunctions:
    def test_get_midi_ports_available(self):
        with patch("chordelia.midi_playback._MIDI_AVAILABLE", True), patch(
            "chordelia.midi_playback.mido"
        ) as mock_mido:
            mock_mido.get_input_names.return_value = ["In1"]
            mock_mido.get_output_names.return_value = ["Out1"]

            from chordelia.midi_playback import get_midi_ports

            ports = get_midi_ports()
            assert ports["input"] == ["In1"]
            assert ports["output"] == ["Out1"]

    def test_get_midi_ports_unavailable(self, midi_unavailable):
        from chordelia.midi_playback import get_midi_ports

        ports = get_midi_ports()
        assert ports["input"] == []
        assert ports["output"] == []
        assert "error" in ports

    def test_is_midi_available(self):
        with patch("chordelia.midi_playback._MIDI_AVAILABLE", True):
            from chordelia.midi_playback import is_midi_available

            assert is_midi_available() is True

        with patch("chordelia.midi_playback._MIDI_AVAILABLE", False):
            from chordelia.midi_playback import is_midi_available

            assert is_midi_available() is False
