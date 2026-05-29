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

from typing import Any, List, Optional, Dict, Union
from pathlib import Path
import mido
from dataclasses import dataclass
from fractions import Fraction

# Import Chordelia components
from chordelia.notes import Note, NoteName, Accidental
from chordelia.rhythm import Tempo, Duration, TimeSignature
from chordelia.score import Score, ScoreEvent, ScoreMetadata
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
    
    def __init__(
        self,
        source: Union[str, Path, Score, Any],
        *,
        tempo: int = 120,
        time_signature: tuple[int, int] = (4, 4),
        key_signature: Optional[str] = None,
        ppq: int = 480,
    ):
        """
        Initialize MidiFile from Score/Sequenceable source or a legacy file path.
        
        Args:
            source: Score/sequenceable source or a legacy MIDI file path.
            tempo: Tempo used when source is sequenceable.
            time_signature: Time signature used when source is sequenceable.
            key_signature: Optional key signature used when source is sequenceable.
            ppq: Pulses per quarter note used when source is sequenceable.
            
        Raises:
            FileNotFoundError: If a file-path source doesn't exist.
            ValueError: If a file-path source is not a valid MIDI file.
        """
        self.filepath: Optional[Path] = None
        self.midi_file: Optional[mido.MidiFile] = None
        self.score: Optional[Score] = None
        self._tempo: Tempo = Tempo(tempo)
        self._time_signature: TimeSignature = TimeSignature(*time_signature)
        self._tracks_info: List[MidiTrackInfo] = []

        if isinstance(source, (str, Path)):
            self._initialize_from_file(Path(source))
            return

        if isinstance(source, Score):
            self.score = source
        else:
            self.score = Score.from_sequenceable(
                source,
                tempo=tempo,
                time_signature=time_signature,
                key_signature=key_signature,
                ppq=ppq,
            )

        self._tempo = Tempo(self.score.metadata.tempo)
        self._time_signature = TimeSignature(*self.score.metadata.time_signature)
        self._tracks_info = self._track_info_from_score(self.score)

    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> 'MidiFile':
        """Load a MIDI file from disk into a MidiFile wrapper."""
        return cls(filepath)

    @classmethod
    def score_to_file(cls, score: Score, file_path: Union[str, Path]) -> Path:
        """Write a score to a MIDI file path and return the resulting path."""
        if not isinstance(score, Score):
            raise TypeError(f"score must be a Score instance, got {type(score).__name__}")

        midi_wrapper = cls(score)
        return midi_wrapper.to_file(file_path)

    @classmethod
    def score_from_file(cls, file_path: Union[str, Path]) -> Score:
        """Parse a MIDI file into a normalized Score."""
        filepath = Path(file_path)
        if not filepath.exists():
            raise FileNotFoundError(f"MIDI file not found: {file_path}")

        try:
            midi = mido.MidiFile(str(filepath))
        except Exception as e:
            raise ValueError(f"Invalid MIDI file: {e}")

        tempo_bpm = 120
        time_sig_numerator = 4
        time_sig_denominator = 4
        key_signature = None

        events: list[ScoreEvent] = []

        for track in midi.tracks:
            absolute_tick = 0
            active_notes: dict[tuple[int, int], list[tuple[int, int]]] = {}

            for msg in track:
                absolute_tick += msg.time

                if msg.type == 'set_tempo':
                    tempo_bpm = int(round(mido.tempo2bpm(msg.tempo)))
                    continue
                if msg.type == 'time_signature':
                    time_sig_numerator = msg.numerator
                    time_sig_denominator = msg.denominator
                    continue
                if msg.type == 'key_signature':
                    key_signature = msg.key
                    continue

                if msg.type == 'note_on' and msg.velocity > 0:
                    key = (msg.channel, msg.note)
                    active_notes.setdefault(key, []).append((absolute_tick, msg.velocity))
                    continue

                if msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    key = (msg.channel, msg.note)
                    if key not in active_notes or not active_notes[key]:
                        continue

                    start_tick, start_velocity = active_notes[key].pop(0)
                    if not active_notes[key]:
                        del active_notes[key]

                    duration_ticks = max(1, absolute_tick - start_tick)
                    beat = Duration.from_beats(Fraction(start_tick, midi.ticks_per_beat), None)
                    duration = Duration.from_beats(Fraction(duration_ticks, midi.ticks_per_beat), None)

                    events.append(
                        ScoreEvent(
                            beat=beat,
                            duration=duration,
                            pitches=(msg.note,),
                            velocity=start_velocity,
                            channel=msg.channel,
                        )
                    )

        metadata = ScoreMetadata(
            tempo=max(1, tempo_bpm),
            time_signature=(time_sig_numerator, time_sig_denominator),
            key_signature=key_signature,
            ppq=midi.ticks_per_beat,
        )
        return Score(source=filepath, metadata=metadata, events=tuple(events))

    def to_file(self, file_path: Union[str, Path]) -> Path:
        """Write this MidiFile wrapper to disk and return the resulting path."""
        output_path = Path(file_path)

        if self.score is not None:
            midi = self._mido_from_score(self.score)
            midi.save(str(output_path))
            return output_path

        if self.midi_file is not None:
            self.midi_file.save(str(output_path))
            return output_path

        raise ValueError("MidiFile has no score or source MIDI data to write")

    def _initialize_from_file(self, filepath: Path) -> None:
        """Initialize wrapper state from an on-disk MIDI file."""
        self.filepath = filepath
        if not self.filepath.exists():
            raise FileNotFoundError(f"MIDI file not found: {filepath}")
            
        try:
            self.midi_file = mido.MidiFile(str(self.filepath))
        except Exception as e:
            raise ValueError(f"Invalid MIDI file: {e}")

        self._analyze_file()
        self.score = self.score_from_file(self.filepath)

    def _track_info_from_score(self, score: Score) -> List[MidiTrackInfo]:
        """Derive track summary info for score-backed wrapper instances."""
        if not score.events:
            return []

        channels = sorted({event.channel for event in score.events})
        return [
            MidiTrackInfo(
                name="Score Track",
                channel=channel,
                instrument=0,
                note_count=sum(
                    len(event.pitches)
                    for event in score.events
                    if event.channel == channel
                ),
            )
            for channel in channels
        ]

    def _duration_to_ticks(self, duration: Duration, *, tempo_bpm: int, ppq: int) -> int:
        """Convert beat/time Duration values into MIDI ticks."""
        if duration.mode == "seconds":
            seconds = float(duration.as_seconds())
            return int(round(seconds * (tempo_bpm / 60.0) * ppq))
        beats = float(duration.as_beats())
        return int(round(beats * ppq))

    def _duration_to_seconds(self, duration: Duration, *, tempo_bpm: int) -> float:
        """Convert beat/time Duration values into wall-clock seconds."""
        if duration.mode == "seconds":
            return float(duration.as_seconds())
        beats = float(duration.as_beats())
        return beats * 60.0 / float(tempo_bpm)

    def _mido_from_score(self, score: Score) -> mido.MidiFile:
        """Build a mido.MidiFile instance from normalized score events."""
        midi = mido.MidiFile(ticks_per_beat=score.metadata.ppq)
        track = mido.MidiTrack()
        midi.tracks.append(track)

        track.append(
            mido.MetaMessage(
                'set_tempo',
                tempo=mido.bpm2tempo(score.metadata.tempo),
                time=0,
            )
        )
        numerator, denominator = score.metadata.time_signature
        track.append(
            mido.MetaMessage(
                'time_signature',
                numerator=numerator,
                denominator=denominator,
                time=0,
            )
        )
        if score.metadata.key_signature is not None:
            track.append(
                mido.MetaMessage(
                    'key_signature',
                    key=score.metadata.key_signature,
                    time=0,
                )
            )

        scheduled_messages: list[tuple[int, int, int, mido.Message]] = []

        for event in score.events:
            start_tick = self._duration_to_ticks(
                event.beat,
                tempo_bpm=score.metadata.tempo,
                ppq=score.metadata.ppq,
            )
            duration_ticks = max(
                1,
                self._duration_to_ticks(
                    event.duration,
                    tempo_bpm=score.metadata.tempo,
                    ppq=score.metadata.ppq,
                ),
            )
            end_tick = start_tick + duration_ticks

            for pitch in event.pitches:
                scheduled_messages.append(
                    (
                        start_tick,
                        1,
                        pitch,
                        mido.Message(
                            'note_on',
                            note=pitch,
                            velocity=event.velocity,
                            channel=event.channel,
                        ),
                    )
                )
                scheduled_messages.append(
                    (
                        end_tick,
                        0,
                        pitch,
                        mido.Message(
                            'note_off',
                            note=pitch,
                            velocity=0,
                            channel=event.channel,
                        ),
                    )
                )

        scheduled_messages.sort(key=lambda item: (item[0], item[1], item[2]))

        last_tick = 0
        for absolute_tick, _order, _pitch, message in scheduled_messages:
            delta = absolute_tick - last_tick
            track.append(message.copy(time=delta))
            last_tick = absolute_tick

        track.append(mido.MetaMessage('end_of_track', time=0))
        return midi
    
    def _analyze_file(self):
        """Analyze the MIDI file to extract tempo, time signature, and track info."""
        if self.midi_file is None:
            raise ValueError("No MIDI file is loaded")

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
        if self.midi_file is not None:
            return self.midi_file.length

        if self.score is None or not self.score.events:
            return 0.0

        tempo_bpm = self.score.metadata.tempo
        return max(
            self._duration_to_seconds(event.beat, tempo_bpm=tempo_bpm)
            + self._duration_to_seconds(event.duration, tempo_bpm=tempo_bpm)
            for event in self.score.events
        )
    
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
        if self.midi_file is None:
            if self.score is None:
                raise ValueError("MidiFile has no MIDI data or score source to convert")
            return self._score_to_playback_notes(velocity_scale=velocity_scale)

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

    def _score_to_playback_notes(self, *, velocity_scale: float) -> List[PlaybackNote]:
        """Convert score-backed state into playback notes without a source MIDI file."""
        assert self.score is not None

        playback_notes: list[PlaybackNote] = []
        tempo_bpm = self.score.metadata.tempo

        for event in self.score.events:
            start_time = self._duration_to_seconds(event.beat, tempo_bpm=tempo_bpm)
            duration = self._duration_to_seconds(event.duration, tempo_bpm=tempo_bpm)
            velocity = (event.velocity / 127.0) * velocity_scale

            for pitch in event.pitches:
                note = self._midi_note_to_note(pitch)
                playback_notes.append(
                    PlaybackNote(
                        start_time=start_time,
                        note=note,
                        duration=duration,
                        velocity=velocity,
                    )
                )

        playback_notes.sort(key=lambda note: note.start_time)
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
        if self.midi_file is None:
            if track_index != 0:
                raise IndexError("Score-backed MidiFile exposes only a synthetic track 0")
            return self.to_playback_notes(waveform=waveform)

        if track_index >= len(self.midi_file.tracks):
            raise IndexError(f"Track index {track_index} out of range")
            
        return self.to_playback_notes(track_indices=[track_index], waveform=waveform)
    
    def print_info(self):
        """Print information about the MIDI file."""
        source_name = self.filepath.name if self.filepath is not None else "<score-source>"
        print(f"📁 MIDI File: {source_name}")
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
    return MidiFile.load_from_file(filepath)


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
