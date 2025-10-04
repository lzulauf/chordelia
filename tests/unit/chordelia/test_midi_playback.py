"""
Tests for the Chordelia MIDI playback module.

These tests focus on MIDI message generation, intelligent note management,
and proper resource handling. MIDI output is mocked to avoid requiring
actual MIDI hardware during testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time
from threading import Timer

from chordelia.notes import Note, C, D, E, F, G, A, B
from chordelia.chords import Chord
from chordelia.rhythm import Duration, Tempo, quarter_note, half_note, whole_note


# Fixtures
@pytest.fixture
def mock_midi():
    """Fixture providing mocked MIDI components."""
    with patch('chordelia.midi_playback.mido') as mock_mido, \
         patch('chordelia.midi_playback._MIDI_AVAILABLE', True):
        
        # Setup mock MIDI port
        mock_port = Mock()
        mock_port.closed = False
        mock_mido.open_output.return_value = mock_port
        mock_mido.get_output_names.return_value = ['Test MIDI Port']
        
        # Mock Message class
        mock_mido.Message = Mock(side_effect=lambda msg_type, **kwargs: 
                               {'type': msg_type, **kwargs})
        
        yield {
            'mido': mock_mido,
            'port': mock_port
        }


@pytest.fixture
def midi_unavailable():
    """Fixture for testing when MIDI is unavailable."""
    with patch('chordelia.midi_playback._MIDI_AVAILABLE', False):
        yield


class TestMIDIPlaybackNote:
    """Test MIDIPlaybackNote creation and validation."""
    
    def test_create_midi_playback_note(self):
        """Test creating a MIDI playback note with valid parameters."""
        pytest.importorskip('chordelia.midi_playback')
        
        from chordelia.midi_playback import MIDIPlaybackNote
        
        note = C.with_octave(4)
        midi_note = MIDIPlaybackNote(note, velocity=100, duration=quarter_note())
        
        assert midi_note.note == note
        assert midi_note.velocity == 100
        assert midi_note.duration == quarter_note()
        assert midi_note.midi_number == 60  # Middle C

    def test_note_requires_octave(self):
        """Test that MIDI playback note requires octave information."""
        pytest.importorskip('chordelia.midi_playback')
        
        from chordelia.midi_playback import MIDIPlaybackNote
        
        note_without_octave = C  # No octave specified
        
        with pytest.raises(ValueError, match="octave information"):
            MIDIPlaybackNote(note_without_octave)

    def test_velocity_validation(self):
        """Test MIDI velocity validation."""
        pytest.importorskip('chordelia.midi_playback')
        
        from chordelia.midi_playback import MIDIPlaybackNote
        
        note = C.with_octave(4)
        
        # Valid velocities
        MIDIPlaybackNote(note, velocity=0)   # Min
        MIDIPlaybackNote(note, velocity=127) # Max
        MIDIPlaybackNote(note, velocity=64)  # Default
        
        # Invalid velocities
        with pytest.raises(ValueError):
            MIDIPlaybackNote(note, velocity=-1)
        
        with pytest.raises(ValueError):
            MIDIPlaybackNote(note, velocity=128)

    def test_midi_playback_note_repr(self):
        """Test string representation of MIDI playback note."""
        pytest.importorskip('chordelia.midi_playback')
        
        from chordelia.midi_playback import MIDIPlaybackNote
        
        note = A.with_octave(4)
        midi_note = MIDIPlaybackNote(note, velocity=80)
        
        repr_str = repr(midi_note)
        assert "MIDIPlaybackNote" in repr_str
        assert "A4" in repr_str
        assert "velocity=80" in repr_str
        assert "midi=69" in repr_str  # A4 is MIDI 69


class TestMIDIChordPlayer:
    """Test MIDIChordPlayer with mocked MIDI output."""
    
    def test_midi_chord_player_creation(self, mock_midi):
        """Test creating MIDI chord player."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer(channel=5, default_velocity=80)
        
        assert player.channel == 5
        assert player.default_velocity == 80
        assert player.base_octave == 4
        assert player.is_connected
        
        player.stop()

    def test_chord_player_parameter_validation(self, mock_midi):
        """Test parameter validation in MIDIChordPlayer."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        # Invalid channel
        with pytest.raises(ValueError):
            MIDIChordPlayer(channel=-1)
        
        with pytest.raises(ValueError):
            MIDIChordPlayer(channel=16)
        
        # Invalid velocity
        with pytest.raises(ValueError):
            MIDIChordPlayer(default_velocity=-1)
        
        with pytest.raises(ValueError):
            MIDIChordPlayer(default_velocity=128)

    def test_update_chord_intelligent_management(self, mock_midi):
        """Test intelligent chord update with note change detection."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer()
        port = mock_midi['port']
        
        # Play C major chord (C, E, G)
        c_major = Chord.from_string("C")
        player.update_chord(c_major)
        
        # Check that note_on messages were sent (order may vary due to set)
        sent_messages = port.send.call_args_list
        assert len(sent_messages) == 3
        
        # Reset mock for next test
        port.send.reset_mock()
        
        # Change to F major chord (F, A, C) 
        f_major = Chord.from_string("F")
        player.update_chord(f_major)
        
        # Should send note_off for E4, G4 and note_on for F4, A4
        # C4 should continue (no change)
        sent_messages = port.send.call_args_list
        
        # Should have both note_off and note_on messages
        note_off_count = sum(1 for call in sent_messages 
                           if call[0][0]['type'] == 'note_off')
        note_on_count = sum(1 for call in sent_messages 
                          if call[0][0]['type'] == 'note_on')
        
        assert note_off_count == 2  # E4, G4
        assert note_on_count == 2   # F4, A4
        
        player.stop()

    def test_stop_all_notes(self, mock_midi):
        """Test stopping all notes."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer()
        port = mock_midi['port']
        
        # Play a chord
        chord = Chord.from_string("Am")
        player.update_chord(chord)
        
        # Reset mock
        port.send.reset_mock()
        
        # Stop all notes
        player.update_chord(None)
        
        # Should send note_off for all notes
        sent_messages = port.send.call_args_list
        note_off_count = sum(1 for call in sent_messages 
                           if call[0][0]['type'] == 'note_off')
        
        assert note_off_count == 3  # A, C, E
        assert len(player.current_notes) == 0
        
        player.stop()

    def test_play_single_note(self, mock_midi):
        """Test playing a single note."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer()
        port = mock_midi['port']
        
        note = A.with_octave(4)
        player.play_note(note, velocity=100)
        
        # Should send note_on for A4
        port.send.assert_called()
        last_call = port.send.call_args_list[-1]
        message = last_call[0][0]
        
        assert message['type'] == 'note_on'
        assert message['note'] == 69  # A4 MIDI number
        assert message['velocity'] == 100
        
        player.stop()

    def test_note_without_octave_uses_base_octave(self, mock_midi):
        """Test that notes without octave use base_octave."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer(base_octave=5)
        port = mock_midi['port']
        
        note = C  # No octave specified
        player.play_note(note)
        
        # Should use C5 (octave 5)
        last_call = port.send.call_args_list[-1]
        message = last_call[0][0]
        
        assert message['note'] == 72  # C5 MIDI number
        
        player.stop()

    def test_set_velocity_and_channel(self, mock_midi):
        """Test setting velocity and channel."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer()
        
        # Test velocity change
        player.set_velocity(100)
        assert player.default_velocity == 100
        
        # Test invalid velocity
        with pytest.raises(ValueError):
            player.set_velocity(128)
        
        # Test channel change
        player.set_channel(10)
        assert player.channel == 10
        
        # Test invalid channel
        with pytest.raises(ValueError):
            player.set_channel(16)
        
        player.stop()

    def test_midi_unavailable_error(self, midi_unavailable):
        """Test error when MIDI is not available."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        with pytest.raises(ImportError, match="mido"):
            MIDIChordPlayer()


class TestMIDIConvenienceFunctions:
    """Test MIDI convenience functions."""
    
    @patch('chordelia.midi_playback.time.sleep')
    def test_play_chord_function(self, mock_sleep, mock_midi):
        """Test play_chord convenience function."""
        from chordelia.midi_playback import play_chord
        from chordelia.rhythm import TimeSignature
        
        chord = Chord.from_string("G")
        tempo = Tempo(120)
        duration = half_note()
        
        play_chord(chord, tempo=tempo, duration=duration, velocity=80)
        
        # Should have sent note_on messages
        mock_midi['port'].send.assert_called()
        
        # Should have slept for the duration
        time_sig = TimeSignature(4, 4)
        expected_duration = tempo.duration_to_ms(duration, time_sig) / 1000.0
        mock_sleep.assert_called_with(expected_duration)

    @patch('chordelia.midi_playback.time.sleep')
    def test_play_melody_function(self, mock_sleep, mock_midi):
        """Test play_melody convenience function."""
        from chordelia.midi_playback import play_melody, MIDIPlaybackNote
        
        # Create a simple melody
        notes = [
            MIDIPlaybackNote(C.with_octave(4), velocity=64, duration=quarter_note()),
            D.with_octave(4),  # Plain note, will use defaults
            MIDIPlaybackNote(E.with_octave(4), velocity=80, duration=half_note())
        ]
        
        tempo = Tempo(120)
        play_melody(notes, tempo=tempo, default_velocity=70)
        
        # Should have sent multiple note_on messages
        assert mock_midi['port'].send.call_count >= 3
        
        # Should have slept multiple times
        assert mock_sleep.call_count >= 3


class TestMIDIUtilityFunctions:
    """Test MIDI utility functions."""
    
    def test_get_midi_ports_available(self):
        """Test get_midi_ports when MIDI is available."""
        with patch('chordelia.midi_playback._MIDI_AVAILABLE', True):
            with patch('chordelia.midi_playback.mido') as mock_mido:
                mock_mido.get_input_names.return_value = ['MIDI In 1', 'MIDI In 2']
                mock_mido.get_output_names.return_value = ['MIDI Out 1', 'MIDI Out 2']
                
                from chordelia.midi_playback import get_midi_ports
                
                ports = get_midi_ports()
                
                assert ports['input'] == ['MIDI In 1', 'MIDI In 2']
                assert ports['output'] == ['MIDI Out 1', 'MIDI Out 2']

    def test_get_midi_ports_unavailable(self, midi_unavailable):
        """Test get_midi_ports when MIDI is not available."""
        from chordelia.midi_playback import get_midi_ports
        
        ports = get_midi_ports()
        
        assert ports['input'] == []
        assert ports['output'] == []
        assert 'error' in ports

    def test_is_midi_available(self):
        """Test is_midi_available function."""
        with patch('chordelia.midi_playback._MIDI_AVAILABLE', True):
            from chordelia.midi_playback import is_midi_available
            assert is_midi_available() == True
        
        with patch('chordelia.midi_playback._MIDI_AVAILABLE', False):
            from chordelia.midi_playback import is_midi_available
            assert is_midi_available() == False


class TestMIDIErrorHandling:
    """Test MIDI error handling and edge cases."""
    
    def test_midi_port_connection_failure(self):
        """Test handling MIDI port connection failures."""
        with patch('chordelia.midi_playback.mido') as mock_mido, \
             patch('chordelia.midi_playback._MIDI_AVAILABLE', True):
            
            from chordelia.midi_playback import MIDIChordPlayer
            
            # Simulate port connection failure
            mock_mido.open_output.side_effect = Exception("Port not found")
            mock_mido.get_output_names.return_value = []
            
            # Should fall back to virtual port
            try:
                player = MIDIChordPlayer()
                # If we get here, virtual port fallback worked
                player.stop()
            except RuntimeError:
                # Expected if virtual port also fails
                pass

    def test_chord_with_mixed_octave_information(self, mock_midi):
        """Test chord with some notes having octave info, others not."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer(base_octave=3)
        
        # Create chord with mixed octave information
        notes_with_octaves = [C.with_octave(5), E, G.with_octave(4)]
        chord = Chord.from_notes(notes_with_octaves)
        
        player.update_chord(chord)
        
        # Should handle mixed octave info correctly
        assert mock_midi['port'].send.called
        
        player.stop()


