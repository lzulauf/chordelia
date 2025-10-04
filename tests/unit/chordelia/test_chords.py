"""
Test suite for the chords module.

Tests all chord functionality including construction, parsing,
extensions, inversions, and enharmonic spelling.
"""

import pytest
from chordelia.chords import Chord, ChordQuality, ChordExtension
from chordelia.chords import (
    major_chord, minor_chord, diminished_chord, augmented_chord,
    dominant_seventh_chord, major_seventh_chord, minor_seventh_chord,
    sus2_chord, sus4_chord
)
from chordelia.notes import Note, NoteName, Accidental
from chordelia.intervals import Interval, IntervalQuality


class TestChordQuality:
    """Test ChordQuality enum."""
    
    def test_chord_quality_values(self):
        """Test that chord qualities have correct string values."""
        assert ChordQuality.MAJOR.value == "major"
        assert ChordQuality.MINOR.value == "minor"
        assert ChordQuality.DIMINISHED.value == "diminished"
        assert ChordQuality.AUGMENTED.value == "augmented"
        assert ChordQuality.SUSPENDED_2.value == "sus2"
        assert ChordQuality.SUSPENDED_4.value == "sus4"
        assert ChordQuality.POWER.value == "power"


class TestChordExtension:
    """Test ChordExtension enum."""
    
    def test_chord_extension_values(self):
        """Test that chord extensions have correct values."""
        assert ChordExtension.SEVENTH.extension_str == "7"
        assert ChordExtension.MAJOR_SEVENTH.extension_str == "maj7"
        assert ChordExtension.NINTH.extension_str == "9"
        assert ChordExtension.MAJOR_NINTH.extension_str == "maj9"
        assert ChordExtension.ELEVENTH.extension_str == "11"
        assert ChordExtension.THIRTEENTH.extension_str == "13"


class TestChordCreation:
    """Test chord creation and initialization."""
    
    def test_create_major_chord(self):
        """Test creation of major chords."""
        c_major = Chord(Note(NoteName.C), ChordQuality.MAJOR)
        assert c_major.root.name == NoteName.C
        assert c_major.quality == ChordQuality.MAJOR
        assert c_major.extensions == ()
        assert c_major.additions == ()
        assert c_major.omissions == ()
        assert c_major.bass_note is None
        assert c_major.inversion is None
    
    def test_create_minor_chord(self):
        """Test creation of minor chords."""
        a_minor = Chord("A", ChordQuality.MINOR)
        assert a_minor.root.name == NoteName.A
        assert a_minor.quality == ChordQuality.MINOR
    
    def test_create_with_string_quality(self):
        """Test creating chords with string quality input."""
        c_major = Chord("C", "major")
        assert c_major.quality == ChordQuality.MAJOR
        
        a_minor = Chord("A", "minor")
        assert a_minor.quality == ChordQuality.MINOR
        
        b_dim = Chord("B", "diminished")
        assert b_dim.quality == ChordQuality.DIMINISHED
        
        c_aug = Chord("C", "augmented")
        assert c_aug.quality == ChordQuality.AUGMENTED
    
    def test_create_with_extensions(self):
        """Test creating chords with extensions."""
        c7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        assert ChordExtension.SEVENTH in c7.extensions
        
        cmaj7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])
        assert ChordExtension.MAJOR_SEVENTH in cmaj7.extensions
    
    def test_create_with_bass_note(self):
        """Test creating chords with bass notes (slash chords)."""
        c_over_e = Chord("C", ChordQuality.MAJOR, bass_note="E")
        assert c_over_e.bass_note.name == NoteName.E
        
        f_over_c = Chord("F", ChordQuality.MAJOR, bass_note=Note("C"))
        assert f_over_c.bass_note.name == NoteName.C
    
    def test_create_with_inversion(self):
        """Test creating chords with inversions."""
        c_first_inv = Chord("C", ChordQuality.MAJOR, inversion=1)
        assert c_first_inv.inversion == 1
        
        c_second_inv = Chord("C", ChordQuality.MAJOR, inversion=2)
        assert c_second_inv.inversion == 2


