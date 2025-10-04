from enum import Enum
from typing import List, Union
from .note import NoteName, Note
from .interval import Interval

class ScaleType(Enum):
    MAJOR = [0, 2, 4, 5, 7, 9, 11]
    MINOR = [0, 2, 3, 5, 7, 8, 10]
    HARMONIC_MINOR = [0, 2, 3, 5, 7, 8, 11]
    MELODIC_MINOR = [0, 2, 3, 5, 7, 9, 11]
    PENTATONIC_MAJOR = [0, 2, 4, 7, 9]
    PENTATONIC_MINOR = [0, 3, 5, 7, 10]
    BLUES = [0, 3, 5, 6, 7, 10]
    DORIAN = [0, 2, 3, 5, 7, 9, 10]
    PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]
    LYDIAN = [0, 2, 4, 6, 7, 9, 11]
    MIXOLYDIAN = [0, 2, 4, 5, 7, 9, 10]
    LOCRIAN = [0, 1, 3, 5, 6, 8, 10]

class Mode(Enum):
    IONIAN = 0      # Major
    DORIAN = 1
    PHRYGIAN = 2
    LYDIAN = 3
    MIXOLYDIAN = 4
    AEOLIAN = 5     # Minor
    LOCRIAN = 6

class Scale:
    """Represents a musical scale."""
    
    def __init__(self, root: Union[NoteName, str], scale_type: ScaleType, mode: Mode = Mode.IONIAN):
        if isinstance(root, str):
            root = Note._parse_note_name(root)
        self.root = root
        self.scale_type = scale_type
        self.mode = mode
    
    def get_intervals(self) -> List[int]:
        """Get the intervals for this scale accounting for mode."""
        base_intervals = self.scale_type.value
        mode_offset = self.mode.value
        
        # Rotate the intervals based on the mode
        if mode_offset == 0:
            return base_intervals
        
        rotated = base_intervals[mode_offset:] + [i + 12 for i in base_intervals[:mode_offset]]
        # Normalize to start from 0
        return [(i - rotated[0]) % 12 for i in rotated]
    
    def get_note_names(self) -> List[NoteName]:
        """Get all note names in this scale."""
        intervals = self.get_intervals()
        notes = []
        
        for interval in intervals:
            note_value = (self.root.value + interval) % 12
            # Find a NoteName with this value (prefer sharps for consistency)
            for note_name in NoteName:
                if note_name.value == note_value:
                    notes.append(note_name)
                    break
        
        return notes

def get_scale_notes(root: Union[NoteName, str], scale_type: ScaleType, mode: Mode = Mode.IONIAN) -> List[NoteName]:
    """
    Get all note names in a scale given root, scale type, and mode.
    
    Args:
        root: Root note name
        scale_type: Type of scale (major, minor, etc.)
        mode: Mode of the scale (default: Ionian/Major)
    
    Returns:
        List of note names in the scale
    """
    scale = Scale(root, scale_type, mode)
    return scale.get_note_names()
