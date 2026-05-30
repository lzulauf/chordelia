"""
Tests for the Chordelia playback module.

These tests focus on timing accuracy, frequency calculations, and integration
with the rhythm and notes modules. Audio output testing is mocked to avoid
requiring actual audio hardware during CI/testing.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

import pytest

from chordelia.notes import Note
from chordelia.rhythm import Duration, Tempo
from chordelia.scales import Scale, ScaleType
from chordelia.chords import Chord


class TestPlaybackNote(unittest.TestCase):
    """Test PlaybackNote data structure."""
    
    def setUp(self):
        self.note_c4 = Note("C4")
        self.quarter = Duration("quarter")
        
    def test_create_playback_note(self):
        """Test creating a basic PlaybackNote."""
        from chordelia.audio_playback import PlaybackNote
        
        playback_note = PlaybackNote(
            start_time=self.quarter,
            note=self.note_c4,
            duration=self.quarter,
            velocity=0.7
        )
        
        self.assertEqual(playback_note.start_time, self.quarter)
        self.assertEqual(playback_note.note, self.note_c4)
        self.assertEqual(playback_note.duration, self.quarter)
        self.assertEqual(playback_note.velocity, 0.7)
    
    def test_playback_note_with_milliseconds(self):
        """Test PlaybackNote with millisecond timing."""
        from chordelia.audio_playback import PlaybackNote
        
        playback_note = PlaybackNote(
            start_time=500.0,  # 500ms
            note=self.note_c4,
            duration=1000.0,   # 1 second
            velocity=0.5
        )
        
        self.assertEqual(playback_note.start_time, 500.0)
        self.assertEqual(playback_note.duration, 1000.0)
    
    def test_velocity_validation(self):
        """Test velocity validation."""
        from chordelia.audio_playback import PlaybackNote
        
        # Valid velocities
        PlaybackNote(0.0, self.note_c4, self.quarter, 0.0)  # Should not raise
        PlaybackNote(0.0, self.note_c4, self.quarter, 1.0)  # Should not raise
        PlaybackNote(0.0, self.note_c4, self.quarter, 0.5)  # Should not raise
        
        # Invalid velocities
        with self.assertRaises(ValueError):
            PlaybackNote(0.0, self.note_c4, self.quarter, -0.1)
        
        with self.assertRaises(ValueError):
            PlaybackNote(0.0, self.note_c4, self.quarter, 1.1)
    
    def test_note_requires_octave(self):
        """Test that notes must have octave information."""
        from chordelia.audio_playback import PlaybackNote
        
        note_no_octave = Note("C")  # No octave
        
        with self.assertRaises(ValueError):
            PlaybackNote(0.0, note_no_octave, self.quarter)


class TestAudioBackendMocked(unittest.TestCase):
    """Test AudioBackend with mocked audio dependencies."""
    
    def setUp(self):
        # Mock the audio dependencies
        self.mock_sounddevice = Mock()
        self.mock_numpy = Mock()
        
        # Mock numpy array functions
        self.mock_numpy.ndarray = Mock
        self.mock_numpy.arange.return_value = Mock()
        self.mock_numpy.sin.return_value = Mock()
        self.mock_numpy.sign.return_value = Mock()
        self.mock_numpy.abs.return_value = Mock()
        self.mock_numpy.float32 = float
        
        # Mock sounddevice stream
        self.mock_stream = Mock()
        self.mock_sounddevice.OutputStream.return_value = self.mock_stream
    
    @patch('chordelia.audio_playback.sd')
    @patch('chordelia.audio_playback.np')
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
    def test_audio_backend_creation(self, mock_np, mock_sd):
        """Test AudioBackend creation."""
        from chordelia.audio_playback import AudioBackend
        import numpy as np
        
        # Mock NumPy functions to return actual arrays for math operations
        mock_np.arange.return_value = np.arange(4096)
        mock_np.sin.return_value = np.sin(np.arange(4096))
        mock_np.sign.return_value = np.sign(np.sin(np.arange(4096)))
        mock_np.pi = np.pi
        mock_np.float32 = np.float32
        
        backend = AudioBackend(sample_rate=44100, buffer_size=512)
        self.assertEqual(backend.sample_rate, 44100)
        self.assertEqual(backend.buffer_size, 512)
    
    @patch('chordelia.audio_playback.sd')
    @patch('chordelia.audio_playback.np') 
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
    def test_start_stop_stream(self, mock_np, mock_sd):
        """Test starting and stopping audio stream."""
        from chordelia.audio_playback import AudioBackend
        
        mock_stream = Mock()
        mock_sd.OutputStream.return_value = mock_stream
        
        backend = AudioBackend()
        
        # Test start
        backend.start()
        mock_sd.OutputStream.assert_called_once()
        mock_stream.start.assert_called_once()
        
        # Test stop
        backend.stop()
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
    
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', False)
    def test_audio_backend_unavailable(self):
        """Test AudioBackend when audio dependencies are unavailable."""
        from chordelia.audio_playback import AudioBackend
        
        with self.assertRaises(ImportError):
            AudioBackend()


class TestPlaybackTiming(unittest.TestCase):
    """Test playback timing calculations."""
    
    def setUp(self):
        self.tempo_120 = Tempo(120)  # 120 BPM
        self.tempo_60 = Tempo(60)    # 60 BPM
    
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
    def test_duration_to_milliseconds_conversion(self):
        """Test conversion from Duration to milliseconds."""
        from chordelia.audio_playback import Playback
        from chordelia.rhythm import COMMON_TIME
        
        playback = Playback(self.tempo_120, COMMON_TIME)
        
        # At 120 BPM, quarter note = 500ms
        quarter_ms = playback._convert_to_milliseconds(Duration("quarter"))
        self.assertEqual(quarter_ms, 500.0)
        
        # Half note = 1000ms
        half_ms = playback._convert_to_milliseconds(Duration("half"))
        self.assertEqual(half_ms, 1000.0)
        
        # Whole note = 2000ms
        whole_ms = playback._convert_to_milliseconds(Duration("whole"))
        self.assertEqual(whole_ms, 2000.0)
    
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
    def test_milliseconds_passthrough(self):
        """Test that millisecond values pass through unchanged."""
        from chordelia.audio_playback import Playback
        from chordelia.rhythm import COMMON_TIME
        
        playback = Playback(self.tempo_120, COMMON_TIME)
        
        # Milliseconds should pass through unchanged
        self.assertEqual(playback._convert_to_milliseconds(1500.0), 1500.0)
        self.assertEqual(playback._convert_to_milliseconds(750.5), 750.5)
    
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
    def test_tempo_effects_on_timing(self):
        """Test that different tempos affect timing correctly."""
        from chordelia.audio_playback import Playback
        from chordelia.rhythm import COMMON_TIME
        
        # 120 BPM: quarter = 500ms
        playback_120 = Playback(self.tempo_120, COMMON_TIME)
        quarter_120 = playback_120._convert_to_milliseconds(Duration("quarter"))
        self.assertEqual(quarter_120, 500.0)
        
        # 60 BPM: quarter = 1000ms
        playback_60 = Playback(self.tempo_60, COMMON_TIME)
        quarter_60 = playback_60._convert_to_milliseconds(Duration("quarter"))
        self.assertEqual(quarter_60, 1000.0)


class TestFrequencyCalculations(unittest.TestCase):
    """Test frequency calculations for notes."""
    
    def test_note_frequencies(self):
        """Test that notes produce correct frequencies."""
        # A4 should be 440 Hz
        a4 = Note("A4")
        self.assertAlmostEqual(a4.frequency, 440.0, places=1)
        
        # C4 (Middle C) should be ~261.63 Hz
        c4 = Note("C4")
        self.assertAlmostEqual(c4.frequency, 261.63, places=1)
        
        # Octave doubling: A5 should be 880 Hz
        a5 = Note("A5")
        self.assertAlmostEqual(a5.frequency, 880.0, places=1)
        
        # Octave halving: A3 should be 220 Hz
        a3 = Note("A3")
        self.assertAlmostEqual(a3.frequency, 220.0, places=1)


@patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
class TestPlaybackIntegration(unittest.TestCase):
    """Test integration between playback and other Chordelia modules."""
    
    def setUp(self):
        self.tempo = Tempo(120)
        
        # Mock audio components
        self.patcher_sd = patch('chordelia.audio_playback.sd')
        self.patcher_np = patch('chordelia.audio_playback.np')
        
        self.mock_sd = self.patcher_sd.start()
        self.mock_np = self.patcher_np.start()
        
        # Setup numpy mocks
        self.mock_np.arange.return_value = [0, 1, 2, 3, 4]
        self.mock_np.sin.return_value = [0, 0.5, 1, 0.5, 0]
        self.mock_np.sign.return_value = [0, 1, 1, 1, 0]
        self.mock_np.abs.return_value = [0, 0.5, 1, 0.5, 0]
        self.mock_np.float32 = float
        
        # Setup sounddevice mocks
        self.mock_stream = Mock()
        self.mock_sd.OutputStream.return_value = self.mock_stream
        
    def tearDown(self):
        self.patcher_sd.stop()
        self.patcher_np.stop()
    
    def test_playback_note_creation(self):
        """Test creating PlaybackNote objects."""
        from chordelia.audio_playback import PlaybackNote
        
        note = Note("C4")
        duration = Duration("quarter")
        
        playback_note = PlaybackNote(
            start_time=Duration(0),
            note=note,
            duration=duration,
            velocity=0.7
        )
        
        self.assertEqual(playback_note.note, note)
        self.assertEqual(playback_note.duration, duration)
    
    def test_sequence_timing_calculation(self):
        """Test sequence timing calculations."""
        from chordelia.audio_playback import Playback, PlaybackNote
        from chordelia.rhythm import COMMON_TIME
        
        notes = [
            PlaybackNote(Duration(0), Note("C4"), Duration("quarter"), 0.7),
            PlaybackNote(Duration("quarter"), Note("D4"), Duration("quarter"), 0.7),
            PlaybackNote(Duration("half"), Note("E4"), Duration("quarter"), 0.7),
        ]
        
        playback = Playback(self.tempo, COMMON_TIME)
        
        # Test internal timing conversion
        start_times = [playback._convert_to_milliseconds(note.start_time) for note in notes]
        expected_times = [0.0, 500.0, 1000.0]  # At 120 BPM
        
        self.assertEqual(start_times, expected_times)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for common playback scenarios."""
    
    def setUp(self):
        self.tempo = Tempo(120)
        
        # Mock audio components
        self.patcher_sd = patch('chordelia.audio_playback.sd')
        self.patcher_np = patch('chordelia.audio_playback.np')
        self.patcher_available = patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
        
        self.mock_sd = self.patcher_sd.start()
        self.mock_np = self.patcher_np.start()
        self.patcher_available.start()
        
        # Setup mocks
        self.mock_np.arange.return_value = []
        self.mock_np.sin.return_value = []
        self.mock_np.float32 = float
        
        self.mock_stream = Mock()
        self.mock_sd.OutputStream.return_value = self.mock_stream
        
    def tearDown(self):
        self.patcher_sd.stop()
        self.patcher_np.stop()
        self.patcher_available.stop()
    
    @pytest.mark.slow
    @patch('time.sleep', Mock())  # Speed up tests
    def test_play_scale_function(self):
        """Test the play_scale convenience function."""
        from chordelia.audio_playback import play_scale
        
        scale = Scale("C", ScaleType.MAJOR)
        
        # Should not raise an exception
        play_scale(scale, self.tempo, Duration("quarter"), octave=4)
        
        # Verify audio stream was used
        self.mock_sd.OutputStream.assert_called()
        self.mock_stream.start.assert_called()
    
    @patch('time.sleep', Mock())  # Speed up tests
    def test_play_scale_respects_octave_information(self):
        """Test that play_scale uses octave information from scale notes when available."""
        from chordelia.audio_playback import play_scale, PlaybackNote
        
        # Create a scale with octave information that crosses octave boundaries
        scale_with_octave = Scale("B4", ScaleType.MAJOR)
        
        # Mock the Playback class to capture the notes being played
        with patch('chordelia.audio_playback.Playback') as mock_playback_class:
            mock_playback_instance = MagicMock()
            mock_playback_class.return_value.__enter__.return_value = mock_playback_instance
            
            # Call play_scale - should use the scale's octave information
            play_scale(scale_with_octave, self.tempo, Duration("quarter"))
            
            # Verify play_sequence was called
            mock_playback_instance.play_sequence.assert_called_once()
            
            # Get the notes that were passed to play_sequence
            call_args = mock_playback_instance.play_sequence.call_args[0]
            played_notes = call_args[0]  # First argument is the notes list
            
            # Verify we have the right number of notes (7 for major scale)
            self.assertEqual(len(played_notes), 7)
            
            # Extract the actual Note objects from PlaybackNotes
            actual_notes = [pn.note for pn in played_notes]
            
            # Verify the notes have the correct octaves (should match scale.notes)
            expected_notes = scale_with_octave.notes
            
            for i, (actual, expected) in enumerate(zip(actual_notes, expected_notes)):
                self.assertEqual(actual.name, expected.name, f"Note {i} name mismatch")
                self.assertEqual(actual.accidental, expected.accidental, f"Note {i} accidental mismatch") 
                self.assertEqual(actual.octave, expected.octave, f"Note {i} octave mismatch: expected {expected.octave}, got {actual.octave}")
    
    @patch('time.sleep', Mock())  # Speed up tests
    def test_play_scale_uses_fallback_octave_when_no_octave_info(self):
        """Test that play_scale uses the octave parameter when scale notes have no octave."""
        from chordelia.audio_playback import play_scale
        
        # Create a scale without octave information
        scale_no_octave = Scale("C", ScaleType.MAJOR)  # No octave specified
        
        # Mock the Playback class to capture the notes being played
        with patch('chordelia.audio_playback.Playback') as mock_playback_class:
            mock_playback_instance = MagicMock()
            mock_playback_class.return_value.__enter__.return_value = mock_playback_instance
            
            # Call play_scale with explicit octave parameter
            play_scale(scale_no_octave, self.tempo, Duration("quarter"), octave=5)
            
            # Get the notes that were passed to play_sequence
            call_args = mock_playback_instance.play_sequence.call_args[0]
            played_notes = call_args[0]
            
            # All notes should be in octave 5 (the fallback)
            for i, playback_note in enumerate(played_notes):
                self.assertEqual(playback_note.note.octave, 5, f"Note {i} should be in octave 5")
    
    @pytest.mark.slow
    @patch('time.sleep', Mock())  # Speed up tests  
    def test_play_chord_function(self):
        """Test the play_chord convenience function."""
        from chordelia.audio_playback import play_chord

        chord = Chord.from_string("C")
        
        # Should not raise an exception
        play_chord(chord, self.tempo, Duration("whole"), octave=4)
        
        # Verify audio stream was used
        self.mock_sd.OutputStream.assert_called()
        self.mock_stream.start.assert_called()
    
    @pytest.mark.slow
    @patch('time.sleep', Mock())  # Speed up tests
    def test_play_melody_function(self):
        """Test the play_melody convenience function."""
        from chordelia.audio_playback import play_melody
        
        melody = [
            (Note("C4"), Duration("quarter")),
            (Note("D4"), Duration("quarter")),  
            (Note("E4"), Duration("half")),
        ]
        
        # Should not raise an exception
        play_melody(melody, self.tempo)
        
        # Verify audio stream was used
        self.mock_sd.OutputStream.assert_called()
        self.mock_stream.start.assert_called()
    
    def test_play_melody_requires_octaves(self):
        """Test that play_melody requires notes with octaves."""
        from chordelia.audio_playback import play_melody
        
        melody_no_octaves = [
            (Note("C"), Duration("quarter")),  # No octave
            (Note("D"), Duration("quarter")),  # No octave
        ]
        
        with self.assertRaises(ValueError):
            play_melody(melody_no_octaves, self.tempo)


