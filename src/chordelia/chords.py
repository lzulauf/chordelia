"""
Musical chords implementation with parsing and proper enharmonic spelling.

This module provides classes for representing chords, including constructing
chords from parts, string parsing, additions, extensions, and inversions with
proper enharmonic spelling based on underlying scales.
"""

from enum import Enum
from functools import lru_cache, cached_property
import logging
import re
from typing import Iterable, List, Optional, Union, Dict, Tuple

from chordelia import intervals
from chordelia.intervals import Interval, IntervalQuality
from chordelia.notes import Note, NoteName, Accidental
from chordelia.scales import Scale, ScaleType

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

_MODIFICATION = r'(maj|add|no)?[#b]?[0-9]+'
_MODIFICATION_RE = re.compile(rf'^({_MODIFICATION}|\({_MODIFICATION}\))')
_ROOT_PATTERN_RE = re.compile(r'^([A-G][#b]*)')


class ChordQuality(Enum):
    """Enumeration of basic chord qualities."""
    MAJOR = ("major", ("", "M", "maj", "major"), (0, 4, 7))
    MINOR = ("minor", ("-", "m", "min", "minor"), (0, 3, 7))
    DIMINISHED = ("diminished", ("dim", "diminished", "°"), (0, 3, 6))
    AUGMENTED = ("augmented", ("+", "aug", "augmented"), (0, 4, 8))
    SUSPENDED_2 = ("sus2", ("sus2",), (0, 2, 7))
    SUSPENDED_4 = ("sus4", ("sus", "sus4"), (0, 5, 7))
    POWER = ("power", ("5", "power"), (0, 7))

    def __init__(self, quality_str: str, abbreviations: Tuple[str, ...], semitone_intervals: Tuple[int, ...]):
        self._quality_str = quality_str
        self._abbreviations = abbreviations
        self._semitone_intervals = semitone_intervals

    @classmethod
    def from_string(cls, quality_str: str) -> 'ChordQuality':
        """Get ChordQuality from string."""
        if not hasattr(cls, "_from_string_map"):
            cls._from_string_map: Dict[str, 'ChordQuality'] = {
                abbr: quality
                for quality in cls
                for abbr in quality.abbreviations
            }
        try:
            return cls._from_string_map[quality_str]
        except KeyError:
            raise ValueError(f"Unknown ChordQuality string: {quality_str!r}")

    @property
    def quality_str(self) -> str:
        return self._quality_str

    @property
    def semitone_intervals(self) -> Tuple[int, ...]:
        return self._semitone_intervals

    @property
    def abbreviations(self) -> Tuple[str, ...]:
        return self._abbreviations

    def __str__(self):
        return self._quality_str

    def __repr__(self):
        return f"<ChordQuality({self._quality_str})>"


