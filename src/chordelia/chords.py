"""
Musical chords implementation with parsing and proper enharmonic spelling.

This module provides classes for representing chords, including const    def __init__(self, 
                 root: Union[Note, str],
                 quality: Union[ChordQuality, str] = ChordQuality.MAJOR,
                 extensions: Optional[Iterable[Union[ChordExtension, int, str]]] = None,
                 additions: Optional[Iterable[Union[int, str]]] = None,
                 omissions: Optional[Iterable[Union[int, str]]] = None,
                 bass_note: Optional[Union[Note, str]] = None,
                 inversion: Optional[int] = None,
                 notes: Optional[Iterable[Union[Note, str]]] = None):from parts, string parsing, inversions, and extensions with proper enharmonic
spelling based on underlying scales.
"""

from enum import Enum
from typing import Iterable, List, Optional, Union, Dict, Tuple
import re
from functools import lru_cache, cached_property
from chordelia.notes import Note, NoteName, Accidental
from chordelia.intervals import Interval, IntervalQuality
from chordelia.scales import Scale, ScaleType

# Pre-compiled regex patterns for faster parsing
_ROOT_PATTERN = re.compile(r'^([A-G][#b]*)')
_CHORD_PATTERNS_COMPILED = {
    'maj': re.compile(r'maj(?=\d|$)'),
    'min': re.compile(r'min(?=\d|$)'),
    'dim': re.compile(r'dim(?=\d|$)'), 
    'aug': re.compile(r'aug(?=\d|$)'),
    'sus2': re.compile(r'sus2'),
    'sus4': re.compile(r'sus4'),
    'sus': re.compile(r'sus(?!\d)'),
    'numbers': re.compile(r'\d+'),
    'parens': re.compile(r'\(([^)]+)\)')
}




class ChordQuality(Enum):
    """Enumeration of basic chord qualities."""
    MAJOR = "major"
    MINOR = "minor"
    DIMINISHED = "diminished"
    AUGMENTED = "augmented"
    SUSPENDED_2 = "sus2"
    SUSPENDED_4 = "sus4"
    POWER = "power"  # Just root and fifth


class ChordExtension(Enum):
    """Enumeration of chord extensions with semitone values."""
    SEVENTH = ("7", 10)         # (extension_string, semitones_from_root)
    MAJOR_SEVENTH = ("maj7", 11)
    NINTH = ("9", 14)
    MAJOR_NINTH = ("maj9", 14)
    ELEVENTH = ("11", 17)
    THIRTEENTH = ("13", 21)
    
    def __init__(self, extension_str, semitones):
        self.extension_str = extension_str
        self.semitones = semitones
    
    @classmethod
    def from_string(cls, extension_str: str):
        """Get ChordExtension from string."""
        for ext in cls:
            if ext.extension_str == extension_str:
                return ext
        return None
    
    @classmethod 
    def get_semitones(cls, extension_str: str) -> int:
        """Get semitones for extension string."""
        ext = cls.from_string(extension_str)
        return ext.semitones if ext else None


# Quality hash table with all variants for O(1) lookup
_QUALITY_HASH = {
    "": ChordQuality.MAJOR,
    "major": ChordQuality.MAJOR,
    "maj": ChordQuality.MAJOR,
    "M": ChordQuality.MAJOR,
    "minor": ChordQuality.MINOR,
    "min": ChordQuality.MINOR,
    "m": ChordQuality.MINOR,
    "-": ChordQuality.MINOR,
    "diminished": ChordQuality.DIMINISHED,
    "dim": ChordQuality.DIMINISHED,
    "°": ChordQuality.DIMINISHED,
    "augmented": ChordQuality.AUGMENTED,
    "aug": ChordQuality.AUGMENTED,
    "+": ChordQuality.AUGMENTED,
    "sus2": ChordQuality.SUSPENDED_2,
    "sus4": ChordQuality.SUSPENDED_4,
    "sus": ChordQuality.SUSPENDED_4,
    "power": ChordQuality.POWER,
    "5": ChordQuality.POWER,
}

# Extension semitones are now handled by ChordExtension.get_semitones()

# Standard chord patterns (semitones from root) - tuples for immutability and speed
_CHORD_INTERVALS = {
    ChordQuality.MAJOR: (0, 4, 7),
    ChordQuality.MINOR: (0, 3, 7),
    ChordQuality.DIMINISHED: (0, 3, 6),
    ChordQuality.AUGMENTED: (0, 4, 8),
    ChordQuality.SUSPENDED_2: (0, 2, 7),
    ChordQuality.SUSPENDED_4: (0, 5, 7),
    ChordQuality.POWER: (0, 7),
}