class TestWaveformEnum(unittest.TestCase):
    """Test Waveform enumeration."""
    
    def test_waveform_values(self):
        """Test waveform enum values."""
        from chordelia.audio_playback import Waveform
        
        self.assertEqual(Waveform.SINE.value, "sine")
        self.assertEqual(Waveform.SQUARE.value, "square")
        self.assertEqual(Waveform.SAWTOOTH.value, "sawtooth")
        self.assertEqual(Waveform.TRIANGLE.value, "triangle")


class TestPlaybackErrorHandling(unittest.TestCase):
    """Test error handling in playback scenarios."""
    
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', False)
    def test_playback_unavailable_error(self):
        """Test error when audio dependencies are unavailable."""
        from chordelia.audio_playback import Playback, PlaybackNote
        from chordelia.rhythm import COMMON_TIME
        
        tempo = Tempo(120)
        with self.assertRaises(ImportError):
            playback = Playback(tempo, COMMON_TIME)
    
    @patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
    @patch('chordelia.audio_playback.sd')
    @patch('chordelia.audio_playback.np')
    def test_concurrent_playback_error(self, mock_np, mock_sd):
        """Test error when trying to play multiple sequences concurrently."""
        from chordelia.audio_playback import Playback, PlaybackNote
        from chordelia.rhythm import COMMON_TIME
        
        # Setup mocks
        mock_np.float32 = float
        mock_stream = Mock()
        mock_sd.OutputStream.return_value = mock_stream
        
        tempo = Tempo(120)
        playback = Playback(tempo, COMMON_TIME)
        
        notes = [PlaybackNote(Duration(0), Note("C4"), Duration("quarter"), 0.7)]
        
        # Mock the playing state
        playback._playing = True
        
        with self.assertRaises(RuntimeError):
            playback.play_sequence(notes)