class TestChordFromString:
    """Test chord creation from string notation."""
    
    def test_simple_major_chords(self):
        """Test parsing simple major chords."""
        c = Chord.from_string("C")
        assert c.root.name == NoteName.C
        assert c.quality == ChordQuality.MAJOR
        
        cmaj = Chord.from_string("Cmaj")
        assert cmaj.quality == ChordQuality.MAJOR
        
        c_M = Chord.from_string("CM")
        assert c_M.quality == ChordQuality.MAJOR
    
    def test_minor_chords(self):
        """Test parsing minor chords."""
        cm = Chord.from_string("Cm")
        assert cm.root.name == NoteName.C
        assert cm.quality == ChordQuality.MINOR
        
        cmin = Chord.from_string("Cmin")
        assert cmin.quality == ChordQuality.MINOR
        
        c_minus = Chord.from_string("C-")
        assert c_minus.quality == ChordQuality.MINOR
    
    def test_diminished_chords(self):
        """Test parsing diminished chords."""
        cdim = Chord.from_string("Cdim")
        assert cdim.root.name == NoteName.C
        assert cdim.quality == ChordQuality.DIMINISHED
        
        c_dim_symbol = Chord.from_string("C°")
        assert c_dim_symbol.quality == ChordQuality.DIMINISHED
    
    def test_augmented_chords(self):
        """Test parsing augmented chords."""
        caug = Chord.from_string("Caug")
        assert caug.root.name == NoteName.C
        assert caug.quality == ChordQuality.AUGMENTED
        
        c_plus = Chord.from_string("C+")
        assert c_plus.quality == ChordQuality.AUGMENTED
    
    def test_suspended_chords(self):
        """Test parsing suspended chords."""
        csus2 = Chord.from_string("Csus2")
        assert csus2.root.name == NoteName.C
        assert csus2.quality == ChordQuality.SUSPENDED_2
        
        csus4 = Chord.from_string("Csus4")
        assert csus4.quality == ChordQuality.SUSPENDED_4
        
        csus = Chord.from_string("Csus")  # Should default to sus4
        assert csus.quality == ChordQuality.SUSPENDED_4
    
    def test_seventh_chords(self):
        """Test parsing seventh chords."""
        c7 = Chord.from_string("C7")
        assert c7.root.name == NoteName.C
        assert c7.quality == ChordQuality.MAJOR
        assert ChordExtension.SEVENTH in c7.extensions
        
        cmaj7 = Chord.from_string("Cmaj7")
        assert cmaj7.quality == ChordQuality.MAJOR
        assert ChordExtension.MAJOR_SEVENTH in cmaj7.extensions
        
        cm7 = Chord.from_string("Cm7")
        assert cm7.quality == ChordQuality.MINOR
        assert ChordExtension.SEVENTH in cm7.extensions
    
    def test_extended_chords(self):
        """Test parsing extended chords."""
        c9 = Chord.from_string("C9")
        assert c9.root.name == NoteName.C
        assert ChordExtension.NINTH in c9.extensions
        
        cmaj9 = Chord.from_string("Cmaj9")
        assert ChordExtension.MAJOR_NINTH in cmaj9.extensions
        
        c11 = Chord.from_string("C11")
        assert 11 in c11.extensions
        
        c13 = Chord.from_string("C13")
        assert 13 in c13.extensions
    
    def test_slash_chords(self):
        """Test parsing slash chords."""
        c_over_e = Chord.from_string("C/E")
        assert c_over_e.root.name == NoteName.C
        assert c_over_e.quality == ChordQuality.MAJOR
        assert c_over_e.bass_note.name == NoteName.E
        
        am_over_c = Chord.from_string("Am/C")
        assert am_over_c.root.name == NoteName.A
        assert am_over_c.quality == ChordQuality.MINOR
        assert am_over_c.bass_note.name == NoteName.C
    
    def test_added_tone_chords(self):
        """Test parsing chords with added tones."""
        cadd9 = Chord.from_string("C(add9)")
        assert cadd9.root.name == NoteName.C
        assert cadd9.quality == ChordQuality.MAJOR
        assert 9 in cadd9.additions
        
        cadd2 = Chord.from_string("C(add2)")
        assert 2 in cadd2.additions
    
    def test_accidental_roots(self):
        """Test parsing chords with accidental roots."""
        cs_major = Chord.from_string("C#")
        assert cs_major.root.name == NoteName.C
        assert cs_major.root.accidental == Accidental.SHARP
        
        bb_minor = Chord.from_string("Bbm")
        assert bb_minor.root.name == NoteName.B
        assert bb_minor.root.accidental == Accidental.FLAT
        assert bb_minor.quality == ChordQuality.MINOR
        
        fs_7 = Chord.from_string("F#7")
        assert fs_7.root.name == NoteName.F
        assert fs_7.root.accidental == Accidental.SHARP
        assert ChordExtension.SEVENTH in fs_7.extensions
    
    def test_complex_chord_strings(self):
        """Test parsing complex chord notations."""
        complex_chord = Chord.from_string("Cmaj7(add9)")
        assert complex_chord.root.name == NoteName.C
        assert complex_chord.quality == ChordQuality.MAJOR
        assert ChordExtension.MAJOR_SEVENTH in complex_chord.extensions
        assert 9 in complex_chord.additions


