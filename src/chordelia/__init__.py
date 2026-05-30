"""
Chordelia - A comprehensive music theory library built around algorithmic approaches.

This library provides efficient implementations of fundamental music theory concepts:
- Intervals: Musical intervals with names and calculations
- Notes: Musical notes with accidentals, enharmonics, and octave information
- Scales: Musical scales with proper enharmonic spelling
- Chords: Chord construction, parsing, and inversions
- Rhythm: Musical timing, durations, time signatures, and tempo

All implementations prioritize algorithms over lookup tables for efficiency
and clarity, making it suitable for low-end hardware.
"""

from chordelia.intervals import Interval, IntervalLike, IntervalQuality
from chordelia.degrees import Degree, DegreeLike, RomanCase
from chordelia.accidentals import Accidental
from chordelia.notes import Note, NoteName
from chordelia.scales import Scale, ScaleType
from chordelia.chords import Chord, ChordQuality, ChordExtension
from chordelia.sequences import Sequence, SequenceEntry, SequenceEntryLike, Rest
from chordelia.score import Score, ScoreEvent, ScoreEventContext, ScoreMetadata, score_from_sequenceable
from chordelia.sequenceable import NotesLike, Sequenceable
from chordelia.rhythm import (
    Duration, TimeSignature, Tempo, Beat, NoteValue,
    whole_note, half_note, quarter_note, eighth_note, sixteenth_note,
    dotted, triplet, COMMON_TIME, WALTZ_TIME, COMPOUND_DUPLE
)

# Audio playback module - optional import (requires sounddevice and numpy)
try:
    from chordelia.audio_playback import Playback, PlaybackNote, Waveform, play_scale, play_chord, play_melody, create_chord_notes
    from chordelia.playback_notes import midi_tracks_to_playback_notes, score_to_playback_notes
    _PLAYBACK_AVAILABLE = True
except ImportError:
    _PLAYBACK_AVAILABLE = False

# MIDI modules - optional import (requires mido)
try:
    from chordelia.midi_playback import MidiPlayback, get_midi_ports, is_midi_available
    from chordelia.midi_playback import play_chord as midi_play_chord, play_melody as midi_play_melody
    from chordelia.midifile import MidiFile, MidiTrackInfo
    _MIDI_AVAILABLE = True
except ImportError:
    _MIDI_AVAILABLE = False

__version__ = "0.3.1"
__all__ = [
    "Interval",
    "IntervalLike",
    "IntervalQuality", 
    "Degree",
    "DegreeLike",
    "RomanCase",
    "Note",
    "NoteName",
    "Accidental",
    "Scale",
    "ScaleType",
    "Chord",
    "ChordQuality",
    "ChordExtension",
    "Sequence",
    "SequenceEntry",
    "SequenceEntryLike",
    "Rest",
    "Score",
    "ScoreEvent",
    "ScoreEventContext",
    "ScoreMetadata",
    "score_from_sequenceable",
    "Sequenceable",
    "NotesLike",
    "Duration",
    "TimeSignature", 
    "Tempo",
    "Beat",
    "NoteValue",
    "whole_note",
    "half_note", 
    "quarter_note",
    "eighth_note",
    "sixteenth_note",
    "dotted",
    "triplet",
    "COMMON_TIME",
    "WALTZ_TIME", 
    "COMPOUND_DUPLE",
]

# Add audio playback exports if available
if _PLAYBACK_AVAILABLE:
    __all__.extend([
        "Playback",
        "PlaybackNote", 
        "Waveform",
        "midi_tracks_to_playback_notes",
        "score_to_playback_notes",
        "play_scale",
        "play_chord",
        "play_melody",
        "create_chord_notes",
    ])

# Add MIDI playback exports if available  
if _MIDI_AVAILABLE:
    __all__.extend([
        "MidiPlayback",
        "MidiFile",
        "MidiTrackInfo",
        "get_midi_ports", 
        "is_midi_available",
        "midi_play_chord",
        "midi_play_melody",
    ])


def get_available_features():
    """
    Get information about which optional features are available.
    
    Returns:
        Dict with feature availability and installation instructions
    """
    features = {
        'core': {
            'available': True,
            'description': 'Core music theory (Notes, Scales, Chords, Intervals, Rhythm)',
            'install': 'Included in base installation'
        },
        'audio': {
            'available': _PLAYBACK_AVAILABLE,
            'description': 'Audio playback with multiple waveforms',
            'install': 'pip install chordelia[audio]' if not _PLAYBACK_AVAILABLE else 'Available'
        },
        'midi': {
            'available': _MIDI_AVAILABLE,
            'description': 'MIDI file and playback support',
            'install': 'pip install chordelia[midi]' if not _MIDI_AVAILABLE else 'Available'
        }
    }
    
    return features


def print_feature_status():
    """Print a summary of available features."""
    features = get_available_features()
    
    print("🎵 CHORDELIA FEATURE STATUS")
    print("=" * 30)
    
    for name, info in features.items():
        status = "✅" if info['available'] else "❌"
        print(f"{status} {name.title()}: {info['description']}")
        if not info['available']:
            print(f"   Install with: {info['install']}")
    
    print()
    if not _PLAYBACK_AVAILABLE and not _MIDI_AVAILABLE:
        print("💡 For complete experience: pip install chordelia[all]")
    elif not _PLAYBACK_AVAILABLE:
        print("💡 For audio playback: pip install chordelia[audio]")
    elif not _MIDI_AVAILABLE:
        print("💡 For MIDI support: pip install chordelia[midi]")


# Add to exports
__all__.extend(["get_available_features", "print_feature_status"])
