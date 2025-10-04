"""
A music theory library supporting notes, scales, chords, and their relationships.
"""

from .note import Note, NoteName
from .interval import Interval
from .scale import Scale, ScaleType, Mode, get_scale_notes
from .chord import Chord, ChordType, get_chord_notes, get_chord_note_names, get_compatible_chords

__all__ = [
    'Note', 'NoteName', 'Interval',
    'Scale', 'ScaleType', 'Mode', 'get_scale_notes',
    'Chord', 'ChordType', 'get_chord_notes', 'get_chord_note_names', 'get_compatible_chords'
]