class TestChordNotes:
    """Test chord note generation."""
    
    def test_major_triad_notes(self):
        """Test major triad note generation."""
        c_major = Chord("C", ChordQuality.MAJOR)
        notes = c_major.notes
        
        expected_pitch_classes = [0, 4, 7]  # C, E, G
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_minor_triad_notes(self):
        """Test minor triad note generation."""
        a_minor = Chord("A", ChordQuality.MINOR)
        notes = a_minor.notes
        
        expected_pitch_classes = [9, 0, 4]  # A, C, E
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_diminished_triad_notes(self):
        """Test diminished triad note generation."""
        b_dim = Chord("B", ChordQuality.DIMINISHED)
        notes = b_dim.notes
        
        expected_pitch_classes = [11, 2, 5]  # B, D, F
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_augmented_triad_notes(self):
        """Test augmented triad note generation."""
        c_aug = Chord("C", ChordQuality.AUGMENTED)
        notes = c_aug.notes
        
        expected_pitch_classes = [0, 4, 8]  # C, E, G#
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_suspended_chord_notes(self):
        """Test suspended chord note generation."""
        csus2 = Chord("C", ChordQuality.SUSPENDED_2)
        notes = csus2.notes
        
        expected_pitch_classes = [0, 2, 7]  # C, D, G
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
        
        csus4 = Chord("C", ChordQuality.SUSPENDED_4)
        notes = csus4.notes
        
        expected_pitch_classes = [0, 5, 7]  # C, F, G
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_seventh_chord_notes(self):
        """Test seventh chord note generation."""
        c7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        notes = c7.notes
        
        expected_pitch_classes = [0, 4, 7, 10]  # C, E, G, Bb
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
        
        cmaj7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])
        notes = cmaj7.notes
        
        expected_pitch_classes = [0, 4, 7, 11]  # C, E, G, B
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_extended_chord_notes(self):
        """Test extended chord note generation."""
        c9 = Chord("C", ChordQuality.MAJOR, [ChordExtension.NINTH])
        notes = c9.notes
        
        # Should include 7th and 9th
        pitch_classes = [note.pitch_class for note in notes]
        assert 0 in pitch_classes  # Root
        assert 4 in pitch_classes  # Third
        assert 7 in pitch_classes  # Fifth
        assert 10 in pitch_classes  # Seventh
        assert 2 in pitch_classes  # Ninth (D)
    
    def test_added_tone_chord_notes(self):
        """Test chord notes with added tones."""
        cadd9 = Chord("C", ChordQuality.MAJOR, additions=[9])
        notes = cadd9.notes
        
        pitch_classes = [note.pitch_class for note in notes]
        assert 0 in pitch_classes  # Root
        assert 4 in pitch_classes  # Third
        assert 7 in pitch_classes  # Fifth
        assert 2 in pitch_classes  # Added ninth (D)
        # Should NOT include seventh
        assert 10 not in pitch_classes and 11 not in pitch_classes


class TestChordEnharmonicSpelling:
    """Test proper enharmonic spelling in chords."""
    
    def test_g_major_chord_spelling(self):
        """Test G major chord has proper enharmonic spelling."""
        g_major = Chord("G", ChordQuality.MAJOR)
        notes = g_major.notes
        
        note_names = [str(note) for note in notes]
        expected = ["G", "B", "D"]  # Should use natural notes
        
        assert note_names == expected
    
    def test_f_sharp_major_chord_spelling(self):
        """Test F# major chord enharmonic spelling."""
        fs_major = Chord("F#", ChordQuality.MAJOR)
        notes = fs_major.notes
        
        note_names = [str(note) for note in notes]
        # F# major should be F# A# C#
        expected = ["F#", "A#", "C#"]
        
        assert note_names == expected
    
    def test_b_flat_major_chord_spelling(self):
        """Test Bb major chord enharmonic spelling."""
        bb_major = Chord("Bb", ChordQuality.MAJOR)
        notes = bb_major.notes
        
        note_names = [str(note) for note in notes]
        expected = ["Bb", "D", "F"]
        
        assert note_names == expected
    
    def test_minor_chord_spelling(self):
        """Test minor chord enharmonic spelling."""
        d_minor = Chord("D", ChordQuality.MINOR)
        notes = d_minor.notes
        
        note_names = [str(note) for note in notes]
        expected = ["D", "F", "A"]
        
        assert note_names == expected


