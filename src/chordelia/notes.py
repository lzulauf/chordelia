"""
Musical notes implementation with algorithmic pitch calculation.

This module provides classes for representing musical notes, including
natural notes, accidentals, enharmonic equivalents, and octave information.
All calculations are done algorithmically for efficiency.
"""

from enum import Enum
from typing import Optional, Union
import re
from functools import lru_cache
from chordelia.intervals import Interval, IntervalQuality

# Pre-compiled regex for faster note parsing
_NOTE_PATTERN = re.compile(r'^([A-G])(#{1,2}|b{1,2})?(\d+)?$')


@lru_cache(maxsize=256)
def _calculate_frequency(midi_number: int) -> float:
    """
    Calculate frequency from MIDI number with caching.
    
    Args:
        midi_number: MIDI note number (0-127)
        
    Returns:
        Frequency in Hz
    """
    # A4 (MIDI 69) = 440 Hz
    a4_midi = 69
    midi_diff = midi_number - a4_midi
    
    # Each semitone is a factor of 2^(1/12)
    return 440.0 * (2 ** (midi_diff / 12))


class NoteName(Enum):
    """Enumeration of natural note names."""
    C = 0
    D = 2
    E = 4
    F = 5
    G = 7
    A = 9
    B = 11
    
    @property
    def semitones_from_c(self) -> int:
        """Get semitones from C for this note name."""
        return self.value


# Master mapping of accidentals to their string symbols
# (defined before the Accidental class so it can be used in __str__)
_ACCIDENTAL_TO_SYMBOL = {
    # Will be populated after Accidental class is defined
}


class Accidental(Enum):
    """Enumeration of accidentals."""
    DOUBLE_FLAT = -2
    FLAT = -1
    NATURAL = 0
    SHARP = 1
    DOUBLE_SHARP = 2
    
    def __str__(self) -> str:
        """String representation of accidental."""
        return _ACCIDENTAL_TO_SYMBOL[self]


# Populate the symbols mapping now that Accidental enum is defined
_ACCIDENTAL_TO_SYMBOL.update({
    Accidental.DOUBLE_FLAT: "bb",
    Accidental.FLAT: "b", 
    Accidental.NATURAL: "",
    Accidental.SHARP: "#",
    Accidental.DOUBLE_SHARP: "##"
})

# Inverse mapping - string to enum (generated from accidental-to-symbol)
_SYMBOL_TO_ACCIDENTAL = {symbol: accidental for accidental, symbol in _ACCIDENTAL_TO_SYMBOL.items()}

# MIDI pitch class to note mappings with None for black keys (will be resolved to sharp/flat)
_PITCH_CLASS_TO_NOTE_BASE = [
    (NoteName.C, Accidental.NATURAL),    # 0
    (NoteName.C, None),                  # 1 - will become C# or Db
    (NoteName.D, Accidental.NATURAL),    # 2
    (NoteName.D, None),                  # 3 - will become D# or Eb
    (NoteName.E, Accidental.NATURAL),    # 4
    (NoteName.F, Accidental.NATURAL),    # 5
    (NoteName.F, None),                  # 6 - will become F# or Gb
    (NoteName.G, Accidental.NATURAL),    # 7
    (NoteName.G, None),                  # 8 - will become G# or Ab
    (NoteName.A, Accidental.NATURAL),    # 9
    (NoteName.A, None),                  # 10 - will become A# or Bb
    (NoteName.B, Accidental.NATURAL),    # 11
]