class TestMIDIRealWorldScenarios:
    """Test real-world MIDI scenarios."""
    
    def test_chord_progression_midi_efficiency(self, mock_midi):
        """Test efficient MIDI output during chord progressions."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer()
        port = mock_midi['port']
        
        # I-vi-IV-V progression in C major
        progression = [
            Chord.from_string("C"),   # C-E-G
            Chord.from_string("Am"),  # A-C-E  
            Chord.from_string("F"),   # F-A-C
            Chord.from_string("G")    # G-B-D
        ]
        
        message_counts = []
        
        for chord in progression:
            port.send.reset_mock()
            player.update_chord(chord)
            message_counts.append(port.send.call_count)
        
        # First chord should send 3 note_on messages
        assert message_counts[0] == 3
        
        # Subsequent chords should be efficient (mix of note_on/note_off)
        # Each should send fewer than 6 messages total
        for count in message_counts[1:]:
            assert count <= 6
        
        player.stop()

    @patch('chordelia.midi_playback.time.sleep') 
    def test_rapid_chord_changes(self, mock_sleep, mock_midi):
        """Test rapid chord changes don't cause issues."""
        from chordelia.midi_playback import MIDIChordPlayer
        
        player = MIDIChordPlayer()
        port = mock_midi['port']
        
        chords = [
            Chord.from_string("C"),
            Chord.from_string("F"), 
            Chord.from_string("G"),
            Chord.from_string("Am")
        ]
        
        # Rapid chord changes
        for chord in chords:
            player.update_chord(chord)
            # No sleep - immediate changes
        
        # Should handle rapid changes without error
        assert port.send.called
        
        player.stop()