class TestChordWithOctave:
    """Test chords with octave information."""
    
    def test_chord_with_octave_root(self):
        """Test chord creation with octave information."""
        c4_major = Chord("C4", ChordQuality.MAJOR)
        notes = c4_major.notes
        
        # All notes should have octave information
        for note in notes:
            assert note.octave is not None
        
        # Root should be in octave 4
        assert notes[0].octave == 4
    
    def test_chord_octave_distribution(self):
        """Test that chord notes are distributed across octaves correctly."""
        c4_major = Chord("C4", ChordQuality.MAJOR)
        notes = c4_major.notes
        
        # For a simple triad starting at C4, all notes should be in octave 4
        octaves = [note.octave for note in notes]
        assert all(octave == 4 for octave in octaves)
    
    def test_extended_chord_octaves(self):
        """Test octave distribution in extended chords."""
        c4_maj9 = Chord("C4", ChordQuality.MAJOR, [ChordExtension.MAJOR_NINTH])
        notes = c4_maj9.notes
        
        # Extended notes should go into higher octaves
        for note in notes:
            assert note.octave in [4, 5]


class TestChordNotesWithOctaves:
    """Test that chord notes have correct octaves based on proper voice leading."""
    
    def test_major_chord_octave_distribution(self):
        """Test major chord octave distribution follows proper voice leading."""
        # B3 major chord: B3, D#4, F#4
        b3_major = Chord("B3", ChordQuality.MAJOR)
        notes = b3_major.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "B3"   # Root
        assert str(notes[1]) == "D#4"  # Third goes to next octave
        assert str(notes[2]) == "F#4"  # Fifth stays in next octave
        
        # C4 major chord: C4, E4, G4 (all in same octave)
        c4_major = Chord("C4", ChordQuality.MAJOR)
        notes = c4_major.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "C4"   # Root
        assert str(notes[1]) == "E4"   # Third in same octave
        assert str(notes[2]) == "G4"   # Fifth in same octave
        
        # G3 major chord: G3, B3, D4 (fifth crosses octave)
        g3_major = Chord("G3", ChordQuality.MAJOR)
        notes = g3_major.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "G3"   # Root
        assert str(notes[1]) == "B3"   # Third in same octave
        assert str(notes[2]) == "D4"   # Fifth goes to next octave
    
    def test_minor_chord_octave_distribution(self):
        """Test minor chord octave distribution follows proper voice leading."""
        # A3 minor chord: A3, C4, E4
        a3_minor = Chord("A3", ChordQuality.MINOR) 
        notes = a3_minor.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "A3"   # Root
        assert str(notes[1]) == "C4"   # Minor third goes to next octave
        assert str(notes[2]) == "E4"   # Fifth stays in next octave
        
        # D4 minor chord: D4, F4, A4
        d4_minor = Chord("D4", ChordQuality.MINOR)
        notes = d4_minor.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "D4"   # Root
        assert str(notes[1]) == "F4"   # Minor third in same octave
        assert str(notes[2]) == "A4"   # Fifth in same octave
    
    def test_seventh_chord_octave_distribution(self):
        """Test seventh chord octave distribution."""
        # C4 major 7th: C4, E4, G4, B4
        c4_maj7 = Chord("C4", ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])
        notes = c4_maj7.notes
        
        assert len(notes) == 4
        assert str(notes[0]) == "C4"   # Root
        assert str(notes[1]) == "E4"   # Third
        assert str(notes[2]) == "G4"   # Fifth
        assert str(notes[3]) == "B4"   # Major seventh
        
        # G3 dominant 7th: G3, B3, D4, F4
        g3_dom7 = Chord("G3", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        notes = g3_dom7.notes
        
        assert len(notes) == 4
        assert str(notes[0]) == "G3"   # Root
        assert str(notes[1]) == "B3"   # Third
        assert str(notes[2]) == "D4"   # Fifth crosses octave
        assert str(notes[3]) == "F4"   # Seventh stays in higher octave
    
    def test_extended_chord_octave_distribution(self):
        """Test extended chord octave distribution across multiple octaves."""
        # C4 major 9th: C4, E4, G4, B4, D5
        c4_maj9 = Chord("C4", ChordQuality.MAJOR, [ChordExtension.MAJOR_NINTH])
        notes = c4_maj9.notes
        
        assert len(notes) == 5
        assert str(notes[0]) == "C4"   # Root
        assert str(notes[1]) == "E4"   # Third
        assert str(notes[2]) == "G4"   # Fifth
        assert str(notes[3]) == "B4"   # Major seventh
        assert str(notes[4]) == "D5"   # Ninth goes to next octave
        
        # F3 minor 11th: F3, Ab3, C4, Eb4, G4, Bb4
        f3_min11 = Chord("F3", ChordQuality.MINOR, [ChordExtension.SEVENTH, ChordExtension.ELEVENTH])
        notes = f3_min11.notes
        
        # Should span F3 to Bb4
        assert notes[0].octave == 3  # Root in octave 3
        assert notes[-1].octave == 4  # Highest extension in octave 4
    
    def test_sharp_flat_chord_octave_distribution(self):
        """Test octave distribution with sharp and flat notes."""
        # F#3 major chord: F#3, A#3, C#4
        fs3_major = Chord("F#3", ChordQuality.MAJOR)
        notes = fs3_major.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "F#3"  # Root
        assert str(notes[1]) == "A#3"  # Third in same octave
        assert str(notes[2]) == "C#4"  # Fifth goes to next octave
        
        # Bb3 major chord: Bb3, D4, F4
        bb3_major = Chord("Bb3", ChordQuality.MAJOR)
        notes = bb3_major.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "Bb3"  # Root
        assert str(notes[1]) == "D4"   # Third goes to next octave
        assert str(notes[2]) == "F4"   # Fifth stays in next octave
    
    def test_diminished_augmented_chord_octaves(self):
        """Test octave distribution for diminished and augmented chords."""
        # C4 diminished: C4, Eb4, Gb4
        c4_dim = Chord("C4", ChordQuality.DIMINISHED)
        notes = c4_dim.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "C4"   # Root
        assert str(notes[1]) == "Eb4"  # Minor third
        assert str(notes[2]) == "Gb4"  # Diminished fifth
        
        # C4 augmented: C4, E4, G#4
        c4_aug = Chord("C4", ChordQuality.AUGMENTED)
        notes = c4_aug.notes
        
        assert len(notes) == 3
        assert str(notes[0]) == "C4"   # Root
        assert str(notes[1]) == "E4"   # Major third
        assert str(notes[2]) == "G#4"  # Augmented fifth


class TestChordInversions:
    """Test chord inversions."""
    
    def test_create_inversion(self):
        """Test creating chord inversions with copy constructor."""
        c_major = Chord("C", ChordQuality.MAJOR)
        first_inversion = c_major.with_inversion(1)
        
        assert first_inversion.inversion == 1
        assert first_inversion.root.name == NoteName.C  # Root doesn't change
        
        second_inversion = c_major.with_inversion(2)
        assert second_inversion.inversion == 2
    
    def test_inversion_method(self):
        """Test the with_inversion method creates new chord objects."""
        c_major = Chord("C", ChordQuality.MAJOR)
        first_inv = c_major.with_inversion(1)
        
        assert c_major.inversion != first_inv.inversion
        assert c_major != first_inv


class TestChordModification:
    """Test chord modification methods."""
    
    def test_add_extension(self):
        """Test adding extensions to chords with copy constructor."""
        c_major = Chord("C", ChordQuality.MAJOR)
        c7 = c_major.with_extension(ChordExtension.SEVENTH)
        
        assert ChordExtension.SEVENTH in c7.extensions
        assert c7.root == c_major.root
        assert c7.quality == c_major.quality
        
        # Original chord should be unchanged
        assert ChordExtension.SEVENTH not in c_major.extensions


class TestChordImmutability:
    """Test that Chord instances are immutable and copy-constructor methods work correctly."""
    
    def test_chord_immutability(self):
        """Test that chord attributes cannot be modified after creation."""
        chord = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        
        # Test that attributes cannot be modified
        with pytest.raises(AttributeError):
            chord.root = Note("D")
        
        with pytest.raises(AttributeError):
            chord.quality = ChordQuality.MINOR
        
        with pytest.raises(AttributeError):
            chord.extensions = [ChordExtension.NINTH]
        
        with pytest.raises(AttributeError):
            chord.bass_note = Note("E")
        
        with pytest.raises(AttributeError):
            chord.inversion = 1
    
    def test_immutable_collections(self):
        """Test that collections returned by properties are immutable tuples."""
        chord = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH, ChordExtension.NINTH])
        
        # Test that extensions returns a tuple
        extensions = chord.extensions
        assert isinstance(extensions, tuple)
        assert ChordExtension.SEVENTH in extensions
        assert ChordExtension.NINTH in extensions
        
        # Test that notes returns a tuple
        notes = chord.notes
        assert isinstance(notes, tuple)
        assert len(notes) >= 3  # At least root, third, fifth
        
        # Test that additions and omissions return tuples
        additions = chord.additions
        assert isinstance(additions, tuple)
        
        omissions = chord.omissions
        assert isinstance(omissions, tuple)
    
    def test_with_extension_copy_constructor(self):
        """Test with_extension copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Add extension
        with_seventh = original.with_extension(ChordExtension.SEVENTH)
        
        # Should return new instance
        assert with_seventh is not original
        
        # Original should be unchanged
        assert ChordExtension.SEVENTH not in original.extensions
        
        # New chord should have the extension
        assert ChordExtension.SEVENTH in with_seventh.extensions
        
        # Other properties should be preserved
        assert with_seventh.root == original.root
        assert with_seventh.quality == original.quality
        assert with_seventh.bass_note == original.bass_note
        assert with_seventh.inversion == original.inversion
    
    def test_with_root_copy_constructor(self):
        """Test with_root copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        
        # Change root
        with_new_root = original.with_root("G")
        
        # Should return new instance
        assert with_new_root is not original
        
        # Original should be unchanged
        assert original.root.name == NoteName.C
        
        # New chord should have the new root
        assert with_new_root.root.name == NoteName.G
        
        # Other properties should be preserved
        assert with_new_root.quality == original.quality
        assert with_new_root.extensions == original.extensions
        assert with_new_root.bass_note == original.bass_note
        assert with_new_root.inversion == original.inversion
    
    def test_with_bass_copy_constructor(self):
        """Test with_bass copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Add bass note
        with_bass = original.with_bass("E")
        
        # Should return new instance
        assert with_bass is not original
        
        # Original should be unchanged
        assert original.bass_note is None
        
        # New chord should have the bass note
        assert with_bass.bass_note.name == NoteName.E
        
        # Other properties should be preserved
        assert with_bass.root == original.root
        assert with_bass.quality == original.quality
        assert with_bass.extensions == original.extensions
        assert with_bass.inversion == original.inversion
    
    def test_with_inversion_copy_constructor(self):
        """Test with_inversion copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Set inversion
        with_inversion = original.with_inversion(1)
        
        # Should return new instance
        assert with_inversion is not original
        
        # Original should be unchanged
        assert original.inversion is None
        
        # New chord should have the inversion
        assert with_inversion.inversion == 1
        
        # Other properties should be preserved
        assert with_inversion.root == original.root
        assert with_inversion.quality == original.quality
        assert with_inversion.extensions == original.extensions
        assert with_inversion.bass_note == original.bass_note
    
    def test_with_method_generic_copy_constructor(self):
        """Test the generic with_() copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Modify multiple properties
        modified = original.with_(
            root="G",
            quality=ChordQuality.MINOR,
            extensions=[ChordExtension.SEVENTH],
            bass_note="D"
        )
        
        # Should return new instance
        assert modified is not original
        
        # Original should be unchanged
        assert original.root.name == NoteName.C
        assert original.quality == ChordQuality.MAJOR
        assert len(original.extensions) == 0
        assert original.bass_note is None
        
        # New chord should have all modifications
        assert modified.root.name == NoteName.G
        assert modified.quality == ChordQuality.MINOR
        assert ChordExtension.SEVENTH in modified.extensions
        assert modified.bass_note.name == NoteName.D
    
    def test_chaining_copy_constructors(self):
        """Test chaining copy constructor methods."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Chain multiple modifications
        final = (original
                .with_extension(ChordExtension.SEVENTH)
                .with_bass("E")
                .with_inversion(1))
        
        # Each should return a new instance
        assert final is not original
        
        # Original should be completely unchanged
        assert original.root.name == NoteName.C
        assert original.quality == ChordQuality.MAJOR
        assert len(original.extensions) == 0
        assert original.bass_note is None
        assert original.inversion is None
        
        # Final should have all modifications
        assert final.root.name == NoteName.C
        assert final.quality == ChordQuality.MAJOR
        assert ChordExtension.SEVENTH in final.extensions
        assert final.bass_note.name == NoteName.E
        assert final.inversion == 1