class Note:
    """
    Represents a musical note with optional octave information.
    
    This class is immutable for performance and safety. All operations that 
    modify note properties return new Note instances rather than modifying 
    the existing one.
    
    Supports natural notes, accidentals, enharmonic equivalents,
    and interval arithmetic using algorithmic approaches.
    
    Examples:
        Creating notes:
        >>> note = Note("C4")
        >>> note = Note(NoteName.C, Accidental.SHARP, 4)
        >>> note = Note.from_string("F#5")
        
        Copy-constructor API for modifications:
        >>> original = Note("C4")
        >>> with_octave = original.with_octave(5)      # C5
        >>> with_sharp = original.with_accidental("#") # C#4
        >>> with_name = original.with_name("D")        # D4
        >>> combined = original.with_(name="F", accidental="#", octave=5)  # F#5
        
        Fluent chaining:
        >>> result = Note("C").with_octave(4).with_accidental("#")  # C#4
        
        Removing octave information:
        >>> pitch_class_only = note.with_octave(None)  # C# (no octave)
        
        All methods preserve immutability - the original note is never modified.
    """
    
    __slots__ = ('_name', '_accidental', '_octave')
    
    def __init__(self, 
                 name: Union[NoteName, str], 
                 accidental: Union[Accidental, str, int] = Accidental.NATURAL,
                 octave: Optional[int] = None):
        """
        Initialize a new immutable note.
        
        Args:
            name: The note name (C, D, E, F, G, A, B)
            accidental: The accidental (natural, sharp, flat, etc.)
            octave: Optional octave number (4 = middle octave)
        """
        # Handle string input with complex note parsing
        if isinstance(name, str):
            # Handle simple note name like "C" or use from_string for complex ones
            if len(name) == 1 and name.upper() in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
                name = NoteName[name.upper()]
            else:
                # This is likely a complex note like "C#", use from_string
                # We need to parse it manually here since from_string creates a Note
                match = _NOTE_PATTERN.match(name.strip())
                if not match:
                    raise ValueError(f"Invalid note string: {name}")
                
                note_name = match.group(1)
                accidental_str = match.group(2) or ""
                octave_str = match.group(3)
                
                name = NoteName[note_name.upper()]
                if accidental == Accidental.NATURAL and accidental_str:  # Only override if not explicitly set
                    accidental = accidental_str
                if octave is None and octave_str:
                    octave = int(octave_str)
        
        # Convert accidental to enum if needed
        if isinstance(accidental, str):
            accidental = _SYMBOL_TO_ACCIDENTAL[accidental]
        elif isinstance(accidental, int):
            accidental = Accidental(accidental)
        
        # Set the attributes directly - rely on Python conventions for "private" attributes
        self._name = name
        self._accidental = accidental
        self._octave = octave
    
    @property
    def name(self) -> NoteName:
        """The note name (C, D, E, F, G, A, B)."""
        return self._name
    
    @property
    def accidental(self) -> Accidental:
        """The accidental (natural, sharp, flat, etc.)."""
        return self._accidental
    
    @property
    def octave(self) -> Optional[int]:
        """The octave number (4 = middle octave)."""
        return self._octave
    
    def with_octave(self, octave: Optional[int]) -> 'Note':
        """
        Create a copy of this note with a different octave.
        
        Args:
            octave: The new octave number (or None to remove octave)
            
        Returns:
            A new Note with the same name and accidental but different octave
        """
        return Note(self._name, self._accidental, octave)
    
    def with_accidental(self, accidental: Union[Accidental, str, int]) -> 'Note':
        """
        Create a copy of this note with a different accidental.
        
        Args:
            accidental: The new accidental
            
        Returns:
            A new Note with the same name and octave but different accidental
        """
        return Note(self._name, accidental, self._octave)
    
    def with_name(self, name: Union[NoteName, str]) -> 'Note':
        """
        Create a copy of this note with a different name.
        
        Args:
            name: The new note name
            
        Returns:
            A new Note with the same accidental and octave but different name
        """
        return Note(name, self._accidental, self._octave)
    
    def with_(self, 
              name: Optional[Union[NoteName, str]] = None,
              accidental: Optional[Union[Accidental, str, int]] = None, 
              octave: Optional[int] = ...) -> 'Note':
        """
        Create a copy of this note with any combination of modified attributes.
        
        Args:
            name: New note name (defaults to current)
            accidental: New accidental (defaults to current)  
            octave: New octave (defaults to current, use explicit None to remove octave)
            
        Returns:
            A new Note with the specified modifications
            
        Examples:
            >>> note = Note("C4")
            >>> note.with_(octave=5)  # C5
            >>> note.with_(accidental=Accidental.SHARP)  # C#4
            >>> note.with_(name=NoteName.D, octave=3)  # D3
            >>> note.with_(octave=None)  # C (no octave)
        """
        # Use current values as defaults, but allow explicit None for octave
        new_name = name if name is not None else self._name
        new_accidental = accidental if accidental is not None else self._accidental
        new_octave = self._octave if octave is ... else octave
        
        return Note(new_name, new_accidental, new_octave)
    
    @classmethod
    @lru_cache(maxsize=256)
    def from_string(cls, note_string: str) -> 'Note':
        """
        Create a note from a string representation with optimized parsing.
        
        Args:
            note_string: String like "C", "F#", "Bb4", "C##5"
            
        Returns:
            A Note object
        """
        # Use pre-compiled regex for faster matching
        match = _NOTE_PATTERN.match(note_string.strip())
        
        if not match:
            raise ValueError(f"Invalid note string: {note_string}")
        
        note_name = match.group(1)
        accidental_str = match.group(2) or ""
        octave_str = match.group(3)
        
        octave = int(octave_str) if octave_str else None
        
        return cls(note_name, accidental_str, octave)
    
