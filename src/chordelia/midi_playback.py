"""
MIDI playback functionality for chords and melodies.

This module provides MIDI output capabilities that intelligently manage
note on/off events when chords change, only sending events for notes
that have actually changed.
"""

from typing import List, Set, Optional, Union, Dict
import time
from threading import Lock, Timer
from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.rhythm import Duration, Tempo


try:
    import mido
    _MIDI_AVAILABLE = True
except ImportError:
    _MIDI_AVAILABLE = False
    mido = None


class MIDIPlaybackNote:
    """
    Represents a note for MIDI playback with timing information.
    
    Similar to PlaybackNote but optimized for MIDI output with
    note numbers and velocities.
    """
    
    def __init__(self, note: Note, velocity: int = 64, duration: Optional[Duration] = None):
        """
        Initialize a MIDI playback note.
        
        Args:
            note: Note object (must have octave information)
            velocity: MIDI velocity (0-127, default 64)
            duration: Duration to hold the note (optional)
        """
        if note.octave is None:
            raise ValueError("Note must have octave information for MIDI playback")
        
        if not 0 <= velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")
        
        self.note = note
        self.velocity = velocity
        self.duration = duration
        self.midi_number = note.midi_number
    
    def __repr__(self) -> str:
        return f"MIDIPlaybackNote({self.note}, velocity={self.velocity}, midi={self.midi_number})"