class TestChordTransposition:
    """Test chord transposition."""
    
    def test_transpose_major_chord(self):
        """Test transposing major chords."""
        c_major = Chord("C", ChordQuality.MAJOR)
        perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
        
        g_major = c_major.transpose(perfect_fifth)
        
        assert g_major.root.name == NoteName.G
        assert g_major.quality == ChordQuality.MAJOR
        assert g_major.extensions == c_major.extensions
    
    def test_transpose_with_bass_note(self):
        """Test transposing chords with bass notes."""
        c_over_e = Chord("C", ChordQuality.MAJOR, bass_note="E")
        major_second = Interval(IntervalQuality.MAJOR, 2)
        
        d_over_fs = c_over_e.transpose(major_second)
        
        assert d_over_fs.root.name == NoteName.D
        assert d_over_fs.bass_note.name == NoteName.F
        assert d_over_fs.bass_note.accidental == Accidental.SHARP
    
    def test_transpose_extended_chord(self):
        """Test transposing extended chords."""
        cmaj7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])
        minor_third = Interval(IntervalQuality.MINOR, 3)
        
        eb_maj7 = cmaj7.transpose(minor_third)
        
        assert eb_maj7.root.name == NoteName.E
        assert eb_maj7.root.accidental == Accidental.FLAT
        assert eb_maj7.quality == ChordQuality.MAJOR
        assert ChordExtension.MAJOR_SEVENTH in eb_maj7.extensions