class Chord:
    """
    Represents a musical chord with proper enharmonic spelling.
    
    This class is immutable for performance and safety. All operations that 
    modify chord properties return new Chord instances rather than modifying 
    the existing one.
    
    Supports construction from parts or string parsing, inversions,
    extensions, and additions with correct enharmonic names based
    on the underlying scale context.
    
    Examples:
        Creating chords:
        >>> chord = Chord("C", ChordQuality.MAJOR)
        >>> chord = Chord.from_string("Dm7")
        >>> chord = Chord("F", "minor", ["7"], bass_note="A")
        
        Copy-constructor API for modifications:
        >>> c_major = Chord("C", ChordQuality.MAJOR)
        >>> c_minor = c_major.with_quality(ChordQuality.MINOR)     # Cm
        >>> c_maj7 = c_major.with_extension("maj7")               # Cmaj7
        >>> c_slash_e = c_major.with_bass("E")                    # C/E
        >>> f_major = c_major.with_root("F")                      # F
        >>> first_inv = c_major.with_inversion(1)                # C/E (first inversion)
        
        Fluent chaining:
        >>> complex_chord = Chord("C").with_quality("minor").with_extension("7").with_bass("Bb")  # Cm7/Bb
        
        Combined modifications:
        >>> chord.with_(root="F#", quality="minor", extensions=["7", "9"])  # F#m7add9
        
        All methods preserve immutability - the original chord is never modified.
    """
    
    __slots__ = ('_root', '_quality', '_extensions', '_additions', '_omissions', '_bass_note', '_inversion', '_custom_notes', '__dict__')
    
    # Extension intervals (in semitones from root) - derived from enum semitone values
    EXTENSION_INTERVALS = {ext: ext.semitones for ext in ChordExtension}
    
    def __init__(self, 
                 root: Union[Note, str],
                 quality: Union[ChordQuality, str] = ChordQuality.MAJOR,
                 extensions: Optional[Iterable[Union[ChordExtension, int, str]]] = None,
                 additions: Optional[Iterable[Union[int, str]]] = None,
                 omissions: Optional[Iterable[Union[int, str]]] = None,
                 bass_note: Optional[Union[Note, str]] = None,
                 inversion: Optional[int] = None,
                 notes: Optional[Iterable[Union[Note, str]]] = None):
        """
        Initialize an immutable chord.
        
        Args:
            root: The root note of the chord
            quality: The basic chord quality (major, minor, etc.)
            extensions: Iterable of extensions (7, 9, 11, 13, etc.) - can be list, tuple, set, etc.
            additions: Iterable of added notes (add9, add11, etc.) - can be list, tuple, set, etc.
            omissions: Iterable of omitted chord tones (no3, no5, etc.) - can be list, tuple, set, etc.
            bass_note: Bass note for slash chords
            inversion: Inversion number (1 = first inversion, etc.)
            notes: If provided, creates a chord with exactly these notes (overrides other parameters)
        """
        if isinstance(root, str):
            root = Note.from_string(root)
        
        if isinstance(quality, str):
            quality = _QUALITY_HASH.get(quality.lower(), ChordQuality.MAJOR)
        
        # Convert extensions, additions, omissions to tuples for immutability
        extensions = tuple(extensions or [])
        additions = tuple(additions or [])
        omissions = tuple(omissions or [])
        
        bass_note = Note.from_string(bass_note) if isinstance(bass_note, str) else bass_note
        
        # Handle custom notes parameter
        if notes is not None:
            # Convert notes to Note objects
            note_list = []
            for note in notes:
                if isinstance(note, str):
                    note_list.append(Note.from_string(note))
                else:
                    note_list.append(note)
            
            if not note_list:
                raise ValueError("At least one note must be provided")
            
            # Use first note as root if not already a Note object
            if not isinstance(root, Note):
                root = note_list[0] if note_list else Note.from_string(root)
            
            self._custom_notes = tuple(note_list)
        else:
            self._custom_notes = None
        
        # Set attributes directly - rely on Python conventions for immutability
        self._root = root
        self._quality = quality
        self._extensions = extensions
        self._additions = additions
        self._omissions = omissions
        self._bass_note = bass_note
        self._inversion = inversion

    
    @property
    def root(self) -> Note:
        """The root note of the chord."""
        return self._root
    
    @property
    def quality(self) -> ChordQuality:
        """The basic chord quality (major, minor, etc.)."""
        return self._quality
    
    @property
    def extensions(self) -> Tuple[Union[ChordExtension, int, str], ...]:
        """Tuple of chord extensions."""
        return self._extensions
    
    @property
    def additions(self) -> Tuple[Union[int, str], ...]:
        """Tuple of added chord tones."""
        return self._additions
    
    @property
    def omissions(self) -> Tuple[Union[int, str], ...]:
        """Tuple of omitted chord tones."""
        return self._omissions
    
    @property
    def bass_note(self) -> Optional[Note]:
        """Bass note for slash chords."""
        return self._bass_note
    
    @property
    def inversion(self) -> Optional[int]:
        """Inversion number (1 = first inversion, etc.)."""
        return self._inversion
    
    def with_root(self, root: Union[Note, str]) -> 'Chord':
        """
        Create a copy of this chord with a different root note.
        
        Args:
            root: The new root note
            
        Returns:
            A new Chord with the same properties but different root
        """
        return Chord(root, self._quality, self._extensions, self._additions, 
                    self._omissions, self._bass_note, self._inversion)
    
    def with_quality(self, quality: Union[ChordQuality, str]) -> 'Chord':
        """
        Create a copy of this chord with a different quality.
        
        Args:
            quality: The new chord quality
            
        Returns:
            A new Chord with the same properties but different quality
        """
        return Chord(self._root, quality, self._extensions, self._additions,
                    self._omissions, self._bass_note, self._inversion)
    
    def with_extension(self, extension: Union[ChordExtension, int, str]) -> 'Chord':
        """
        Create a copy of this chord with an added extension.
        
        Args:
            extension: The extension to add
            
        Returns:
            A new Chord with the extension added
        """
        new_extensions = list(self._extensions) + [extension]
        return Chord(self._root, self._quality, new_extensions, self._additions,
                    self._omissions, self._bass_note, self._inversion)
    
    def with_extensions(self, extensions: Iterable[Union[ChordExtension, int, str]]) -> 'Chord':
        """
        Create a copy of this chord with different extensions.
        
        Args:
            extensions: The new iterable of extensions (list, tuple, set, etc.)
            
        Returns:
            A new Chord with the specified extensions
        """
        return Chord(self._root, self._quality, extensions, self._additions,
                    self._omissions, self._bass_note, self._inversion)
    
    def with_bass(self, bass_note: Union[Note, str, None]) -> 'Chord':
        """
        Create a copy of this chord with a different bass note.
        
        Args:
            bass_note: The new bass note (or None to remove)
            
        Returns:
            A new Chord with the specified bass note
        """
        return Chord(self._root, self._quality, self._extensions, self._additions,
                    self._omissions, bass_note, self._inversion)
    
    def with_inversion(self, inversion: Optional[int]) -> 'Chord':
        """
        Create a copy of this chord with a different inversion.
        
        Args:
            inversion: The new inversion number (or None for root position)
            
        Returns:
            A new Chord with the specified inversion
        """
        return Chord(self._root, self._quality, self._extensions, self._additions,
                    self._omissions, self._bass_note, inversion)
    
    def with_(self,
              root: Optional[Union[Note, str]] = None,
              quality: Optional[Union[ChordQuality, str]] = None,
              extensions: Optional[Iterable[Union[ChordExtension, int, str]]] = None,
              additions: Optional[Iterable[Union[int, str]]] = None,
              omissions: Optional[Iterable[Union[int, str]]] = None,
              bass_note: Optional[Union[Note, str, None]] = ...,
              inversion: Optional[int] = ...) -> 'Chord':
        """
        Create a copy of this chord with any combination of modified attributes.
        
        Args:
            root: New root note (defaults to current)
            quality: New chord quality (defaults to current)
            extensions: New extensions iterable (defaults to current) - can be list, tuple, set, etc.
            additions: New additions iterable (defaults to current) - can be list, tuple, set, etc.
            omissions: New omissions iterable (defaults to current) - can be list, tuple, set, etc.
            bass_note: New bass note (defaults to current, use explicit None to remove)
            inversion: New inversion (defaults to current, use explicit None to remove)
            
        Returns:
            A new Chord with the specified modifications
            
        Examples:
            >>> chord = Chord("C")
            >>> chord.with_(quality="minor")  # Cm
            >>> chord.with_(root="F", extensions=["7"])  # F7
            >>> chord.with_(bass_note="E")  # C/E
            >>> chord.with_(bass_note=None)  # Remove bass note
        """
        # Use current values as defaults, but allow explicit None/... for optional fields
        new_root = root if root is not None else self._root
        new_quality = quality if quality is not None else self._quality
        new_extensions = extensions if extensions is not None else self._extensions
        new_additions = additions if additions is not None else self._additions
        new_omissions = omissions if omissions is not None else self._omissions
        new_bass_note = self._bass_note if bass_note is ... else bass_note
        new_inversion = self._inversion if inversion is ... else inversion
        
        return Chord(new_root, new_quality, new_extensions, new_additions,
                    new_omissions, new_bass_note, new_inversion)
    
    @classmethod
    @lru_cache(maxsize=256)
    def from_string(cls, chord_string: str) -> 'Chord':
        """
        Parse a chord from string notation with optimized regex parsing.
        
        Supports formats like:
        - C, Cmaj, CM
        - Cm, Cmin, C-
        - C7, Cmaj7, CM7
        - C(add9), C(add2)
        - C/E (slash chord)
        - Csus4, Csus2
        - Cdim, C°, Caug, C+
        
        Args:
            chord_string: String representation of the chord
            
        Returns:
            A Chord object
        """
        chord_string = chord_string.strip()
        
        # Handle slash chords (C/E)
        bass_note = None
        if '/' in chord_string:
            chord_part, bass_part = chord_string.split('/', 1)
            chord_string = chord_part.strip()
            bass_note = bass_part.strip()
        
        # Extract root note using pre-compiled regex
        root_match = _ROOT_PATTERN.match(chord_string)
        if not root_match:
            raise ValueError(f"Invalid chord string: {chord_string}")
        
        root_str = root_match.group(1)
        remaining = chord_string[len(root_str):]
        
        # Initialize parsing variables
        quality = ChordQuality.MAJOR
        extensions = []
        additions = []
        omissions = []
        is_major_extension = False
        
        # Fast quality detection using hash table
        remaining_lower = remaining.lower()
        
        # Check for quality markers in order of specificity
        if remaining_lower.startswith('maj'):
            quality = ChordQuality.MAJOR
            is_major_extension = True
            remaining = remaining[3:]
        elif remaining_lower.startswith('min'):
            quality = ChordQuality.MINOR
            remaining = remaining[3:]
        elif remaining_lower.startswith('dim'):
            quality = ChordQuality.DIMINISHED
            remaining = remaining[3:]
        elif remaining_lower.startswith('aug'):
            quality = ChordQuality.AUGMENTED
            remaining = remaining[3:]
        elif remaining_lower.startswith('sus2'):
            quality = ChordQuality.SUSPENDED_2
            remaining = remaining[4:]
        elif remaining_lower.startswith('sus4'):
            quality = ChordQuality.SUSPENDED_4
            remaining = remaining[4:]
        elif remaining_lower.startswith('sus'):
            quality = ChordQuality.SUSPENDED_4
            remaining = remaining[3:]
        elif remaining and remaining[0] in 'm-':
            quality = ChordQuality.MINOR
            remaining = remaining[1:]
        elif remaining and remaining[0] == 'M':
            quality = ChordQuality.MAJOR
            remaining = remaining[1:]
        elif remaining and remaining[0] == '°':
            quality = ChordQuality.DIMINISHED
            remaining = remaining[1:]
        elif remaining and remaining[0] == '+':
            quality = ChordQuality.AUGMENTED
            remaining = remaining[1:]
        elif remaining and remaining[0] == '5':
            quality = ChordQuality.POWER
            remaining = remaining[1:]
        
        # Extract numbers using pre-compiled regex
        for match in _CHORD_PATTERNS_COMPILED['numbers'].finditer(remaining):
            num = int(match.group())
            
            # Use hash table for fast extension lookup
            if ChordExtension.get_semitones(str(num)) is not None:
                if num == 7:
                    extensions.append(ChordExtension.MAJOR_SEVENTH if is_major_extension else ChordExtension.SEVENTH)
                elif num == 9:
                    extensions.append(ChordExtension.MAJOR_NINTH if is_major_extension else ChordExtension.NINTH)
                else:
                    extensions.append(num)
            else:
                # Other numbers might be additions
                additions.append(num)
        
        # Extract parenthetical content using pre-compiled regex
        for match in _CHORD_PATTERNS_COMPILED['parens'].finditer(remaining):
            paren_content = match.group(1)
            
            if paren_content.startswith('add'):
                add_num_str = paren_content[3:]
                if add_num_str.isdigit():
                    additions.append(int(add_num_str))
            elif paren_content.startswith('no'):
                omit_num_str = paren_content[2:]
                if omit_num_str.isdigit():
                    omissions.append(int(omit_num_str))
        
        return cls(root_str, quality, extensions, additions, omissions, bass_note)
    
    @classmethod
    def from_notes(cls, notes: Iterable[Union[Note, str]], bass_note: Optional[Union[Note, str]] = None) -> 'Chord':
        """
        Create a chord directly from a list of notes.
        
        This constructor allows creating chords with arbitrary note combinations,
        which is useful for effects like strumming where notes are added progressively.
        The chord will use the first note as the root.
        
        Args:
            notes: Iterable of Note objects or note strings (e.g., ["C", "E", "G"])
            bass_note: Optional bass note for slash chords
            
        Returns:
            A Chord object with the specified notes
            
        Examples:
            >>> chord = Chord.from_notes(["C", "E", "G"])  # C major chord
            >>> chord = Chord.from_notes([Note("C"), Note("E")])  # C-E partial chord
            >>> chord = Chord.from_notes(["C", "E", "G"], bass_note="E")  # C/E
        """
        note_list = list(notes)
        if not note_list:
            raise ValueError("At least one note must be provided")
        
        # Use the first note as the root
        root = note_list[0]
        
        return cls(root=root, bass_note=bass_note, notes=note_list)
    
    def _get_reference_scale(self) -> Scale:
        """
        Get the reference scale for enharmonic spelling.
        
        Returns:
            A Scale object used for determining correct enharmonic spellings
        """
        # Choose reference scale based on chord quality
        if self.quality == ChordQuality.MINOR:
            return Scale(self.root, ScaleType.NATURAL_MINOR)
        elif self.quality == ChordQuality.DIMINISHED:
            return Scale(self.root, ScaleType.LOCRIAN)
        else:
            # Default to major scale for most cases
            return Scale(self.root, ScaleType.MAJOR)
    
    @cached_property
    def notes(self) -> Tuple[Note, ...]:
        """
        Get the notes in this chord with proper enharmonic spelling.
        
        Returns:
            Tuple of Note objects representing the chord tones
        """
        # If this chord was created with from_notes(), return the custom notes
        if self._custom_notes is not None:
            return self._custom_notes
        return self._calculate_notes()
    
    def _calculate_notes(self) -> Tuple[Note, ...]:
        """
        Calculate the notes in the chord with proper enharmonic spelling and voice leading.
        """
        notes = []
        
        # Start with basic chord pattern using pre-computed intervals
        base_pattern = list(_CHORD_INTERVALS[self.quality])
        
        # Add extensions using fast hash table lookup
        for ext in self.extensions:
            if isinstance(ext, ChordExtension):
                interval = self.EXTENSION_INTERVALS[ext]
                base_pattern.append(interval)
            elif isinstance(ext, int) and ChordExtension.get_semitones(str(ext)) is not None:
                base_pattern.append(ChordExtension.get_semitones(str(ext)))
            # Skip invalid extensions silently
            
            # For extended chords, include lower extensions too
            if ext == ChordExtension.NINTH or ext == 9:
                if 10 not in base_pattern:  # Add minor 7th for regular 9th
                    base_pattern.append(10)
            elif ext == ChordExtension.MAJOR_NINTH:
                if 11 not in base_pattern:  # Add major 7th for major 9th
                    base_pattern.append(11)
            elif ext in [11, ChordExtension.ELEVENTH]:
                if 10 not in base_pattern:
                    base_pattern.append(10)
                if 14 not in base_pattern:
                    base_pattern.append(14)
            elif ext in [13, ChordExtension.THIRTEENTH]:
                if 10 not in base_pattern:
                    base_pattern.append(10)
                if 14 not in base_pattern:
                    base_pattern.append(14)
                if 17 not in base_pattern:
                    base_pattern.append(17)
        
        # Add additional notes
        for add in self.additions:
            if isinstance(add, int):
                if add == 2:
                    base_pattern.append(2)  # Major 2nd
                elif add == 4:
                    base_pattern.append(5)  # Perfect 4th
                elif add == 6:
                    base_pattern.append(9)  # Major 6th
                elif add == 9:
                    base_pattern.append(14)  # Major 9th
                elif add == 11:
                    base_pattern.append(17)  # Perfect 11th
        
        # Remove omitted notes
        for omit in self.omissions:
            if isinstance(omit, int):
                if omit == 3:
                    # Remove third
                    if 3 in base_pattern:
                        base_pattern.remove(3)
                    if 4 in base_pattern:
                        base_pattern.remove(4)
                elif omit == 5:
                    # Remove fifth
                    if 7 in base_pattern:
                        base_pattern.remove(7)
        
        # Remove duplicates and sort
        base_pattern = sorted(list(set(base_pattern)))
        
        # Get reference scale for enharmonic spelling
        ref_scale = self._get_reference_scale()
        
        # Calculate notes with proper voice leading octave distribution
        if self.root.octave is not None:
            notes = list(self._calculate_notes_with_voice_leading(base_pattern, ref_scale))
        else:
            # No octave information, calculate without octaves
            notes = [self._get_chord_tone_with_spelling(semitones, ref_scale) for semitones in base_pattern]
        
        # Handle inversion or bass note
        if self.bass_note:
            # For slash chords, add bass note if not already present
            bass_in_chord = any(note.pitch_class == self.bass_note.pitch_class for note in notes)
            if not bass_in_chord:
                notes.insert(0, self.bass_note)
        elif self.inversion and self.inversion > 0:
            # Apply inversion
            if self.inversion < len(notes):
                inverted_notes = notes[self.inversion:] + notes[:self.inversion]
                notes = inverted_notes
        
        return tuple(notes)
    
    def _calculate_notes_with_voice_leading(self, base_pattern: List[int], reference_scale: Scale) -> Tuple[Note, ...]:
        """
        Calculate chord notes with proper voice leading octave distribution.
        Notes are arranged in ascending order from the root, crossing octaves as needed.
        """
        notes = []
        current_midi = self.root.midi_number
        
        for semitones in base_pattern:
            # Calculate target MIDI note
            target_midi = self.root.midi_number + semitones
            
            # For voice leading, ensure each note is higher than or equal to the previous
            # If the target would be lower than current, move it up an octave
            if notes and target_midi < current_midi:
                target_midi += 12
            
            # Update current MIDI for next iteration
            current_midi = target_midi
            
            # Get the note with proper enharmonic spelling
            target_pitch_class = target_midi % 12
            
            # Try to find the note in the reference scale first
            found_in_scale = False
            for scale_note in reference_scale.notes:
                if scale_note.pitch_class == target_pitch_class:
                    target_octave = target_midi // 12 - 1
                    notes.append(scale_note.with_octave(target_octave))
                    found_in_scale = True
                    break
            
            # If not in reference scale, use standard enharmonic spelling
            if not found_in_scale:
                notes.append(Note.from_midi_number(target_midi))
        
        return tuple(notes)
    
    def _get_chord_tone_with_spelling(self, semitones: int, reference_scale: Scale) -> Note:
        """
        Get a chord tone with proper enharmonic spelling based on reference scale.
        """
        # Calculate target pitch class
        if self.root.octave is not None:
            target_midi = self.root.midi_number + semitones
            target_pitch_class = target_midi % 12
            target_octave = target_midi // 12 - 1  # Convert MIDI to octave
        else:
            target_pitch_class = (self.root.pitch_class + semitones) % 12
            target_octave = None
        
        # Try to find the note in the reference scale first
        for scale_note in reference_scale.notes:
            if scale_note.pitch_class == target_pitch_class:
                return scale_note.with_octave(target_octave)
        
        # If not in reference scale, use standard enharmonic spelling
        if self.root.octave is not None:
            return Note.from_midi_number(target_midi)
        else:
            temp_midi = 60 + target_pitch_class
            temp_note = Note.from_midi_number(temp_midi)
            return temp_note.with_octave(target_octave)
    
    def invert(self, inversion_number: int) -> 'Chord':
        """
        Create an inversion of this chord.
        
        Args:
            inversion_number: The inversion (1 = first inversion, etc.)
            
        Returns:
            A new Chord object representing the inversion
        """
        return self.with_inversion(inversion_number)
    
    def add_extension(self, extension: Union[ChordExtension, int, str]) -> 'Chord':
        """
        Add an extension to this chord.
        
        Args:
            extension: The extension to add
            
        Returns:
            A new Chord object with the extension added
        """
        return self.with_extension(extension)
    
    def transpose(self, interval: Interval) -> 'Chord':
        """
        Transpose this chord by an interval.
        
        Args:
            interval: The interval to transpose by
            
        Returns:
            A new Chord object transposed by the interval
        """
        new_root = self.root.transpose(interval)
        new_bass = self.bass_note.transpose(interval) if self.bass_note else None
        
        return self.with_(root=new_root, bass_note=new_bass)
    
    @property
    def name(self) -> str:
        """
        Get the full name/symbol of the chord.
        
        Returns:
            String representation of the chord symbol
        """
        name = str(self.root)
        
        # Add quality
        quality_symbols = {
            ChordQuality.MAJOR: "",
            ChordQuality.MINOR: "m",
            ChordQuality.DIMINISHED: "°",
            ChordQuality.AUGMENTED: "+",
            ChordQuality.SUSPENDED_2: "sus2",
            ChordQuality.SUSPENDED_4: "sus4",
            ChordQuality.POWER: "5",
        }
        name += quality_symbols[self.quality]
        
        # Add extensions
        for ext in self.extensions:
            if ext == ChordExtension.SEVENTH:
                name += "7"
            elif ext == ChordExtension.MAJOR_SEVENTH:
                name += "maj7"
            elif ext == ChordExtension.NINTH:
                name += "9"
            elif ext == ChordExtension.MAJOR_NINTH:
                name += "maj9"
            elif isinstance(ext, int):
                name += str(ext)
        
        # Add additions
        for add in self.additions:
            name += f"(add{add})"
        
        # Add omissions
        for omit in self.omissions:
            name += f"(no{omit})"
        
        # Add bass note
        if self.bass_note:
            name += f"/{self.bass_note}"
        
        return name
    
    def __iter__(self) -> Iterable[Note]:
        """Iterate over the notes in the chord."""
        return iter(self.notes)

    def __str__(self) -> str:
        """String representation of the chord."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        notes_str = ", ".join(str(note) for note in self.notes)
        return f"Chord({self.name}) - Notes: [{notes_str}]"
    
    def __eq__(self, other) -> bool:
        """Check equality with another chord."""
        if not isinstance(other, Chord):
            return False
        return (self.root == other.root and 
                self.quality == other.quality and
                self.extensions == other.extensions and
                self.additions == other.additions and
                self.omissions == other.omissions and
                self.bass_note == other.bass_note and
                self.inversion == other.inversion)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((
            self.root, self.quality, 
            tuple(self.extensions), tuple(self.additions), tuple(self.omissions),
            self.bass_note, self.inversion
        ))


# Common chord factory functions for convenience
def major_chord(root: Union[Note, str]) -> Chord:
    """Create a major triad."""
    return Chord(root, ChordQuality.MAJOR)

def minor_chord(root: Union[Note, str]) -> Chord:
    """Create a minor triad."""
    return Chord(root, ChordQuality.MINOR)

def diminished_chord(root: Union[Note, str]) -> Chord:
    """Create a diminished triad."""
    return Chord(root, ChordQuality.DIMINISHED)

def augmented_chord(root: Union[Note, str]) -> Chord:
    """Create an augmented triad."""
    return Chord(root, ChordQuality.AUGMENTED)

def dominant_seventh_chord(root: Union[Note, str]) -> Chord:
    """Create a dominant 7th chord."""
    return Chord(root, ChordQuality.MAJOR, [ChordExtension.SEVENTH])

def major_seventh_chord(root: Union[Note, str]) -> Chord:
    """Create a major 7th chord."""
    return Chord(root, ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])

def minor_seventh_chord(root: Union[Note, str]) -> Chord:
    """Create a minor 7th chord."""
    return Chord(root, ChordQuality.MINOR, [ChordExtension.SEVENTH])

def sus2_chord(root: Union[Note, str]) -> Chord:
    """Create a sus2 chord."""
    return Chord(root, ChordQuality.SUSPENDED_2)

def sus4_chord(root: Union[Note, str]) -> Chord:
    """Create a sus4 chord."""
    return Chord(root, ChordQuality.SUSPENDED_4)