class ChordExtension(Enum):
    """
    Enumeration of chord extensions with semitone values.

    Extensions represent additional chord tones beyond the basic triad. An
    even-numbered extension adds just that single note, while an odd-numbered
    extension implies the presence of the lower odd extensions as well.
    """
    SIXTH = ("6", (intervals.MAJOR_SIXTH,))
    SEVENTH = ("7", (intervals.MINOR_SEVENTH,))
    MAJOR_SEVENTH = ("maj7", (intervals.MAJOR_SEVENTH,))
    NINTH = ("9", (intervals.MINOR_SEVENTH, intervals.MAJOR_NINTH,))
    MAJOR_NINTH = ("maj9", (intervals.MAJOR_SEVENTH, intervals.MAJOR_NINTH,))
    ELEVENTH = ("11", (intervals.MINOR_SEVENTH, intervals.MAJOR_NINTH, intervals.PERFECT_ELEVENTH,))
    MAJOR_ELEVENTH = ("maj11", (intervals.MAJOR_SEVENTH, intervals.MAJOR_NINTH, intervals.PERFECT_ELEVENTH,))
    THIRTEENTH = ("13", (intervals.MINOR_SEVENTH, intervals.MAJOR_NINTH, intervals.PERFECT_ELEVENTH, intervals.MAJOR_THIRTEENTH))
    MAJOR_THIRTEENTH = ("maj13", (intervals.MAJOR_SEVENTH, intervals.MAJOR_NINTH, intervals.PERFECT_ELEVENTH, intervals.MAJOR_THIRTEENTH))

    def __init__(self, extension_str, intervals):
        self._extension_str = extension_str
        self._intervals = intervals
    
    @classmethod
    def from_string(cls, extension_str: str) -> 'ChordExtension':
        """Get ChordExtension from string."""
        for ext in cls:
            if ext._extension_str == extension_str:
                return ext
        raise ValueError(f"Unknown ChordExtension string: {extension_str!r}")

    @classmethod
    def from_unknown(cls, extension: Union['ChordExtension', str]) -> 'ChordExtension':
        """Convert unknown extension representation to ChordExtension."""
        if isinstance(extension, ChordExtension):
            return extension
        elif isinstance(extension, str):
            return cls.from_string(extension)
        else:
            raise ValueError(f"Unknown ChordExtension representation: {extension!r}")

    @property
    def intervals(self) -> List[Interval]:
        return self._intervals

    def __str__(self):
        return self._extension_str

    def __repr__(self):
        return f"ChordExtension({self._extension_str})"


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
        >>> chord.with_(root="F#", quality="minor", extension="maj9")  # F#m(maj9)
        
        All methods preserve immutability - the original chord is never modified.
    """
    
    __slots__ = ('_root', '_quality', '_extension', '_additions', '_omissions', '_bass_note', '_inversion', '_custom_notes', '__dict__')
    
    def __init__(self, 
                 root: Union[Note, str],
                 quality: Union[ChordQuality, str] = ChordQuality.MAJOR,
                 extension: Optional[Union[ChordExtension, str]] = None,
                 additions: Optional[Iterable[Union[Interval, int, str]]] = None,
                 omissions: Optional[Iterable[Union[Interval, int, str]]] = None,
                 bass_note: Optional[Union[Note, str]] = None,
                 inversion: int = 0,
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
            quality = ChordQuality.from_string(quality)
        
        # Convert extensions, additions, omissions to tuples for immutability
        extension = ChordExtension.from_unknown(extension) if extension else None
        additions = tuple((Interval.from_unknown(a) for a in additions) if additions else [])
        omissions = tuple((Interval.from_unknown(o) for o in omissions) if omissions else [])
        
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
        self._extension = extension
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
    def extension(self) -> ChordExtension:
        """Chord extension."""
        return self._extension
    
    @property
    def additions(self) -> Tuple[Interval, ...]:
        """Tuple of added chord tones."""
        return self._additions
    
    @property
    def omissions(self) -> Tuple[Interval, ...]:
        """Tuple of omitted chord tones as Interval objects."""
        return self._omissions
    
    @property
    def bass_note(self) -> Optional[Note]:
        """Bass note for slash chords."""
        return self._bass_note
    
    @property
    def inversion(self) -> int:
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
        return Chord(root, self._quality, self._extension, self._additions,
                    self._omissions, self._bass_note, self._inversion)

    def with_octave(self, octave: int|None) -> 'Chord':
        """
        Create a copy of this chord with the given root note octave.

        Can be used to give an octave to a chord that lacks one, or to replace
        the octave.
        
        Args:
            octave: The octave of the root note
            
        Returns:
            A new Chord with the same properties but different root octave
        """
        return Chord(self._root.with_octave(octave), self._quality, self._extension, self._additions,
                    self._omissions, self._bass_note, self._inversion)

    
    def with_quality(self, quality: Union[ChordQuality, str]) -> 'Chord':
        """
        Create a copy of this chord with a different quality.
        
        Args:
            quality: The new chord quality
            
        Returns:
            A new Chord with the same properties but different quality
        """
        return Chord(self._root, quality, self._extension, self._additions,
                    self._omissions, self._bass_note, self._inversion)
    
    def with_extension(self, extension: Union[ChordExtension, str]) -> 'Chord':
        """
        Create a copy of this chord with a different extension.
        
        Args:
            extension: The new chord extension
            
        Returns:
            A new Chord with the given extension
        """
        extension = ChordExtension.from_unknown(extension)
        return Chord(self._root, self._quality, extension, self._additions,
                    self._omissions, self._bass_note, self._inversion)
    
    def with_bass(self, bass_note: Union[Note, str, None]) -> 'Chord':
        """
        Create a copy of this chord with a different bass note.
        
        Args:
            bass_note: The new bass note (or None to remove)
            
        Returns:
            A new Chord with the specified bass note
        """
        return Chord(self._root, self._quality, self._extension, self._additions,
                    self._omissions, bass_note, self._inversion)
    
    def with_inversion(self, inversion: int) -> 'Chord':
        """
        Create a copy of this chord with a different inversion.
        
        Args:
            inversion: The new inversion number (or None for root position)
            
        Returns:
            A new Chord with the specified inversion
        """
        return Chord(self._root, self._quality, self._extension, self._additions,
                    self._omissions, self._bass_note, inversion)
    
    def with_(self,
              root: Optional[Union[Note, str]] = None,
              quality: Optional[Union[ChordQuality, str]] = None,
              extension: Optional[Union[ChordExtension, str]] = None,
              additions: Optional[Iterable[Union[Interval, int, str]]] = None,
              omissions: Optional[Iterable[Union[Interval, int, str]]] = None,
              bass_note: Optional[Union[Note, str, None]] = ...,
              inversion: Optional[int] = ...) -> 'Chord':
        """
        Create a copy of this chord with any combination of modified attributes.
        
        Args:
            root: New root note (defaults to current)
            quality: New chord quality (defaults to current)
            extension: New chord extension (defaults to current) - can be ChordExtension or str
            additions: New additions iterable (defaults to current) - can be list, tuple, set, etc.
            omissions: New omissions iterable (defaults to current) - can be list, tuple, set, etc.
            bass_note: New bass note (defaults to current, use explicit None to remove)
            inversion: New inversion (defaults to current, use explicit None to remove)
            
        Returns:
            A new Chord with the specified modifications
            
        Examples:
            >>> chord = Chord("C")
            >>> chord.with_(quality="minor")  # Cm
            >>> chord.with_(root="F", extension="7")  # F7
            >>> chord.with_(bass_note="E")  # C/E
            >>> chord.with_(bass_note=None)  # Remove bass note
        """
        # Use current values as defaults, but allow explicit None/... for optional fields
        new_root = root if root is not None else self._root
        new_quality = quality if quality is not None else self._quality
        new_extension = ChordExtension.from_unknown(extension) if extension is not None else self._extension
        new_additions = additions if additions is not None else self._additions
        new_omissions = omissions if omissions is not None else self._omissions
        new_bass_note = self._bass_note if bass_note is ... else bass_note
        new_inversion = self._inversion if inversion is ... else inversion
        
        return Chord(new_root, new_quality, new_extension, new_additions,
                    new_omissions, new_bass_note, new_inversion)
    
    @classmethod
    @lru_cache(maxsize=256)
    def from_string(cls, chord_string: str, octave: int|None = None) -> 'Chord':
        """
        Parse a chord from string notation with optimized regex parsing.
        
        Supports formats like:
        - C, Cmaj, Cmajor, CM
        - Cm, Cmin, Cminor, C-
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
        root_match = _ROOT_PATTERN_RE.match(chord_string)
        if not root_match:
            raise ValueError(f"Invalid chord string: {chord_string}")
        
        root_str = root_match.group(1)
        remaining = chord_string[len(root_str):]
        
        # Initialize parsing variables
        quality = ChordQuality.MAJOR
        extension = None
        additions = []
        omissions = []
        
        # Fast quality detection using hash table
        remaining_lower = remaining.lower()
        
        # Check for quality markers in order of specificity
        if remaining_lower.startswith('minor'):
            quality = ChordQuality.MINOR
            remaining = remaining[5:]
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
        elif remaining_lower.startswith('maj'):
            # it's probably an extension leave the quality as major without consuming remainder
            quality = ChordQuality.MAJOR
        elif re.match(r'^([m-])', remaining):
            quality = ChordQuality.MINOR
            remaining = remaining[1:]
        elif re.match(r'^M\b', remaining):
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

        print(f"{quality=}, {remaining=}")

        # True until we've found the first modification.
        first_modification = True

        def _process_modifications(content: str):
            nonlocal first_modification
            nonlocal extension
            if content.startswith('no'):
                omissions.append(Interval.from_string(content[2:]))
            elif content.startswith('add'):
                additions.append(Interval.from_string(content[3:]))
            else:
                # No prefix. Assume chord extension if it's the first modification, otherwise addition.
                if first_modification:
                    extension = ChordExtension.from_string(content)
                else: 
                    additions.append(Interval.from_string(content))
            first_modification = False

        while match := _MODIFICATION_RE.match(remaining):
            mod_str = match.group(0)
            print(f"Found modification: {mod_str}")
            _process_modifications(mod_str.strip("()"))
            remaining = remaining[len(mod_str):]

        return cls(root_str, quality, extension=extension, additions=additions, omissions=omissions, bass_note=bass_note)
    
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
        base_pattern = list(self.quality.semitone_intervals)
        _logger.debug(f"Base pattern for {self.quality}: {base_pattern}")
        
        if self.extension:
            base_pattern.extend([interval.semitones for interval in self.extension.intervals])
            _logger.debug(f"  Extension {self.extension}: {base_pattern}")
        
        # Add additional notes
        for add in self.additions:
            base_pattern.append(add.semitones)
            _logger.debug(f"  Added {add}: {base_pattern}")
        
        # Remove omitted notes
        for omit in self.omissions:
            base_pattern.remove(omit.semitones)
            _logger.debug(f"  Omitted {omit}: {base_pattern}")
        
        # Remove duplicates and sort semitone (intervals)
        base_pattern = sorted(list(set(base_pattern)))
        _logger.debug(f"  Sorted: {base_pattern}")
        
        # Get reference scale for enharmonic spelling
        ref_scale = self._get_reference_scale()
        _logger.debug(f"  Reference scale: {ref_scale}: {[str(n) for n in ref_scale.notes]}")
        
        # Calculate notes with proper voice leading octave distribution
        if self.root.octave is not None:
            notes = list(self._calculate_notes_with_voice_leading(base_pattern, ref_scale))
            _logger.debug(f"  Notes with voice leading: {notes}")
        else:
            # No octave information, calculate without octaves
            notes = [self._get_chord_tone_with_spelling(semitones, ref_scale) for semitones in base_pattern]
            _logger.debug(f"  Notes without octave: {notes}")
        
        # Handle inversion or bass note
        if self.bass_note:
            # For slash chords, add bass note if not already present
            bass_in_chord = any(note.pitch_class == self.bass_note.pitch_class for note in notes)
            if not bass_in_chord:
                notes.insert(0, self.bass_note)
                _logger.debug(f"  Inserted bass note {self.bass_note} at bottom: {notes}")
            else:
                # TODO - We could consider moving base note down to the bottom
                # and/or adding another base note to the bottom.
                _logger.debug(f"  Bass note {self.bass_note} already in chord, no insertion needed")


        elif self.inversion != 0:
            inversions = self.inversion
            while inversions > 0:
                inversions -= 1
                inverted_note = notes[0].with_octave(notes[0].octave + 1 if notes[0].octave is not None else None)
                notes = notes[1:] + [inverted_note]
            while inversions < 0:
                inversions += 1
                inverted_note = notes[-1].with_octave(notes[-1].octave - 1 if notes[-1].octave is not None else None)
                notes =  [inverted_note] + notes[:-1]
            _logger.debug(f"  Notes after inversion {self.inversion}: {notes}")
        
        return tuple(notes)
    
    def _calculate_notes_with_voice_leading(self, base_pattern: List[int], reference_scale: Scale) -> Tuple[Note, ...]:
        """
        Calculate chord notes with proper voice leading octave distribution.
        Notes are arranged in ascending order from the root, crossing octaves as needed.
        """
        notes = []
        current_midi = self.root.midi_number

        _logger.debug(f"Calculating notes with voice leading from root {self.root}({current_midi}), "
                      f"base pattern: {base_pattern}, and reference scale: {reference_scale}")
        
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
    
    def add_extension(self, extension: Union[ChordExtension, str]) -> 'Chord':
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
        
        # Add extension
        if self._extension:
            name += f"({self._extension})"
        
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

    def as_dict(self) -> Dict:
        """
        Get a dictionary representation of the chord.
        
        Returns:
            A dictionary with chord attributes
        """
        return {
            "root": str(self.root),
            "quality": str(self.quality),
            "extension": str(self._extension) if self._extension else None,
            "additions": [str(add) for add in self.additions],
            "omissions": [str(omit) for omit in self.omissions],
            "bass_note": str(self.bass_note) if self.bass_note else None,
            "inversion": self.inversion,
            "notes": [str(note) for note in self.notes]
        }
    
    def __iter__(self) -> Iterable[Note]:
        """Iterate over the notes in the chord."""
        return iter(self.notes)

    def __str__(self) -> str:
        """String representation of the chord."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        notes_str = ", ".join(str(note) for note in self.notes)
        return f'<Chord({self.name})[{notes_str}]>'
    
    def __eq__(self, other) -> bool:
        """Check equality with another chord."""
        if not isinstance(other, Chord):
            return False
        return (self.root == other.root and 
                self.quality == other.quality and
                self.extension == other.extension and
                self.additions == other.additions and
                self.omissions == other.omissions and
                self.bass_note == other.bass_note and
                self.inversion == other.inversion)
    
    def __hash__(self) -> int:
        """Hash function for use in sets and dictionaries."""
        return hash((
            self.root, self.quality, 
            self.extension, tuple(self.additions), tuple(self.omissions),
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
    return Chord(root, ChordQuality.MAJOR, ChordExtension.SEVENTH)

def major_seventh_chord(root: Union[Note, str]) -> Chord:
    """Create a major 7th chord."""
    return Chord(root, ChordQuality.MAJOR, ChordExtension.MAJOR_SEVENTH)

def minor_seventh_chord(root: Union[Note, str]) -> Chord:
    """Create a minor 7th chord."""
    return Chord(root, ChordQuality.MINOR, ChordExtension.SEVENTH)

def sus2_chord(root: Union[Note, str]) -> Chord:
    """Create a sus2 chord."""
    return Chord(root, ChordQuality.SUSPENDED_2)

def sus4_chord(root: Union[Note, str]) -> Chord:
    """Create a sus4 chord."""
    return Chord(root, ChordQuality.SUSPENDED_4)