class TestChordFactoryFunctions:
    """Test convenience factory functions."""
    
    def test_major_chord_factory(self):
        """Test major_chord factory function."""
        c_major = major_chord("C")
        assert isinstance(c_major, Chord)
        assert c_major.quality == ChordQuality.MAJOR
        assert c_major.root.name == NoteName.C
    
    def test_minor_chord_factory(self):
        """Test minor_chord factory function."""
        a_minor = minor_chord("A")
        assert isinstance(a_minor, Chord)
        assert a_minor.quality == ChordQuality.MINOR
        assert a_minor.root.name == NoteName.A
    
    def test_diminished_chord_factory(self):
        """Test diminished_chord factory function."""
        b_dim = diminished_chord("B")
        assert b_dim.quality == ChordQuality.DIMINISHED
        assert b_dim.root.name == NoteName.B
    
    def test_augmented_chord_factory(self):
        """Test augmented_chord factory function."""
        c_aug = augmented_chord("C")
        assert c_aug.quality == ChordQuality.AUGMENTED
        assert c_aug.root.name == NoteName.C
    
    def test_seventh_chord_factories(self):
        """Test seventh chord factory functions."""
        c7 = dominant_seventh_chord("C")
        assert c7.quality == ChordQuality.MAJOR
        assert c7.root.name == NoteName.C
        assert ChordExtension.SEVENTH in c7.extensions
        
        cmaj7 = major_seventh_chord("C")
        assert ChordExtension.MAJOR_SEVENTH in cmaj7.extensions
        
        cm7 = minor_seventh_chord("C")
        assert cm7.quality == ChordQuality.MINOR
        assert ChordExtension.SEVENTH in cm7.extensions
    
    def test_suspended_chord_factories(self):
        """Test suspended chord factory functions."""
        csus2 = sus2_chord("C")
        assert csus2.quality == ChordQuality.SUSPENDED_2
        
        csus4 = sus4_chord("C")
        assert csus4.quality == ChordQuality.SUSPENDED_4


