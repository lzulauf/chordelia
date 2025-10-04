"""
Musical scales implementation using interval patterns.

This module provides classes for representing scales and their constituent notes,
with proper enharmonic spelling based on music theory principles.
"""

from enum import Enum
from typing import List, Optional, Union, Tuple, Iterable
from functools import lru_cache, cached_property
from chordelia.notes import Note, NoteName, Accidental
from chordelia.intervals import Interval, IntervalQuality


class ScaleType(Enum):
    """Enumeration of common scale types with their interval patterns."""
    
    # Major scale and modes
    MAJOR = "major"
    IONIAN = "ionian"  # Same as major
    DORIAN = "dorian"
    PHRYGIAN = "phrygian"
    LYDIAN = "lydian"
    MIXOLYDIAN = "mixolydian"
    AEOLIAN = "aeolian"  # Same as natural minor
    LOCRIAN = "locrian"
    
    # Minor scales
    NATURAL_MINOR = "natural_minor"
    HARMONIC_MINOR = "harmonic_minor"
    MELODIC_MINOR = "melodic_minor"
    
    # Other common scales
    CHROMATIC = "chromatic"
    WHOLE_TONE = "whole_tone"
    DIMINISHED = "diminished"
    PENTATONIC_MAJOR = "pentatonic_major"
    PENTATONIC_MINOR = "pentatonic_minor"
    BLUES = "blues"


