"""
MIDI File Module for Chordelia

This module provides functionality to read MIDI files and convert them
to sequences suitable for playback using Chordelia's audio system.

Features:
- Read MIDI files using the mido library
- Convert MIDI notes to PlaybackNote objects
- Extract tempo and time signature information
- Handle multiple     # Play using Chordelia's playback system
    print(f"🎵 Playing {midi.filepath.name} ({len(notes)} notes)")
    with Playback(midi.tempo, default_waveform=waveform) as playback:
        playback.play_sequence(notes, blocking=blocking)ks and channels
- Support for velocity mapping

Example:
    >>> from chordelia.midifile import MidiFile
    >>> from chordelia.audio_playback import AudioPlayer
    >>> 
    >>> # Load a MIDI file
    >>> midi = MidiFile("song.mid")
    >>> 
    >>> # Convert to playback sequence
    >>> notes = midi.to_playback_notes()
    >>> 
    >>> # Play using Chordelia's audio playback system
    >>> with AudioPlayer() as player:
    ...     player.play_sequence(notes, blocking=True)
"""

from typing import List, Optional, Dict, Tuple, Union
from pathlib import Path
import mido
from dataclasses import dataclass

# Import Chordelia components
from chordelia.notes import Note, NoteName, Accidental
from chordelia.rhythm import Tempo, Duration, TimeSignature
from chordelia.audio_playback import PlaybackNote, Waveform


@dataclass
class MidiTrackInfo:
    """Information about a MIDI track."""
    name: str
    channel: int
    instrument: int
    note_count: int