class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world musical scenarios."""
    
    def setUp(self):
        # Mock audio components for testing
        self.patcher_sd = patch('chordelia.audio_playback.sd')
        self.patcher_np = patch('chordelia.audio_playback.np')
        self.patcher_available = patch('chordelia.audio_playback.AUDIO_AVAILABLE', True)
        
        self.mock_sd = self.patcher_sd.start()
        self.mock_np = self.patcher_np.start() 
        self.patcher_available.start()
        
        # Setup mocks
        self.mock_np.arange.return_value = []
        self.mock_np.sin.return_value = []
        self.mock_np.float32 = float
        
        self.mock_stream = Mock()
        self.mock_sd.OutputStream.return_value = self.mock_stream
        
    def tearDown(self):
        self.patcher_sd.stop()
        self.patcher_np.stop()
        self.patcher_available.stop()
    
    def test_chord_progression_timing(self):
        """Test playing a chord progression with correct timing."""
        from chordelia.audio_playback import Playback, PlaybackNote
        from chordelia.rhythm import COMMON_TIME
        from chordelia.chords import Chord
        
        # Simple I-V-vi-IV progression in C major
        progression = ["C", "G", "Am", "F"]
        tempo = Tempo(120)
        
        notes = []
        current_time = Duration(0)
        chord_duration = Duration("whole")
        
        for chord_name in progression:
            chord = Chord.from_string(chord_name)
            
            # Add each chord note
            for i, chord_note in enumerate(chord.notes):
                note = Note(chord_note.name, chord_note.accidental, 4 + i // 7)
                notes.append(PlaybackNote(
                    start_time=current_time,
                    note=note,
                    duration=chord_duration,
                    velocity=0.5
                ))
            
            current_time = current_time + chord_duration
        
        # Should create playback without errors
        playback = Playback(tempo, COMMON_TIME)
        
        # Test timing calculations
        total_duration_ms = playback._convert_to_milliseconds(current_time)
        expected_ms = 4 * 2000  # 4 whole notes at 120 BPM = 8 seconds
        self.assertEqual(total_duration_ms, expected_ms)
    
    def test_melody_with_varying_durations(self):
        """Test melody with different note durations.""" 
        from chordelia.audio_playback import Playback, PlaybackNote
        from chordelia.rhythm import COMMON_TIME, dotted
        
        # "Mary Had a Little Lamb" rhythm pattern
        melody_rhythm = [
            (Note("E4"), Duration("quarter")),
            (Note("D4"), Duration("quarter")),
            (Note("C4"), Duration("quarter")),
            (Note("D4"), Duration("quarter")),
            (Note("E4"), Duration("quarter")),
            (Note("E4"), Duration("quarter")),
            (Note("E4"), Duration("half")),
            (Note("D4"), Duration("quarter")),
            (Note("D4"), Duration("quarter")),
            (Note("D4"), Duration("half")),
        ]
        
        notes = []
        current_time = Duration(0)
        
        for note, duration in melody_rhythm:
            notes.append(PlaybackNote(
                start_time=current_time,
                note=note,
                duration=duration,
                velocity=0.7
            ))
            current_time = current_time + duration
        
        tempo = Tempo(120)
        playback = Playback(tempo, COMMON_TIME)
        
        # Calculate total duration - should be reasonable
        total_ms = playback._convert_to_milliseconds(current_time)
        self.assertGreater(total_ms, 0)
        self.assertLess(total_ms, 20000)  # Less than 20 seconds


if __name__ == '__main__':
    unittest.main()