class MIDIChordPlayer:
    """
    Intelligent MIDI chord player that manages note on/off events efficiently.
    
    This class tracks the currently playing notes and only sends MIDI events
    for notes that have actually changed when updating to a new chord.
    """
    
    def __init__(self, 
                 output_name: Optional[str] = None, 
                 channel: int = 0,
                 base_octave: int = 4,
                 default_velocity: int = 64):
        """
        Initialize MIDI chord player.
        
        Args:
            output_name: Name of MIDI output port (None for default)
            channel: MIDI channel (0-15, default 0)
            base_octave: Default octave for chords without octave info
            default_velocity: Default MIDI velocity (0-127)
        """
        if not _MIDI_AVAILABLE:
            raise ImportError("MIDI playback requires 'mido' package. Install with: pip install mido")
        
        if not 0 <= channel <= 15:
            raise ValueError("MIDI channel must be between 0 and 15")
        
        if not 0 <= default_velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")
        
        self.channel = channel
        self.base_octave = base_octave
        self.default_velocity = default_velocity
        
        # State tracking
        self._current_notes: Set[int] = set()  # MIDI note numbers currently playing
        self._lock = Lock()
        self._output_port = None
        self._stop_timers: List[Timer] = []
        
        # Initialize MIDI output
        self._setup_midi_output(output_name)
    
    def _setup_midi_output(self, output_name: Optional[str]):
        """Set up MIDI output port."""
        try:
            if output_name:
                self._output_port = mido.open_output(output_name)
            else:
                # Use first available output port
                available_ports = mido.get_output_names()
                if available_ports:
                    self._output_port = mido.open_output(available_ports[0])
                else:
                    # Create virtual port if no hardware ports available
                    self._output_port = mido.open_output('Chordelia Virtual Out', virtual=True)
                    
        except Exception as e:
            print(f"Warning: Could not open MIDI output: {e}")
            print("Creating virtual MIDI port...")
            try:
                self._output_port = mido.open_output('Chordelia Virtual Out', virtual=True)
            except Exception as e2:
                raise RuntimeError(f"Failed to create MIDI output: {e2}")
    
    def update_chord(self, chord: Optional[Chord]):
        """
        Update the currently playing chord with intelligent note management.
        
        Only sends MIDI events for notes that have actually changed:
        - Note On for new notes
        - Note Off for removed notes  
        - No events for notes that remain the same
        
        Args:
            chord: New chord to play (None to stop all notes)
        """
        with self._lock:
            if chord is None:
                # Stop all currently playing notes
                self._stop_all_notes()
                return
            
            # Get MIDI note numbers for the new chord
            new_notes = self._chord_to_midi_numbers(chord)
            
            # Calculate which notes to stop and start
            notes_to_stop = self._current_notes - new_notes
            notes_to_start = new_notes - self._current_notes
            
            # Stop notes that are no longer needed
            for midi_note in notes_to_stop:
                self._send_note_off(midi_note)
            
            # Start new notes
            for midi_note in notes_to_start:
                self._send_note_on(midi_note, self.default_velocity)
            
            # Update current state
            self._current_notes = new_notes.copy()
    
    def _chord_to_midi_numbers(self, chord: Chord) -> Set[int]:
        """Convert chord to set of MIDI note numbers."""
        midi_numbers = set()
        
        for note in chord.notes:
            if note.octave is not None:
                midi_numbers.add(note.midi_number)
            else:
                # Use base octave for notes without octave information
                note_with_octave = note.with_octave(self.base_octave)
                midi_numbers.add(note_with_octave.midi_number)
        
        return midi_numbers
    
    def _send_note_on(self, midi_note: int, velocity: int):
        """Send MIDI note on event."""
        if self._output_port:
            msg = mido.Message('note_on', channel=self.channel, note=midi_note, velocity=velocity)
            self._output_port.send(msg)
    
    def _send_note_off(self, midi_note: int):
        """Send MIDI note off event."""
        if self._output_port:
            msg = mido.Message('note_off', channel=self.channel, note=midi_note, velocity=0)
            self._output_port.send(msg)
    
    def _stop_all_notes(self):
        """Stop all currently playing notes."""
        for midi_note in self._current_notes:
            self._send_note_off(midi_note)
        self._current_notes.clear()
    
    def play_chord_with_duration(self, chord: Chord, duration: Duration, tempo: Tempo = Tempo(120)):
        """
        Play a chord for a specific duration then stop.
        
        Args:
            chord: Chord to play
            duration: How long to hold the chord
            tempo: Tempo for duration calculation
        """
        # Start the chord
        self.update_chord(chord)
        
        # Schedule stop
        from chordelia.rhythm import TimeSignature
        time_sig = TimeSignature(4, 4)  # Default 4/4 time
        duration_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0
        stop_timer = Timer(duration_seconds, lambda: self.update_chord(None))
        
        # Track timer for cleanup
        self._stop_timers.append(stop_timer)
        stop_timer.start()
    
    def play_note(self, note: Note, velocity: int = None, duration: Duration = None, tempo: Tempo = Tempo(120)):
        """
        Play a single note.
        
        Args:
            note: Note to play (must have octave)
            velocity: MIDI velocity (uses default if None)
            duration: Duration to hold note (infinite if None)
            tempo: Tempo for duration calculation
        """
        if note.octave is None:
            note = note.with_octave(self.base_octave)
        
        velocity = velocity if velocity is not None else self.default_velocity
        midi_note = note.midi_number
        
        with self._lock:
            self._send_note_on(midi_note, velocity)
            
            if duration:
                # Schedule note off
                from chordelia.rhythm import TimeSignature
                time_sig = TimeSignature(4, 4)  # Default 4/4 time
                duration_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0
                stop_timer = Timer(duration_seconds, lambda: self._send_note_off(midi_note))
                self._stop_timers.append(stop_timer)
                stop_timer.start()
    
    def set_velocity(self, velocity: int):
        """Set default velocity for new notes."""
        if not 0 <= velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")
        self.default_velocity = velocity
    
    def set_channel(self, channel: int):
        """Set MIDI channel."""
        if not 0 <= channel <= 15:
            raise ValueError("MIDI channel must be between 0 and 15")
        
        with self._lock:
            # Stop all notes on current channel
            self._stop_all_notes()
            # Switch to new channel
            self.channel = channel
    
    def stop(self):
        """Stop all notes and clean up resources."""
        with self._lock:
            # Cancel all pending timers
            for timer in self._stop_timers:
                timer.cancel()
            self._stop_timers.clear()
            
            # Stop all notes
            self._stop_all_notes()
            
            # Close MIDI port
            if self._output_port:
                self._output_port.close()
                self._output_port = None
    
    @property
    def current_notes(self) -> Set[int]:
        """Get currently playing MIDI note numbers (read-only)."""
        with self._lock:
            return self._current_notes.copy()
    
    @property 
    def is_connected(self) -> bool:
        """Check if MIDI output is connected."""
        return self._output_port is not None and not self._output_port.closed
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.stop()
        except:
            pass