class MidiFile:
    """
    A class to read and process MIDI files for Chordelia playback.
    
    This class handles the conversion of MIDI data to Chordelia's
    musical representation, making it easy to play MIDI files
    using the audio playback system.
    """
    
    def __init__(self, filepath: Union[str, Path]):
        """
        Initialize MidiFile from a file path.
        
        Args:
            filepath: Path to the MIDI file
            
        Raises:
            FileNotFoundError: If the MIDI file doesn't exist
            ValueError: If the file is not a valid MIDI file
        """
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"MIDI file not found: {filepath}")
            
        try:
            self.midi_file = mido.MidiFile(str(self.filepath))
        except Exception as e:
            raise ValueError(f"Invalid MIDI file: {e}")
            
        # Extract basic information
        self._tempo = None
        self._time_signature = None
        self._tracks_info = []
        self._analyze_file()
    
    def _analyze_file(self):
        """Analyze the MIDI file to extract tempo, time signature, and track info."""
        # Default values
        tempo_bpm = 120  # Default MIDI tempo
        time_sig_numerator = 4
        time_sig_denominator = 4
        
        # Track information
        track_info = []
        
        for i, track in enumerate(self.midi_file.tracks):
            track_name = f"Track {i}"
            channel = 0
            instrument = 0
            note_count = 0
            
            for msg in track:
                if msg.type == 'set_tempo':
                    # Convert microseconds per beat to BPM
                    tempo_bpm = mido.tempo2bpm(msg.tempo)
                elif msg.type == 'time_signature':
                    time_sig_numerator = msg.numerator
                    time_sig_denominator = msg.denominator
                elif msg.type == 'track_name':
                    track_name = msg.name
                elif msg.type == 'program_change':
                    instrument = msg.program
                    channel = msg.channel
                elif msg.type == 'note_on' and msg.velocity > 0:
                    note_count += 1
                    if channel == 0:  # Update channel from first note
                        channel = msg.channel
            
            if note_count > 0:  # Only include tracks with notes
                track_info.append(MidiTrackInfo(
                    name=track_name,
                    channel=channel,
                    instrument=instrument,
                    note_count=note_count
                ))
        
        self._tempo = Tempo(tempo_bpm)
        self._time_signature = TimeSignature(time_sig_numerator, time_sig_denominator)
        self._tracks_info = track_info
    
    @property
    def tempo(self) -> Tempo:
        """Get the tempo of the MIDI file."""
        return self._tempo
    
    @property
    def time_signature(self) -> TimeSignature:
        """Get the time signature of the MIDI file."""
        return self._time_signature
    
    @property
    def tracks_info(self) -> List[MidiTrackInfo]:
        """Get information about all tracks in the MIDI file."""
        return self._tracks_info
    
    @property
    def duration_seconds(self) -> float:
        """Get the total duration of the MIDI file in seconds."""
        return self.midi_file.length
    
    def _midi_note_to_note(self, midi_note: int) -> Note:
        """
        Convert a MIDI note number to a Chordelia Note object.
        
        Args:
            midi_note: MIDI note number (0-127)
            
        Returns:
            Note object with proper name, accidental, and octave
        """
        # MIDI note 60 = C4 (middle C)
        # Each octave spans 12 semitones
        octave = (midi_note // 12) - 1  # MIDI octave offset
        semitone = midi_note % 12
        
        # Map semitones to note names (using sharps for black keys)
        note_mapping = [
            (NoteName.C, Accidental.NATURAL),      # 0
            (NoteName.C, Accidental.SHARP),        # 1
            (NoteName.D, Accidental.NATURAL),      # 2
            (NoteName.D, Accidental.SHARP),        # 3
            (NoteName.E, Accidental.NATURAL),      # 4
            (NoteName.F, Accidental.NATURAL),      # 5
            (NoteName.F, Accidental.SHARP),        # 6
            (NoteName.G, Accidental.NATURAL),      # 7
            (NoteName.G, Accidental.SHARP),        # 8
            (NoteName.A, Accidental.NATURAL),      # 9
            (NoteName.A, Accidental.SHARP),        # 10
            (NoteName.B, Accidental.NATURAL),      # 11
        ]
        
        note_name, accidental = note_mapping[semitone]
        return Note(note_name, accidental, octave)
    
    def to_playback_notes(self, 
                         track_indices: Optional[List[int]] = None,
                         waveform: Waveform = Waveform.SINE,
                         velocity_scale: float = 1.0) -> List[PlaybackNote]:
        """
        Convert MIDI file to a list of PlaybackNote objects.
        
        Args:
            track_indices: List of track indices to include (None = all tracks)
            waveform: Waveform to use for all notes
            velocity_scale: Scale factor for note velocities (0.0-1.0)
            
        Returns:
            List of PlaybackNote objects ready for playback
        """
        playback_notes = []
        
        # Select tracks to process
        if track_indices is None:
            tracks_to_process = enumerate(self.midi_file.tracks)
        else:
            tracks_to_process = [(i, self.midi_file.tracks[i]) 
                               for i in track_indices 
                               if i < len(self.midi_file.tracks)]
        
        for track_idx, track in tracks_to_process:
            # Track active notes (note_on without note_off)
            active_notes: Dict[int, Dict] = {}
            current_time = 0.0  # Time in seconds
            
            for msg in track:
                # Update current time
                current_time += mido.tick2second(msg.time, 
                                               self.midi_file.ticks_per_beat, 
                                               mido.bpm2tempo(self._tempo.bpm))
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Start a new note
                    note = self._midi_note_to_note(msg.note)
                    velocity = (msg.velocity / 127.0) * velocity_scale
                    
                    active_notes[msg.note] = {
                        'note': note,
                        'start_time': current_time,
                        'velocity': velocity,
                        'channel': msg.channel
                    }
                
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # End a note
                    if msg.note in active_notes:
                        note_info = active_notes[msg.note]
                        duration = current_time - note_info['start_time']
                        
                        # Create PlaybackNote
                        playback_note = PlaybackNote(
                            start_time=note_info['start_time'],
                            note=note_info['note'],
                            duration=duration,
                            velocity=note_info['velocity']
                        )
                        playback_notes.append(playback_note)
                        
                        # Remove from active notes
                        del active_notes[msg.note]
            
            # Handle any notes that didn't have explicit note_off events
            for note_info in active_notes.values():
                duration = current_time - note_info['start_time']
                if duration > 0:
                    playback_note = PlaybackNote(
                        start_time=note_info['start_time'],
                        note=note_info['note'],
                        duration=duration,
                        velocity=note_info['velocity']
                    )
                    playback_notes.append(playback_note)
        
        # Sort notes by start time
        playback_notes.sort(key=lambda n: n.start_time)
        return playback_notes
    
    def get_track_notes(self, track_index: int, 
                       waveform: Waveform = Waveform.SINE) -> List[PlaybackNote]:
        """
        Get PlaybackNote objects for a specific track.
        
        Args:
            track_index: Index of the track to extract
            waveform: Waveform to use for the notes
            
        Returns:
            List of PlaybackNote objects for the specified track
        """
        if track_index >= len(self.midi_file.tracks):
            raise IndexError(f"Track index {track_index} out of range")
            
        return self.to_playback_notes(track_indices=[track_index], waveform=waveform)
    
    def print_info(self):
        """Print information about the MIDI file."""
        print(f"📁 MIDI File: {self.filepath.name}")
        print(f"⏱️  Duration: {self.duration_seconds:.2f} seconds")
        print(f"🎵 Tempo: {self.tempo.bpm} BPM")
        print(f"📊 Time Signature: {self.time_signature}")
        print(f"🎼 Tracks: {len(self.tracks_info)}")
        print()
        
        for i, track in enumerate(self.tracks_info):
            print(f"  Track {i}: {track.name}")
            print(f"    🎹 Channel: {track.channel}")
            print(f"    🎺 Instrument: {track.instrument}")
            print(f"    🎵 Notes: {track.note_count}")
            print()


def load_midi_file(filepath: Union[str, Path]) -> MidiFile:
    """
    Convenience function to load a MIDI file.
    
    Args:
        filepath: Path to the MIDI file
        
    Returns:
        MidiFile object
    """
    return MidiFile(filepath)


def play_midi_file(filepath: Union[str, Path], 
                  track_indices: Optional[List[int]] = None,
                  waveform: Waveform = Waveform.SINE,
                  blocking: bool = True):
    """
    Convenience function to load and play a MIDI file.
    
    Args:
        filepath: Path to the MIDI file
        track_indices: List of track indices to play (None = all tracks)
        waveform: Waveform to use for playback
        blocking: Whether to block until playback is complete
    """
    from chordelia.audio_playback import Playback
    
    # Load MIDI file
    midi = MidiFile(filepath)
    
    # Convert to playback notes
    notes = midi.to_playback_notes(track_indices=track_indices, waveform=waveform)
    
    if not notes:
        print("No notes found in MIDI file")
        return
    
    # Play using Chordelia's playback system with specified performance mode
    print(f"🎵 Playing {midi.filepath.name} ({len(notes)} notes)")
    with Playback(midi.tempo, default_waveform=waveform) as playback:
        playback.play_sequence(notes, blocking=blocking)
