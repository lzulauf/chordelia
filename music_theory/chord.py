from enum import Enum
from typing import List, Union, Optional, Dict
from .note import NoteName, Note
from .interval import Interval
from .scale import Scale, ScaleType

class ChordType(Enum):
    MAJOR = [0, 4, 7]
    MINOR = [0, 3, 7]
    DIMINISHED = [0, 3, 6]
    AUGMENTED = [0, 4, 8]
    SUSPENDED_2 = [0, 2, 7]
    SUSPENDED_4 = [0, 5, 7]
    MAJOR_7 = [0, 4, 7, 11]
    MINOR_7 = [0, 3, 7, 10]
    DOMINANT_7 = [0, 4, 7, 10]
    DIMINISHED_7 = [0, 3, 6, 9]
    HALF_DIMINISHED_7 = [0, 3, 6, 10]
    MAJOR_MAJ_7 = [0, 4, 7, 11]

class Chord:
    """Represents a musical chord."""
    
    def __init__(self, root: Union[NoteName, str], chord_type: ChordType, 
                 extensions: Optional[List[int]] = None, inversion: int = 0):
        if isinstance(root, str):
            root = Note._parse_note_name(root)
        self.root = root
        self.chord_type = chord_type
        self.extensions = extensions or []
        self.inversion = inversion
    
    def get_intervals(self) -> List[int]:
        """Get all intervals in the chord including extensions."""
        intervals = list(self.chord_type.value)
        
        # Add extensions
        extension_map = {
            6: 9,   # Major 6th
            7: 10,  # Minor 7th (dominant 7th)
            9: 2,   # Major 9th (same as major 2nd within octave)
            11: 5,  # Perfect 11th (same as perfect 4th within octave)
            13: 9   # Major 13th (same as major 6th within octave)
        }
        
        for ext in self.extensions:
            if ext in extension_map:
                intervals.append(extension_map[ext])
        
        return sorted(intervals)
    
    def get_notes(self, octave: int = 4) -> List[Note]:
        """Get specific notes in the chord with inversions applied."""
        intervals = self.get_intervals()
        notes = []
        
        for interval in intervals:
            note = Note(self.root, octave).transpose(interval)
            notes.append(note)
        
        # Apply inversions
        if self.inversion != 0:
            notes = self._apply_inversion(notes, self.inversion)
        
        return notes
    
    def get_note_names(self) -> List[NoteName]:
        """Get note names in the chord."""
        intervals = self.get_intervals()
        note_names = []
        
        for interval in intervals:
            note_value = (self.root.value + interval) % 12
            for note_name in NoteName:
                if note_name.value == note_value:
                    note_names.append(note_name)
                    break
        
        # Apply inversions to note names (just reorder)
        if self.inversion != 0:
            note_names = self._apply_inversion_to_names(note_names, self.inversion)
        
        return note_names
    
    def _apply_inversion(self, notes: List[Note], inversion: int) -> List[Note]:
        """Apply inversion to a list of notes."""
        if inversion == 0:
            return notes
        
        result = notes.copy()
        
        if inversion > 0:
            # Positive: move lowest notes up an octave
            for _ in range(inversion):
                if result:
                    lowest = result.pop(0)
                    highest_octave = max(note.octave for note in result) if result else lowest.octave
                    result.append(Note(lowest.name, highest_octave + 1))
        else:
            # Negative: move highest notes down an octave
            for _ in range(abs(inversion)):
                if result:
                    highest = result.pop()
                    lowest_octave = min(note.octave for note in result) if result else highest.octave
                    result.insert(0, Note(highest.name, lowest_octave - 1))
        
        return result
    
    def _apply_inversion_to_names(self, note_names: List[NoteName], inversion: int) -> List[NoteName]:
        """Apply inversion ordering to note names."""
        if inversion == 0:
            return note_names
        
        result = note_names.copy()
        
        if inversion > 0:
            # Positive: rotate left (move first elements to end)
            for _ in range(inversion % len(result)):
                if result:
                    result.append(result.pop(0))
        else:
            # Negative: rotate right (move last elements to front)
            for _ in range(abs(inversion) % len(result)):
                if result:
                    result.insert(0, result.pop())
        
        return result

def get_chord_notes(root: Union[NoteName, str], chord_type: ChordType, 
                   extensions: Optional[List[int]] = None, inversion: int = 0, 
                   octave: int = 4) -> List[Note]:
    """
    Get specific notes of a chord.
    
    Args:
        root: Root note name
        chord_type: Type of chord
        extensions: Additional intervals (6, 7, 9, etc.)
        inversion: Inversion number (positive moves lowest up, negative moves highest down)
        octave: Starting octave for the root note
    
    Returns:
        List of specific notes in the chord
    """
    chord = Chord(root, chord_type, extensions, inversion)
    return chord.get_notes(octave)

def get_chord_note_names(root: Union[NoteName, str], chord_type: ChordType, 
                        extensions: Optional[List[int]] = None, inversion: int = 0) -> List[NoteName]:
    """
    Get note names of a chord (without octave information).
    
    Args:
        root: Root note name
        chord_type: Type of chord
        extensions: Additional intervals (6, 7, 9, etc.)
        inversion: Inversion number
    
    Returns:
        List of note names in the chord
    """
    chord = Chord(root, chord_type, extensions, inversion)
    return chord.get_note_names()

def get_compatible_chords(scale_root: Union[NoteName, str], scale_type: ScaleType, 
                         note_name: Union[NoteName, str]) -> List[ChordType]:
    """
    Get chord types that are compatible with a given scale when built on a specific note.
    
    Args:
        scale_root: Root of the scale
        scale_type: Type of scale
        note_name: Note to build chords on
    
    Returns:
        List of compatible chord types
    """
    if isinstance(scale_root, str):
        scale_root = Note._parse_note_name(scale_root)
    if isinstance(note_name, str):
        note_name = Note._parse_note_name(note_name)
    
    scale = Scale(scale_root, scale_type)
    scale_notes = set(note.value for note in scale.get_note_names())
    
    compatible_chords = []
    
    # Check each chord type
    for chord_type in ChordType:
        chord = Chord(note_name, chord_type)
        chord_note_values = set((note_name.value + interval) % 12 for interval in chord.get_intervals())
        
        # Check if all chord notes are in the scale
        if chord_note_values.issubset(scale_notes):
            compatible_chords.append(chord_type)
    
    return compatible_chords