class Scale:
    """
    Represents a musical scale with proper enharmonic spelling.
    
    This class is immutable for performance and safety. Scale modifications 
    like transposition and mode generation return new Scale instances.
    
    Uses interval patterns to generate scale degrees algorithmically,
    ensuring correct enharmonic spelling based on music theory principles.
    
    Examples:
        Creating scales:
        >>> scale = Scale("C", ScaleType.MAJOR)
        >>> scale = Scale("F#", "harmonic_minor")
        >>> scale = Scale(Note("Bb"), ScaleType.PENTATONIC_MAJOR)
        
        Scale operations (return new instances):
        >>> f_major = Scale("F", ScaleType.MAJOR)
        >>> d_dorian = c_major.get_mode(2)  # D dorian mode
        >>> transposed = scale.transpose(Interval(IntervalQuality.PERFECT, 4))
        
        All methods preserve immutability - the original scale is never modified.
    """
    
    __slots__ = ('_root', '_scale_type', '__dict__')
    
    # Scale interval patterns (in semitones from root)
    SCALE_PATTERNS = {
        ScaleType.MAJOR: [0, 2, 4, 5, 7, 9, 11],
        ScaleType.IONIAN: [0, 2, 4, 5, 7, 9, 11],
        ScaleType.DORIAN: [0, 2, 3, 5, 7, 9, 10],
        ScaleType.PHRYGIAN: [0, 1, 3, 5, 7, 8, 10],
        ScaleType.LYDIAN: [0, 2, 4, 6, 7, 9, 11],
        ScaleType.MIXOLYDIAN: [0, 2, 4, 5, 7, 9, 10],
        ScaleType.AEOLIAN: [0, 2, 3, 5, 7, 8, 10],
        ScaleType.NATURAL_MINOR: [0, 2, 3, 5, 7, 8, 10],
        ScaleType.LOCRIAN: [0, 1, 3, 5, 6, 8, 10],
        ScaleType.HARMONIC_MINOR: [0, 2, 3, 5, 7, 8, 11],
        ScaleType.MELODIC_MINOR: [0, 2, 3, 5, 7, 9, 11],
        ScaleType.CHROMATIC: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        ScaleType.WHOLE_TONE: [0, 2, 4, 6, 8, 10],
        ScaleType.DIMINISHED: [0, 2, 3, 5, 6, 8, 9, 11],
        ScaleType.PENTATONIC_MAJOR: [0, 2, 4, 7, 9],
        ScaleType.PENTATONIC_MINOR: [0, 3, 5, 7, 10],
        ScaleType.BLUES: [0, 3, 5, 6, 7, 10],
    }
    
    def __init__(self, root: Union[Note, str], scale_type: Union[ScaleType, str]):
        """
        Initialize an immutable scale.
        
        Args:
            root: The root note of the scale
            scale_type: The type of scale to construct
        """
        if isinstance(root, str):
            root = Note.from_string(root)
        
        if isinstance(scale_type, str):
            # Try to match string to ScaleType enum
            scale_type_map = {st.value: st for st in ScaleType}
            if scale_type.lower() in scale_type_map:
                scale_type = scale_type_map[scale_type.lower()]
            else:
                raise ValueError(f"Unknown scale type: {scale_type}")
        
        # Set attributes directly - rely on Python conventions for immutability
        self._root = root
        self._scale_type = scale_type
    
    @property
    def root(self) -> Note:
        """The root note of the scale."""
        return self._root
    
    @property
    def scale_type(self) -> ScaleType:
        """The type of scale."""
        return self._scale_type
    
    @property
    def pattern(self) -> Tuple[int, ...]:
        """Get the semitone pattern for this scale type."""
        return tuple(self.SCALE_PATTERNS[self.scale_type])
    
    @cached_property
    def notes(self) -> Tuple[Note, ...]:
        """
        Get the notes in this scale with proper enharmonic spelling.
        
        Returns:
            Tuple of Note objects representing the scale degrees
        """
        return self._calculate_notes()

    def with_octave(self, octave: int):
        """Return a new Scale instance with all notes set to the specified octave."""
        new_root = self.root.with_octave(octave)
        return Scale(new_root, self.scale_type)
    
    def _calculate_notes(self) -> Tuple[Note, ...]:
        """
        Calculate the notes in the scale with proper enharmonic spelling.
        
        Uses music theory principles to ensure correct letter names are used
        for each scale degree.
        """
        notes = []
        pattern = self.pattern
        
        # For certain scale types, use direct pitch class to note mapping
        # instead of sequential letter names
        if self.scale_type in [ScaleType.PENTATONIC_MAJOR, ScaleType.PENTATONIC_MINOR, 
                              ScaleType.BLUES, ScaleType.CHROMATIC, ScaleType.WHOLE_TONE,
                              ScaleType.DIMINISHED]:
            return self._calculate_notes_by_pitch_class()
        
        # Get the basic note names in order starting from root
        note_names = [NoteName.C, NoteName.D, NoteName.E, NoteName.F, 
                     NoteName.G, NoteName.A, NoteName.B]
        

        
        root_index = note_names.index(self.root.name)
        
        for i, semitones in enumerate(pattern):
            # Calculate the expected note name for this scale degree
            expected_name_index = (root_index + i) % 7
            expected_name = note_names[expected_name_index]
            
            # Calculate the target pitch class
            if self.root.octave is not None:
                # For notes with octave information, calculate exact MIDI number
                target_midi = self.root.midi_number + semitones
                
                if target_midi >= 128:  # Handle MIDI overflow
                    target_midi = 127
                
                # Derive octave directly from MIDI number for correct octave crossing
                target_octave = (target_midi // 12) - 1  # MIDI octave formula
                target_pitch_class = target_midi % 12
            else:
                # For notes without octave, work with pitch classes
                target_pitch_class = (self.root.pitch_class + semitones) % 12
                target_octave = None
            
            # Calculate the required accidental for the expected note name
            expected_natural_pc = expected_name.semitones_from_c
            accidental_semitones = target_pitch_class - expected_natural_pc
            
            # Handle wrap-around cases
            if accidental_semitones > 6:
                accidental_semitones -= 12
            elif accidental_semitones < -6:
                accidental_semitones += 12
            
            # Create the note with proper accidental
            try:
                # Only use reasonable accidentals (single sharp/flat)
                if -2 <= accidental_semitones <= 2:
                    accidental = Accidental(accidental_semitones)
                    note = Note(expected_name).with_(accidental=accidental, octave=target_octave)
                    notes.append(note)
                else:
                    raise ValueError("Too many accidentals needed")
            except ValueError:
                # If we can't create the required accidental (too many sharps/flats),
                # fall back to enharmonic equivalent
                if self.root.octave is not None:
                    note = Note.from_midi_number(target_midi)
                else:
                    # Create a temporary note to get enharmonic spelling
                    temp_midi = 60 + target_pitch_class
                    temp_note = Note.from_midi_number(temp_midi)
                    note = temp_note.with_octave(target_octave)
                notes.append(note)
        
        return tuple(notes)
    
    def _calculate_notes_by_pitch_class(self) -> Tuple[Note, ...]:
        """
        Calculate notes using pitch class mapping for non-diatonic scales.
        """
        pattern = self.pattern
        prefer_sharps = self._should_prefer_sharps()
        
        def _create_note_for_semitones(semitones: int) -> Note:
            if self.root.octave is not None:
                target_midi = self.root.midi_number + semitones
                if target_midi >= 128:
                    target_midi = 127
                return Note.from_midi_number(target_midi, prefer_sharps)
            else:
                target_pitch_class = (self.root.pitch_class + semitones) % 12
                temp_midi = 60 + target_pitch_class
                temp_note = Note.from_midi_number(temp_midi, prefer_sharps)
                return temp_note.with_octave(None)
        
        return tuple(_create_note_for_semitones(semitones) for semitones in pattern)
    
    def _should_prefer_sharps(self) -> bool:
        """
        Determine whether to prefer sharps or flats based on the root note.
        """
        # If root has sharps, prefer sharps; if root has flats, prefer flats
        if self.root.accidental == Accidental.SHARP or self.root.accidental == Accidental.DOUBLE_SHARP:
            return True
        elif self.root.accidental == Accidental.FLAT or self.root.accidental == Accidental.DOUBLE_FLAT:
            return False
        
        # For natural roots, use key signature logic
        sharp_keys = [NoteName.G, NoteName.D, NoteName.A, NoteName.E, NoteName.B]
        flat_keys = [NoteName.F]
        
        if self.root.name in sharp_keys:
            return True
        elif self.root.name in flat_keys:
            return False
        else:
            return True  # Default to sharps
    
    def degree(self, degree_number: int) -> Note:
        """
        Get a specific scale degree.
        
        Args:
            degree_number: The scale degree (1-based, 1 = root)
            
        Returns:
            The note representing that scale degree
        """
        if not 1 <= degree_number <= len(self.notes):
            raise ValueError(f"Scale degree must be 1-{len(self.notes)}, got {degree_number}")
        
        return self.notes[degree_number - 1]
    
    def get_mode(self, degree: int) -> 'Scale':
        """
        Get a mode of this scale starting from the specified degree.
        
        Args:
            degree: The scale degree to start the mode from (1-based)
            
        Returns:
            A new Scale object representing the mode
        """
        if not 1 <= degree <= len(self.notes):
            raise ValueError(f"Degree must be 1-{len(self.notes)}, got {degree}")
        
        # Get the new root note
        new_root = self.degree(degree)
        
        # Calculate the new pattern by rotating the original pattern
        original_pattern = self.pattern
        degree_index = degree - 1
        
        # Rotate pattern and normalize to start from 0
        rotated_pattern = original_pattern[degree_index:] + original_pattern[:degree_index]
        root_offset = rotated_pattern[0]
        normalized_pattern = []
        
        for interval in rotated_pattern:
            new_interval = interval - root_offset
            # Handle negative intervals by adding an octave
            if new_interval < 0:
                new_interval += 12
            normalized_pattern.append(new_interval)
        
        # Create a custom scale with this pattern
        return CustomScale(new_root, normalized_pattern)
    
    def transpose(self, interval: Interval) -> 'Scale':
        """
        Transpose this scale by an interval.
        
        Args:
            interval: The interval to transpose by
            
        Returns:
            A new Scale object transposed by the interval
        """
        new_root = self.root.transpose(interval)
        return Scale(new_root, self.scale_type)
    
    def contains_note(self, note: Note) -> bool:
        """
        Check if a note is in this scale (ignoring octave).
        
        Args:
            note: The note to check
            
        Returns:
            True if the note is in the scale
        """
        scale_pitch_classes = {n.pitch_class for n in self.notes}
        return note.pitch_class in scale_pitch_classes
    
    def get_chord_scale_degrees(self, chord_root: Note) -> Optional[int]:
        """
        Get the scale degree for a given note.
        
        Args:
            chord_root: The note to find the degree for
            
        Returns:
            The scale degree (1-based) or None if not in scale
        """
        for i, scale_note in enumerate(self.notes):
            if scale_note.pitch_class == chord_root.pitch_class:
                return i + 1
        return None
    
    @property
    def name(self) -> str:
        """Get the full name of the scale."""
        scale_names = {
            ScaleType.MAJOR: "Major",
            ScaleType.IONIAN: "Ionian",
            ScaleType.DORIAN: "Dorian", 
            ScaleType.PHRYGIAN: "Phrygian",
            ScaleType.LYDIAN: "Lydian",
            ScaleType.MIXOLYDIAN: "Mixolydian",
            ScaleType.AEOLIAN: "Aeolian",
            ScaleType.NATURAL_MINOR: "Natural Minor",
            ScaleType.LOCRIAN: "Locrian",
            ScaleType.HARMONIC_MINOR: "Harmonic Minor",
            ScaleType.MELODIC_MINOR: "Melodic Minor",
            ScaleType.CHROMATIC: "Chromatic",
            ScaleType.WHOLE_TONE: "Whole Tone",
            ScaleType.DIMINISHED: "Diminished",
            ScaleType.PENTATONIC_MAJOR: "Major Pentatonic",
            ScaleType.PENTATONIC_MINOR: "Minor Pentatonic",
            ScaleType.BLUES: "Blues",
        }
        
        scale_name = scale_names.get(self.scale_type, self.scale_type.value.title())
        return f"{self.root} {scale_name}"
    
    def __str__(self) -> str:
        """String representation of the scale."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        notes_str = ", ".join(str(note) for note in self.notes)
        return f"Scale({self.root}, {self.scale_type.value}) - Notes: [{notes_str}]"
    
    def __eq__(self, other) -> bool:
        """Check equality with another scale."""
        if not isinstance(other, Scale):
            return False
        return (self.root == other.root and 
                self.scale_type == other.scale_type)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((self.root, self.scale_type))


class CustomScale(Scale):
    """
    A scale with a custom interval pattern.
    
    Useful for creating scales that don't fit the predefined types
    or for modes derived from other scales.
    """
    __slots__ = ('_custom_pattern',)  # Add slots for CustomScale-specific attributes
    
    def __init__(self, root: Union[Note, str], pattern: Iterable[int]):
        """
        Initialize a custom scale.
        
        Args:
            root: The root note of the scale
            pattern: Iterable of semitone intervals from the root (can be list, tuple, etc.)
        """
        # Initialize parent class with None scale_type for custom scales
        super().__init__(root, None)
        
        # Set custom scale specific attributes
        self._custom_pattern = tuple(pattern)  # Store as immutable tuple

    @property
    def pattern(self) -> Tuple[int, ...]:
        """Get the custom semitone pattern."""
        return self._custom_pattern
    
    @property
    def name(self) -> str:
        """Get the name of the custom scale."""
        pattern_str = "-".join(str(interval) for interval in self._custom_pattern)
        return f"{self.root} Custom Scale ({pattern_str})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another scale."""
        if not isinstance(other, CustomScale):
            return False
        return (self.root == other.root and 
                self._custom_pattern == other._custom_pattern)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((self.root, self._custom_pattern))


# Common scale factory functions for convenience
def major_scale(root: Union[Note, str]) -> Scale:
    """Create a major scale."""
    return Scale(root, ScaleType.MAJOR)

def minor_scale(root: Union[Note, str]) -> Scale:
    """Create a natural minor scale."""
    return Scale(root, ScaleType.NATURAL_MINOR)

def harmonic_minor_scale(root: Union[Note, str]) -> Scale:
    """Create a harmonic minor scale."""
    return Scale(root, ScaleType.HARMONIC_MINOR)

def melodic_minor_scale(root: Union[Note, str]) -> Scale:
    """Create a melodic minor scale."""
    return Scale(root, ScaleType.MELODIC_MINOR)

def dorian_scale(root: Union[Note, str]) -> Scale:
    """Create a dorian scale."""
    return Scale(root, ScaleType.DORIAN)

def mixolydian_scale(root: Union[Note, str]) -> Scale:
    """Create a mixolydian scale."""
    return Scale(root, ScaleType.MIXOLYDIAN)

def pentatonic_major_scale(root: Union[Note, str]) -> Scale:
    """Create a major pentatonic scale."""
    return Scale(root, ScaleType.PENTATONIC_MAJOR)

def pentatonic_minor_scale(root: Union[Note, str]) -> Scale:
    """Create a minor pentatonic scale."""
    return Scale(root, ScaleType.PENTATONIC_MINOR)

def blues_scale(root: Union[Note, str]) -> Scale:
    """Create a blues scale."""
    return Scale(root, ScaleType.BLUES)