class TestChordEquality:
    """Test chord equality and hashing."""
    
    def test_chord_equality(self):
        """Test chord equality comparison."""
        c_major1 = Chord("C", ChordQuality.MAJOR)
        c_major2 = Chord("C", ChordQuality.MAJOR)
        g_major = Chord("G", ChordQuality.MAJOR)
        c_minor = Chord("C", ChordQuality.MINOR)
        
        assert c_major1 == c_major2
        assert c_major1 != g_major
        assert c_major1 != c_minor
    
    def test_chord_equality_with_extensions(self):
        """Test equality with extensions."""
        c7_1 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        c7_2 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        cmaj7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])
        
        assert c7_1 == c7_2
        assert c7_1 != cmaj7
    
    def test_chord_hashing(self):
        """Test that chords can be used in sets and dicts."""
        chords = {
            Chord("C", ChordQuality.MAJOR),
            Chord("G", ChordQuality.MAJOR),
            Chord("C", ChordQuality.MAJOR),  # Duplicate
        }
        
        assert len(chords) == 2  # Duplicate should be removed


class TestChordStringRepresentation:
    """Test string representations of chords."""
    
    def test_chord_name_generation(self):
        """Test chord name/symbol generation."""
        c_major = Chord("C", ChordQuality.MAJOR)
        assert c_major.name == "C"
        
        c_minor = Chord("C", ChordQuality.MINOR)
        assert c_minor.name == "Cm"
        
        c_dim = Chord("C", ChordQuality.DIMINISHED)
        assert c_dim.name == "C°"
        
        c_aug = Chord("C", ChordQuality.AUGMENTED)
        assert c_aug.name == "C+"
        
        csus2 = Chord("C", ChordQuality.SUSPENDED_2)
        assert csus2.name == "Csus2"
        
        csus4 = Chord("C", ChordQuality.SUSPENDED_4)
        assert csus4.name == "Csus4"
    
    def test_chord_name_with_extensions(self):
        """Test chord names with extensions."""
        c7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        assert c7.name == "C7"
        
        cmaj7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.MAJOR_SEVENTH])
        assert cmaj7.name == "Cmaj7"
        
        cm7 = Chord("C", ChordQuality.MINOR, [ChordExtension.SEVENTH])
        assert cm7.name == "Cm7"
    
    def test_chord_name_with_additions(self):
        """Test chord names with additions."""
        cadd9 = Chord("C", ChordQuality.MAJOR, additions=[9])
        assert "(add9)" in cadd9.name
    
    def test_chord_name_with_bass(self):
        """Test chord names with bass notes."""
        c_over_e = Chord("C", ChordQuality.MAJOR, bass_note="E")
        assert c_over_e.name == "C/E"
        
        am_over_c = Chord("A", ChordQuality.MINOR, bass_note="C")
        assert am_over_c.name == "Am/C"
    
    def test_str_representation(self):
        """Test __str__ method."""
        c_major = Chord("C", ChordQuality.MAJOR)
        assert str(c_major) == "C"
        
        c7 = Chord("C", ChordQuality.MAJOR, [ChordExtension.SEVENTH])
        assert str(c7) == "C7"
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        c_major = Chord("C", ChordQuality.MAJOR)
        repr_str = repr(c_major)
        
        assert "Chord" in repr_str
        assert "C" in repr_str
        assert "Notes:" in repr_str