# Convenience functions similar to audio_playback
def play_chord(chord: Chord, 
               tempo: Tempo = Tempo(120), 
               duration: Duration = None,
               channel: int = 0,
               velocity: int = 64,
               output_name: Optional[str] = None) -> None:
    """
    Play a chord via MIDI with all notes starting simultaneously.
    
    Args:
        chord: Chord object to play
        tempo: Playback tempo
        duration: Duration to hold the chord (default: whole note)
        channel: MIDI channel (0-15)
        velocity: MIDI velocity (0-127)
        output_name: MIDI output port name (None for default)
    """
    if not _MIDI_AVAILABLE:
        raise ImportError("MIDI playback requires 'mido' package. Install with: pip install mido")
    
    from chordelia.rhythm import whole_note
    
    if duration is None:
        duration = whole_note()
    
    # Create temporary player
    player = MIDIChordPlayer(
        output_name=output_name,
        channel=channel,
        default_velocity=velocity
    )
    
    try:
        player.play_chord_with_duration(chord, duration, tempo)
        
        # Wait for chord to finish
        from chordelia.rhythm import TimeSignature
        time_sig = TimeSignature(4, 4)  # Default 4/4 time
        duration_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0
        time.sleep(duration_seconds)
        
    finally:
        player.stop()


def play_melody(notes: List[Union[Note, MIDIPlaybackNote]], 
                tempo: Tempo = Tempo(120),
                channel: int = 0,
                default_velocity: int = 64,
                output_name: Optional[str] = None) -> None:
    """
    Play a sequence of notes as a melody.
    
    Args:
        notes: List of Note or MIDIPlaybackNote objects
        tempo: Playback tempo
        channel: MIDI channel (0-15)  
        default_velocity: Default velocity for Note objects
        output_name: MIDI output port name (None for default)
    """
    if not _MIDI_AVAILABLE:
        raise ImportError("MIDI playback requires 'mido' package. Install with: pip install mido")
    
    from chordelia.rhythm import quarter_note
    
    # Create temporary player
    player = MIDIChordPlayer(
        output_name=output_name,
        channel=channel,
        default_velocity=default_velocity
    )
    
    try:
        for note_item in notes:
            if isinstance(note_item, MIDIPlaybackNote):
                note = note_item.note
                velocity = note_item.velocity
                duration = note_item.duration or quarter_note()
            else:
                # Plain Note object
                note = note_item
                velocity = default_velocity
                duration = quarter_note()
            
            player.play_note(note, velocity, duration, tempo)
            
            # Wait for note duration
            from chordelia.rhythm import TimeSignature
            time_sig = TimeSignature(4, 4)  # Default 4/4 time
            duration_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0
            time.sleep(duration_seconds)
            
    finally:
        player.stop()


def get_midi_ports() -> Dict[str, List[str]]:
    """
    Get available MIDI input and output ports.
    
    Returns:
        Dictionary with 'input' and 'output' lists of port names
    """
    if not _MIDI_AVAILABLE:
        return {'input': [], 'output': [], 'error': 'mido not installed'}
    
    try:
        return {
            'input': mido.get_input_names(),
            'output': mido.get_output_names()
        }
    except Exception as e:
        return {'input': [], 'output': [], 'error': str(e)}


# Export check function
def is_midi_available() -> bool:
    """Check if MIDI functionality is available."""
    return _MIDI_AVAILABLE