# Cached property since pitch class never changes for a note
    @lru_cache(maxsize=1)
    def _calculate_pitch_class(self) -> int:
        """Calculate pitch class with caching."""
        return (self.name.value + self.accidental.value) % 12
    
    @property
    def pitch_class(self) -> int:
        """
        Get the pitch class (0-11) of this note.
        
        Returns:
            Integer from 0-11 representing the pitch class
        """
        return self._calculate_pitch_class()
    
    @property
    def midi_number(self) -> Optional[int]:
        """
        Get the MIDI note number if octave is specified.
        
        Returns:
            MIDI note number (0-127) or None if no octave
        """
        if self.octave is None:
            return None
        
        # MIDI note 60 = C4 (middle C)
        # Each octave spans 12 semitones
        base_midi = (self.octave + 1) * 12  # C0 = MIDI 12
        return base_midi + self.pitch_class
    
    @classmethod
    def from_midi_number(cls, midi_number: int, prefer_sharps: bool = True) -> 'Note':
        """
        Create a note from a MIDI note number.
        
        Args:
            midi_number: MIDI note number (0-127)
            prefer_sharps: Whether to prefer sharps over flats for accidentals
            
        Returns:
            A Note object with octave information
        """
        if not 0 <= midi_number <= 127:
            raise ValueError(f"MIDI number must be 0-127, got {midi_number}")
        
        octave = (midi_number // 12) - 1
        pitch_class = midi_number % 12
        
        # Get base note name and accidental from unified mapping
        note_name, accidental = _PITCH_CLASS_TO_NOTE_BASE[pitch_class]
        
        # Resolve None accidentals to sharp or flat based on preference
        if accidental is None:
            if prefer_sharps:
                accidental = Accidental.SHARP
            else:
                # For flats, we need to adjust the note name to the next higher note
                note_names = list(NoteName)
                current_index = note_names.index(note_name)
                next_index = (current_index + 1) % len(note_names)
                note_name = note_names[next_index]
                accidental = Accidental.FLAT
        return cls(note_name, accidental, octave)
    
    def transpose(self, interval: Interval) -> 'Note':
        """
        Transpose this note by an interval.
        
        Args:
            interval: The interval to transpose by
            
        Returns:
            A new Note object representing the transposed note
        """
        # Get the actual semitones to transpose (could be negative)
        semitones = getattr(interval, '_original_semitones', interval.semitones)
        
        # Calculate the new pitch class
        if self.octave is not None:
            new_midi = self.midi_number + semitones
            # Handle MIDI overflow/underflow
            if new_midi < 0:
                new_midi = 0
            elif new_midi > 127:
                new_midi = 127
            
            # Use enharmonic spelling based on interval direction
            prefer_sharps = semitones >= 0
            base_note = Note.from_midi_number(new_midi, prefer_sharps)
        else:
            new_pitch_class = (self.pitch_class + semitones) % 12
            # Create a temporary note to get proper enharmonic spelling
            temp_midi = 60 + new_pitch_class  # Use middle octave for calculation
            prefer_sharps = semitones >= 0
            base_note = Note.from_midi_number(temp_midi, prefer_sharps)
            base_note = base_note.with_octave(None)  # Remove octave
        
        # Adjust enharmonic spelling based on the interval
        return self._get_enharmonic_for_interval(base_note, interval)
    
    def _get_enharmonic_for_interval(self, target_note: 'Note', interval: Interval) -> 'Note':
        """
        Get the correct enharmonic spelling for a note based on an interval.
        
        This ensures that intervals maintain their theoretical letter-name distance.
        """
        # Calculate expected letter name based on interval number
        note_names = [NoteName.C, NoteName.D, NoteName.E, NoteName.F, 
                     NoteName.G, NoteName.A, NoteName.B]
        
        current_index = note_names.index(self.name)
        expected_index = (current_index + interval.number - 1) % 7
        expected_name = note_names[expected_index]
        
        # If the target note already has the correct letter name, return it
        if target_note.name == expected_name:
            return target_note
        
        # Otherwise, find the enharmonic equivalent with the correct letter name
        target_pitch_class = target_note.pitch_class
        expected_natural_pitch_class = expected_name.semitones_from_c
        
        # Calculate required accidental
        accidental_semitones = target_pitch_class - expected_natural_pitch_class
        
        # Handle wrap-around (e.g., C to B requires going down)
        if accidental_semitones > 6:
            accidental_semitones -= 12
        elif accidental_semitones < -6:
            accidental_semitones += 12
        
        # Create accidental if valid
        try:
            required_accidental = Accidental(accidental_semitones)
            return target_note.with_(name=expected_name, accidental=required_accidental)
        except ValueError:
            # If we can't create the required accidental, return the original
            return target_note
    
    def interval_to(self, other: 'Note') -> Interval:
        """
        Calculate the interval from this note to another note.
        
        Args:
            other: The target note
            
        Returns:
            The interval between the notes
        """
        if self.octave is not None and other.octave is not None:
            semitone_difference = other.midi_number - self.midi_number
        else:
            # For notes without octave, calculate within one octave
            self_pc = self.pitch_class
            other_pc = other.pitch_class
            semitone_difference = other_pc - self_pc
            if semitone_difference < 0:
                semitone_difference += 12
        
        return Interval.from_semitones(semitone_difference, prefer_simple=False)
    
    def enharmonic_equivalents(self) -> list['Note']:
        """
        Get all enharmonic equivalents of this note.
        
        Returns:
            List of enharmonically equivalent notes
        """
        equivalents = []
        target_pitch_class = self.pitch_class
        
        # Check all possible note names and accidentals
        for note_name in NoteName:
            for accidental in Accidental:
                test_note = Note(note_name, accidental, self.octave)
                if (test_note.pitch_class == target_pitch_class and 
                    not (test_note.name == self.name and test_note.accidental == self.accidental)):
                    equivalents.append(test_note)
        
        return equivalents
    
    def is_enharmonic_with(self, other: 'Note') -> bool:
        """
        Check if this note is enharmonically equivalent to another.
        
        Args:
            other: The note to compare with
            
        Returns:
            True if enharmonically equivalent
        """
        return self.pitch_class == other.pitch_class
    
    @property
    def frequency(self) -> Optional[float]:
        """
        Get the frequency in Hz if octave is specified.
        Uses A4 = 440 Hz as reference.
        
        Returns:
            Frequency in Hz or None if no octave
        """
        if self.octave is None:
            return None
        
        return _calculate_frequency(self.midi_number)
    
    def __str__(self) -> str:
        """String representation of the note."""
        octave_str = str(self.octave) if self.octave is not None else ""
        return f"{self.name.name}{self.accidental}{octave_str}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Note({self.name.name}, {self.accidental.name}, {self.octave})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another note."""
        if not isinstance(other, Note):
            return False
        return (self.name == other.name and 
                self.accidental == other.accidental and 
                self.octave == other.octave)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((self.name, self.accidental, self.octave))
    
    def __lt__(self, other: 'Note') -> bool:
        """Less than comparison for sorting."""
        if not isinstance(other, Note):
            return NotImplemented
        
        # If both have octaves, compare MIDI numbers
        if self.octave is not None and other.octave is not None:
            return self.midi_number < other.midi_number
        
        # If neither has octave, compare pitch classes
        if self.octave is None and other.octave is None:
            return self.pitch_class < other.pitch_class
        
        # Mixed comparison - notes without octave come before notes with octave
        if self.octave is None and other.octave is not None:
            return True
        if self.octave is not None and other.octave is None:
            return False
        
        # This shouldn't be reached, but just in case
        return False
    
    def __le__(self, other: 'Note') -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __gt__(self, other: 'Note') -> bool:
        """Greater than comparison."""
        return not self <= other
    
    def __ge__(self, other: 'Note') -> bool:
        """Greater than or equal comparison."""
        return not self < other


# Common note constants for convenience
C = Note(NoteName.C)
C_SHARP = Note(NoteName.C, Accidental.SHARP)
D_FLAT = Note(NoteName.D, Accidental.FLAT)
D = Note(NoteName.D)
D_SHARP = Note(NoteName.D, Accidental.SHARP)
E_FLAT = Note(NoteName.E, Accidental.FLAT)
E = Note(NoteName.E)
F = Note(NoteName.F)
F_SHARP = Note(NoteName.F, Accidental.SHARP)
G_FLAT = Note(NoteName.G, Accidental.FLAT)
G = Note(NoteName.G)
G_SHARP = Note(NoteName.G, Accidental.SHARP)
A_FLAT = Note(NoteName.A, Accidental.FLAT)
A = Note(NoteName.A)
A_SHARP = Note(NoteName.A, Accidental.SHARP)
B_FLAT = Note(NoteName.B, Accidental.FLAT)
B = Note(NoteName.B)