class TestChordPatterns:
    """Test chord interval patterns."""
    
    def test_chord_patterns_dict(self):
        """Test that chord patterns are correctly defined in the optimized structure."""
        from chordelia.chords import _CHORD_INTERVALS
        
        assert _CHORD_INTERVALS[ChordQuality.MAJOR] == (0, 4, 7)
        assert _CHORD_INTERVALS[ChordQuality.MINOR] == (0, 3, 7)
        assert _CHORD_INTERVALS[ChordQuality.DIMINISHED] == (0, 3, 6)
        assert _CHORD_INTERVALS[ChordQuality.AUGMENTED] == (0, 4, 8)
        assert _CHORD_INTERVALS[ChordQuality.SUSPENDED_2] == (0, 2, 7)
        assert _CHORD_INTERVALS[ChordQuality.SUSPENDED_4] == (0, 5, 7)
        assert _CHORD_INTERVALS[ChordQuality.POWER] == (0, 7)
    
    def test_extension_intervals_dict(self):
        """Test that extension intervals are correctly defined."""
        assert Chord.EXTENSION_INTERVALS[ChordExtension.SEVENTH] == 10
        assert Chord.EXTENSION_INTERVALS[ChordExtension.MAJOR_SEVENTH] == 11
        assert Chord.EXTENSION_INTERVALS[ChordExtension.NINTH] == 14
        assert Chord.EXTENSION_INTERVALS[ChordExtension.ELEVENTH] == 17
        assert Chord.EXTENSION_INTERVALS[ChordExtension.THIRTEENTH] == 21


class TestChordEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_power_chord(self):
        """Test power chord (just root and fifth)."""
        c5 = Chord("C", ChordQuality.POWER)
        notes = c5.notes
        
        expected_pitch_classes = [0, 7]  # C, G
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_chord_with_many_extensions(self):
        """Test chord with multiple extensions."""
        complex_chord = Chord(
            "C", ChordQuality.MAJOR,
            extensions=[ChordExtension.MAJOR_SEVENTH, ChordExtension.NINTH],
            additions=[11]
        )
        
        notes = complex_chord.notes
        pitch_classes = set(note.pitch_class for note in notes)
        
        # Should contain root, third, fifth, major seventh, ninth, eleventh
        assert 0 in pitch_classes  # Root
        assert 4 in pitch_classes  # Third
        assert 7 in pitch_classes  # Fifth
        assert 11 in pitch_classes  # Major seventh
        assert 2 in pitch_classes  # Ninth
        assert 5 in pitch_classes  # Eleventh (same as fourth)
    
    def test_chord_string_parsing_edge_cases(self):
        """Test edge cases in chord string parsing."""
        # Test with double accidentals
        chord = Chord.from_string("F##")
        assert chord.root.name == NoteName.F
        assert chord.root.accidental == Accidental.DOUBLE_SHARP
        
        # Test with complex notation
        complex_chord = Chord.from_string("Bb13")
        assert complex_chord.root.name == NoteName.B
        assert complex_chord.root.accidental == Accidental.FLAT
        assert 13 in complex_chord.extensions
    
    def test_chord_lazy_initialization(self):
        """Test that chord notes are calculated lazily with cached_property."""
        c_major = Chord("C", ChordQuality.MAJOR)
        
        # Notes should not be cached until accessed
        assert 'notes' not in c_major.__dict__
        
        # Access notes
        notes = c_major.notes
        
        # Now notes should be cached in __dict__
        assert 'notes' in c_major.__dict__
        assert c_major.__dict__['notes'] == notes
        
        # Second access should return the same object
        notes2 = c_major.notes
        assert notes2 is notes
    
    def test_invalid_chord_string_format(self):
        """Test error handling for invalid chord strings."""
        with pytest.raises(ValueError):
            Chord.from_string("H")  # Invalid root note
        
        with pytest.raises(ValueError):
            Chord.from_string("")  # Empty string
        
        # These should not raise errors but might have unexpected results
        # Testing that the parser is robust
        try:
            Chord.from_string("C#####")  # Too many sharps
        except ValueError:
            pass  # Expected to fail
        
        try:
            Chord.from_string("Cbbbb")  # Too many flats
        except ValueError:
            pass  # Expected to fail
