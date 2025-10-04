from enum import Enum
from typing import Union

class NoteName(Enum):
    C = 0
    C_SHARP = 1
    D_FLAT = 1
    D = 2
    D_SHARP = 3
    E_FLAT = 3
    E = 4
    F = 5
    F_SHARP = 6
    G_FLAT = 6
    G = 7
    G_SHARP = 8
    A_FLAT = 8
    A = 9
    A_SHARP = 10
    B_FLAT = 10
    B = 11

class Note:
    """Represents a specific note with name and octave."""
    
    def __init__(self, name: Union[NoteName, str], octave: int = 3):
        if isinstance(name, str):
            name = self._parse_note_name(name)
        self.name = name
        self.octave = octave
    
    @staticmethod
    def _parse_note_name(name_str: str) -> NoteName:
        """Parse string note name to NoteName enum."""
        name_map = {
            'C': NoteName.C, 'C#': NoteName.C_SHARP, 'Db': NoteName.D_FLAT,
            'D': NoteName.D, 'D#': NoteName.D_SHARP, 'Eb': NoteName.E_FLAT,
            'E': NoteName.E, 'F': NoteName.F, 'F#': NoteName.F_SHARP,
            'Gb': NoteName.G_FLAT, 'G': NoteName.G, 'G#': NoteName.G_SHARP,
            'Ab': NoteName.A_FLAT, 'A': NoteName.A, 'A#': NoteName.A_SHARP,
            'Bb': NoteName.B_FLAT, 'B': NoteName.B
        }
        return name_map[name_str]
    
    def __str__(self) -> str:
        sharp_names = {
            NoteName.C: 'C', NoteName.C_SHARP: 'C#', NoteName.D: 'D',
            NoteName.D_SHARP: 'D#', NoteName.E: 'E', NoteName.F: 'F',
            NoteName.F_SHARP: 'F#', NoteName.G: 'G', NoteName.G_SHARP: 'G#',
            NoteName.A: 'A', NoteName.A_SHARP: 'A#', NoteName.B: 'B'
        }
        return f"{sharp_names[self.name]}{self.octave}"

    def __repr__(self) -> str:
        return f"Note({self.name.name}, {self.octave})"
    
    def transpose(self, semitones: int) -> 'Note':
        """Transpose the note by a number of semitones."""
        new_value = (self.name.value + semitones) % 12
        new_octave = self.octave + (self.name.value + semitones) // 12
        
        # Find the NoteName with the new value (prefer sharps)
        for note_name in NoteName:
            if note_name.value == new_value and '#' in note_name.name:
                return Note(note_name, new_octave)
        
        # Fallback to any NoteName with the value
        for note_name in NoteName:
            if note_name.value == new_value:
                return Note(note_name, new_octave)
