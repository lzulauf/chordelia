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

from chordelia.intervals import Interval, IntervalQuality
from chordelia.notes import Note, NoteName, Accidental
from chordelia.scales import Scale, ScaleType
from chordelia.chords import Chord, ChordQuality, ChordExtension
from chordelia.rhythm import (
    Duration, TimeSignature, Tempo, Beat, NoteValue,
    whole_note, half_note, quarter_note, eighth_note, sixteenth_note,
    dotted, triplet, COMMON_TIME, WALTZ_TIME, COMPOUND_DUPLE
)

# Audio playback module - optional import (requires sounddevice and numpy)
try:
    from chordelia.audio_playback import Playback, PlaybackNote, Waveform, play_scale, play_chord, play_melody, create_chord_notes
    _PLAYBACK_AVAILABLE = True
except ImportError:
    _PLAYBACK_AVAILABLE = False

# MIDI modules - optional import (requires mido)
try:
    from chordelia.midi_playback import MIDIChordPlayer, MIDIPlaybackNote, get_midi_ports, is_midi_available
    from chordelia.midi_playback import play_chord as midi_play_chord, play_melody as midi_play_melody
    from chordelia.midifile import MidiFile, MidiTrackInfo, load_midi_file, play_midi_file
    _MIDI_AVAILABLE = True
except ImportError:
    _MIDI_AVAILABLE = False

__version__ = "0.1.0"
__all__ = [
    "Interval",
    "IntervalQuality", 
    "Note",
    "NoteName",
    "Accidental",
    "Scale",
    "ScaleType",
    "Chord",
    "ChordQuality",
    "ChordExtension",
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
        "play_scale",
        "play_chord",
        "play_melody",
        "create_chord_notes",
    ])

# Add MIDI playback exports if available  
if _MIDI_AVAILABLE:
    __all__.extend([
        "MIDIChordPlayer",
        "MIDIPlaybackNote",
        "MidiFile",
        "MidiTrackInfo",
        "get_midi_ports", 
        "is_midi_available",
        "load_midi_file", 
        "midi_play_chord",
        "midi_play_melody",
        "play_midi_file",
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
