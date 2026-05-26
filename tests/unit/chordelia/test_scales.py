"""
Test suite for the scales module.

Tests all scale functionality including construction, note generation,
enharmonic spelling, modes, and transposition.
"""

import pytest
from chordelia.scales import Scale, ScaleType, CustomScale
from chordelia.degrees import Degree
from chordelia.scales import (
    major_scale, minor_scale, harmonic_minor_scale, melodic_minor_scale,
    dorian_scale, mixolydian_scale, pentatonic_major_scale, 
    pentatonic_minor_scale, blues_scale
)
from chordelia.chords import Chord, ChordQuality
from chordelia.notes import Note, NoteName, Accidental
from chordelia.intervals import Interval, IntervalQuality


class TestScaleType:
    """Test ScaleType enum."""
    
    def test_scale_type_values(self):
        """Test that scale types have correct string values."""
        assert ScaleType.MAJOR.value == "major"
        assert ScaleType.NATURAL_MINOR.value == "natural_minor"
        assert ScaleType.HARMONIC_MINOR.value == "harmonic_minor"
        assert ScaleType.DORIAN.value == "dorian"
        assert ScaleType.PENTATONIC_MAJOR.value == "pentatonic_major"


class TestScaleCreation:
    """Test scale creation and initialization."""
    
    def test_create_major_scale(self):
        """Test creation of major scales."""
        c_major = Scale(Note(NoteName.C), ScaleType.MAJOR)
        assert c_major.root.name == NoteName.C
        assert c_major.scale_type == ScaleType.MAJOR
        
        g_major = Scale("G", ScaleType.MAJOR)
        assert g_major.root.name == NoteName.G
        assert g_major.scale_type == ScaleType.MAJOR
    
    def test_create_minor_scale(self):
        """Test creation of minor scales."""
        a_minor = Scale(Note(NoteName.A), ScaleType.NATURAL_MINOR)
        assert a_minor.root.name == NoteName.A
        assert a_minor.scale_type == ScaleType.NATURAL_MINOR
    
    def test_create_from_string(self):
        """Test creating scales with string inputs."""
        d_major = Scale("D", "major")
        assert d_major.root.name == NoteName.D
        assert d_major.scale_type == ScaleType.MAJOR
        
        f_minor = Scale("F", "natural_minor")
        assert f_minor.root.name == NoteName.F
        assert f_minor.scale_type == ScaleType.NATURAL_MINOR
    
    def test_invalid_scale_type(self):
        """Test that invalid scale types raise errors."""
        with pytest.raises(ValueError):
            Scale("C", "invalid_scale")


class TestScalePatterns:
    """Test scale interval patterns."""
    
    def test_major_scale_pattern(self):
        """Test major scale interval pattern."""
        c_major = Scale("C", ScaleType.MAJOR)
        expected_pattern = (0, 2, 4, 5, 7, 9, 11)
        assert c_major.pattern == expected_pattern
    
    def test_natural_minor_pattern(self):
        """Test natural minor scale interval pattern."""
        a_minor = Scale("A", ScaleType.NATURAL_MINOR)
        expected_pattern = (0, 2, 3, 5, 7, 8, 10)
        assert a_minor.pattern == expected_pattern
    
    def test_harmonic_minor_pattern(self):
        """Test harmonic minor scale interval pattern."""
        a_harmonic = Scale("A", ScaleType.HARMONIC_MINOR)
        expected_pattern = (0, 2, 3, 5, 7, 8, 11)
        assert a_harmonic.pattern == expected_pattern
    
    def test_dorian_pattern(self):
        """Test Dorian mode interval pattern."""
        d_dorian = Scale("D", ScaleType.DORIAN)
        expected_pattern = (0, 2, 3, 5, 7, 9, 10)
        assert d_dorian.pattern == expected_pattern
    
    def test_pentatonic_major_pattern(self):
        """Test major pentatonic scale interval pattern."""
        c_pent = Scale("C", ScaleType.PENTATONIC_MAJOR)
        expected_pattern = (0, 2, 4, 7, 9)
        assert c_pent.pattern == expected_pattern


class TestScaleNotes:
    """Test scale note generation and enharmonic spelling."""
    
    def test_c_major_notes(self):
        """Test C major scale notes."""
        c_major = Scale("C", ScaleType.MAJOR)
        notes = c_major.notes
        
        expected_names = [NoteName.C, NoteName.D, NoteName.E, NoteName.F,
                         NoteName.G, NoteName.A, NoteName.B]
        
        assert len(notes) == 7
        for i, note in enumerate(notes):
            assert note.name == expected_names[i]
            assert note.accidental == Accidental.NATURAL
    
    def test_g_major_notes(self):
        """Test G major scale notes with proper enharmonic spelling."""
        g_major = Scale("G", ScaleType.MAJOR)
        notes = g_major.notes
        
        # G major has F#
        expected = ["G", "A", "B", "C", "D", "E", "F#"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
    
    def test_f_major_notes(self):
        """Test F major scale notes with proper enharmonic spelling."""
        f_major = Scale("F", ScaleType.MAJOR)
        notes = f_major.notes
        
        # F major has Bb
        expected = ["F", "G", "A", "Bb", "C", "D", "E"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
    
    def test_c_sharp_major_notes(self):
        """Test C# major scale notes with many sharps."""
        cs_major = Scale("C#", ScaleType.MAJOR)
        notes = cs_major.notes
        
        # C# major: C# D# E# F# G# A# B#
        expected = ["C#", "D#", "E#", "F#", "G#", "A#", "B#"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
    
    def test_a_minor_notes(self):
        """Test A natural minor scale notes."""
        a_minor = Scale("A", ScaleType.NATURAL_MINOR)
        notes = a_minor.notes
        
        expected = ["A", "B", "C", "D", "E", "F", "G"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
    
    def test_a_harmonic_minor_notes(self):
        """Test A harmonic minor scale notes."""
        a_harmonic = Scale("A", ScaleType.HARMONIC_MINOR)
        notes = a_harmonic.notes
        
        # A harmonic minor has G#
        expected = ["A", "B", "C", "D", "E", "F", "G#"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
    
    def test_b_flat_major_notes(self):
        """Test Bb major scale notes."""
        bb_major = Scale("Bb", ScaleType.MAJOR)
        notes = bb_major.notes
        
        # Bb major: Bb C D Eb F G A
        expected = ["Bb", "C", "D", "Eb", "F", "G", "A"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
    
    def test_pentatonic_scales(self):
        """Test pentatonic scale notes."""
        c_pent_major = Scale("C", ScaleType.PENTATONIC_MAJOR)
        notes = c_pent_major.notes
        
        expected = ["C", "D", "E", "G", "A"]
        actual = [str(note) for note in notes]
        
        assert actual == expected
        
        a_pent_minor = Scale("A", ScaleType.PENTATONIC_MINOR)
        notes = a_pent_minor.notes
        
        expected = ["A", "C", "D", "E", "G"]
        actual = [str(note) for note in notes]
        
        assert actual == expected


class TestScaleWithOctave:
    """Test scales with octave information."""
    
    def test_scale_with_octave_information(self):
        """Test that scales preserve octave information."""
        c4_major = Scale("C4", ScaleType.MAJOR)
        notes = c4_major.notes
        
        # All notes should have octave 4 except those that cross into octave 5
        assert notes[0].octave == 4  # C4
        assert notes[1].octave == 4  # D4
        assert notes[2].octave == 4  # E4
        assert notes[3].octave == 4  # F4
        assert notes[4].octave == 4  # G4
        assert notes[5].octave == 4  # A4
        assert notes[6].octave == 4  # B4
    
    def test_scale_crossing_octave(self):
        """Test scales that cross octave boundaries."""
        b4_major = Scale("B4", ScaleType.MAJOR)
        notes = b4_major.notes
        
        # Starting from B4, some notes will be in octave 5
        assert notes[0].octave == 4  # B4
        # Subsequent notes may be in octave 5 depending on the pattern
        for note in notes:
            assert note.octave in [4, 5]
    
    def test_scale_notes_ascending_order(self):
        """Test that scale notes are in ascending pitch order."""
        # Test with C4 major scale
        c4_major = Scale("C4", ScaleType.MAJOR)
        notes = c4_major.notes
        
        # All notes should have MIDI numbers (since they have octaves)
        midi_numbers = [note.midi_number for note in notes]
        assert all(midi is not None for midi in midi_numbers), "All notes should have MIDI numbers"
        
        # MIDI numbers should be in ascending order
        for i in range(len(midi_numbers) - 1):
            current_midi = midi_numbers[i]
            next_midi = midi_numbers[i + 1]
            assert next_midi > current_midi, f"Scale notes should be in ascending order: {notes[i]} ({current_midi}) should be less than {notes[i+1]} ({next_midi})"
        
        # Test with a scale that crosses octave boundaries
        b4_major = Scale("B4", ScaleType.MAJOR)
        b4_notes = b4_major.notes
        b4_midi_numbers = [note.midi_number for note in b4_notes]
        
        # Should still be in ascending order
        for i in range(len(b4_midi_numbers) - 1):
            current_midi = b4_midi_numbers[i]
            next_midi = b4_midi_numbers[i + 1]
            assert next_midi > current_midi, f"B4 major scale notes should be in ascending order: {b4_notes[i]} ({current_midi}) should be less than {b4_notes[i+1]} ({next_midi})"


class TestScaleDegrees:
    """Test scale degree access."""
    
    def test_scale_degree_access(self):
        """Test accessing specific scale degrees."""
        c_major = Scale("C", ScaleType.MAJOR)
        
        assert str(c_major.degree(1)) == "C"  # Root
        assert str(c_major.degree(2)) == "D"  # Second
        assert str(c_major.degree(3)) == "E"  # Third
        assert str(c_major.degree(4)) == "F"  # Fourth
        assert str(c_major.degree(5)) == "G"  # Fifth
        assert str(c_major.degree(6)) == "A"  # Sixth
        assert str(c_major.degree(7)) == "B"  # Seventh

    def test_scale_degree_access_with_degree_like_inputs(self):
        """Degree APIs should accept ints, Degree objects, and Roman strings."""
        c_major = Scale("C", ScaleType.MAJOR)

        assert str(c_major.degree(Degree(4))) == "F"
        assert str(c_major.degree("V")) == "G"
        assert str(c_major.degree("ii")) == "D"
    
    def test_invalid_scale_degree(self):
        """Test that invalid scale degrees raise errors."""
        c_major = Scale("C", ScaleType.MAJOR)
        
        with pytest.raises(ValueError):
            c_major.degree(0)
        
        with pytest.raises(ValueError):
            c_major.degree(8)  # Only 7 degrees in major scale
    
    def test_pentatonic_scale_degrees(self):
        """Test scale degrees for pentatonic scales."""
        c_pent = Scale("C", ScaleType.PENTATONIC_MAJOR)
        
        assert str(c_pent.degree(1)) == "C"
        assert str(c_pent.degree(2)) == "D"
        assert str(c_pent.degree(3)) == "E"
        assert str(c_pent.degree(4)) == "G"
        assert str(c_pent.degree(5)) == "A"
        
        with pytest.raises(ValueError):
            c_pent.degree(6)  # Only 5 degrees in pentatonic


class TestScaleModes:
    """Test scale mode generation."""
    
    def test_major_scale_modes(self):
        """Test modes of the major scale."""
        c_major = Scale("C", ScaleType.MAJOR)
        
        # Second mode (Dorian) starting from D
        d_dorian = c_major.mode_from_degree(2)
        assert str(d_dorian.root) == "D"
        
        # Fifth mode (Mixolydian) starting from G
        g_mixolydian = c_major.mode_from_degree(5)
        assert str(g_mixolydian.root) == "G"
        
        # Sixth mode (Aeolian/Natural Minor) starting from A
        a_aeolian = c_major.mode_from_degree(6)
        assert str(a_aeolian.root) == "A"

    def test_mode_from_degree_accepts_degree_like(self):
        """Mode selection should accept DegreeLike values."""
        c_major = Scale("C", ScaleType.MAJOR)

        assert str(c_major.mode_from_degree(Degree(2)).root) == "D"
        assert str(c_major.mode_from_degree("iii").root) == "E"
    
    def test_mode_patterns(self):
        """Test that modes have correct interval patterns."""
        c_major = Scale("C", ScaleType.MAJOR)
        d_dorian = c_major.mode_from_degree(2)
        
        # Dorian pattern should be (0, 2, 3, 5, 7, 9, 10)
        expected_dorian = (0, 2, 3, 5, 7, 9, 10)
        assert d_dorian.pattern == expected_dorian
    
    def test_invalid_mode_degree(self):
        """Test that invalid mode degrees raise errors."""
        c_major = Scale("C", ScaleType.MAJOR)
        
        with pytest.raises(ValueError):
            c_major.mode_from_degree(0)
        
        with pytest.raises(ValueError):
            c_major.mode_from_degree(8)


class TestScaleTransposition:
    """Test scale transposition."""
    
    def test_transpose_major_scale(self):
        """Test transposing major scales."""
        c_major = Scale("C", ScaleType.MAJOR)
        perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
        
        g_major = c_major.transpose(perfect_fifth)
        
        assert str(g_major.root) == "G"
        assert g_major.scale_type == ScaleType.MAJOR
        
        # Check that notes are correct
        g_major_notes = [str(note) for note in g_major.notes]
        expected = ["G", "A", "B", "C", "D", "E", "F#"]
        assert g_major_notes == expected
    
    def test_transpose_minor_scale(self):
        """Test transposing minor scales."""
        a_minor = Scale("A", ScaleType.NATURAL_MINOR)
        major_third = Interval(IntervalQuality.MAJOR, 3)
        
        c_sharp_minor = a_minor.transpose(major_third)
        
        assert str(c_sharp_minor.root) == "C#"
        assert c_sharp_minor.scale_type == ScaleType.NATURAL_MINOR


class TestScaleImmutability:
    """Test that Scale instances are immutable."""
    
    def test_scale_immutability(self):
        """Test that scale attributes cannot be modified after creation."""
        scale = Scale("C", ScaleType.MAJOR)
        
        # Test that attributes cannot be modified
        with pytest.raises(AttributeError):
            scale.root = Note("D")
        
        with pytest.raises(AttributeError):
            scale.scale_type = ScaleType.MINOR
    
    def test_immutable_collections(self):
        """Test that collections returned by properties are immutable tuples."""
        scale = Scale("C", ScaleType.MAJOR)
        
        # Test that notes returns an immutable tuple
        notes = scale.notes
        assert isinstance(notes, tuple)
        assert len(notes) == 7  # Major scale has 7 notes
        
        # Test that pattern returns an immutable tuple
        pattern = scale.pattern
        assert isinstance(pattern, tuple)
        assert pattern == (0, 2, 4, 5, 7, 9, 11)  # Major scale pattern
    
    def test_transpose_returns_new_instance(self):
        """Test that transpose returns a new immutable Scale instance."""
        original = Scale("C", ScaleType.MAJOR)
        perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
        
        transposed = original.transpose(perfect_fifth)
        
        # Should return new instance
        assert transposed is not original
        
        # Original should be unchanged
        assert original.root.name == NoteName.C
        assert original.scale_type == ScaleType.MAJOR
        
        # New scale should have the transposition
        assert transposed.root.name == NoteName.G
        assert transposed.scale_type == ScaleType.MAJOR
    
    def test_mode_from_degree_returns_new_instance(self):
        """Test that mode_from_degree returns a new immutable Scale instance."""
        original = Scale("C", ScaleType.MAJOR)
        
        # Get Dorian mode (2nd mode)
        dorian = original.mode_from_degree(2)
        
        # Should return new instance
        assert dorian is not original
        
        # Original should be unchanged
        assert original.root.name == NoteName.C
        assert original.scale_type == ScaleType.MAJOR
        
        # New scale should be the mode
        assert dorian.root.name == NoteName.D
        assert dorian.scale_type is None  # CustomScale has no predefined scale_type
    
    def test_existing_methods_preserve_immutability(self):
        """Test that existing scale methods already preserve immutability correctly."""
        original = Scale("C", ScaleType.MAJOR)
        
        # Test various operations that should return new instances
        transposed = original.transpose(Interval(IntervalQuality.PERFECT, 5))
        mode = original.mode_from_degree(3)  # Phrygian
        
        # All should be different instances
        assert original is not transposed
        assert original is not mode
        assert transposed is not mode
        
        # Original should be completely unchanged
        assert original.root.name == NoteName.C
        assert original.scale_type == ScaleType.MAJOR
        assert len(original.notes) == 7
        assert original.pattern == (0, 2, 4, 5, 7, 9, 11)


class TestScaleNoteContainment:
    """Test checking if notes are in scales."""
    
    def test_major_scale_contains_notes(self):
        """Test checking note containment in major scales."""
        c_major = Scale("C", ScaleType.MAJOR)
        
        # All natural notes should be in C major
        assert c_major.contains_note(Note("C"))
        assert c_major.contains_note(Note("D"))
        assert c_major.contains_note(Note("E"))
        assert c_major.contains_note(Note("F"))
        assert c_major.contains_note(Note("G"))
        assert c_major.contains_note(Note("A"))
        assert c_major.contains_note(Note("B"))
        
        # Sharps and flats should not be in C major
        assert not c_major.contains_note(Note("C#"))
        assert not c_major.contains_note(Note("Bb"))
    
    def test_scale_degree_lookup(self):
        """Test finding scale degrees for notes."""
        c_major = Scale("C", ScaleType.MAJOR)
        
        assert c_major.degree_for_chord_root(Note("C")) == Degree(1)
        assert c_major.degree_for_chord_root(Note("E")) == Degree(3)
        assert c_major.degree_for_chord_root(Note("G")) == Degree(5)
        
        # Note not in scale should return None
        assert c_major.degree_for_chord_root(Note("F#")) is None


class TestScaleDegreeHarmonization:
    """Test scale harmonization helpers that use degree inputs."""

    @pytest.mark.parametrize(
        "degree, expected_root, expected_quality",
        [
            pytest.param(1, "C", ChordQuality.MAJOR, id="major-I"),
            pytest.param("ii", "D", ChordQuality.MINOR, id="major-ii"),
            pytest.param("vii°", "B", ChordQuality.DIMINISHED, id="major-vii-dim"),
            pytest.param(Degree(5), "G", ChordQuality.MAJOR, id="major-V"),
        ],
    )
    def test_chord_for_degree_major(self, degree, expected_root, expected_quality):
        c_major = Scale("C", ScaleType.MAJOR)

        chord = c_major.chord_for_degree(degree)
        assert isinstance(chord, Chord)
        assert str(chord.root) == expected_root
        assert chord.quality == expected_quality

    @pytest.mark.parametrize(
        "degree, expected_root, expected_quality",
        [
            pytest.param(1, "A", ChordQuality.MINOR, id="minor-i"),
            pytest.param(2, "B", ChordQuality.DIMINISHED, id="minor-ii-dim"),
            pytest.param(3, "C", ChordQuality.MAJOR, id="minor-III"),
            pytest.param(7, "G", ChordQuality.MAJOR, id="minor-VII"),
        ],
    )
    def test_chord_for_degree_natural_minor(self, degree, expected_root, expected_quality):
        a_minor = Scale("A", ScaleType.NATURAL_MINOR)

        chord = a_minor.chord_for_degree(degree)
        assert str(chord.root) == expected_root
        assert chord.quality == expected_quality

    def test_chords_for_degrees_preserves_input_order(self):
        c_major = Scale("C", ScaleType.MAJOR)

        progression = c_major.chords_for_degrees("ii", "V", "I")
        assert isinstance(progression, tuple)
        assert [str(chord.root) for chord in progression] == ["D", "G", "C"]
        assert [chord.quality for chord in progression] == [
            ChordQuality.MINOR,
            ChordQuality.MAJOR,
            ChordQuality.MAJOR,
        ]

    def test_chords_for_degrees_rejects_ambiguous_single_tuple_call(self):
        c_major = Scale("C", ScaleType.MAJOR)

        with pytest.raises(ValueError):
            c_major.chords_for_degrees((1, 4, 5))

    def test_chord_generation_limited_to_heptatonic_scales(self):
        c_pent = Scale("C", ScaleType.PENTATONIC_MAJOR)

        with pytest.raises(ValueError):
            c_pent.chord_for_degree(1)

        with pytest.raises(ValueError):
            c_pent.chords_for_degrees(1, 4, 5)

    @pytest.mark.parametrize("degree", ["I", "V"])
    def test_uppercase_roman_function_conflict_raises(self, degree):
        a_minor = Scale("A", ScaleType.NATURAL_MINOR)

        with pytest.raises(ValueError):
            a_minor.chord_for_degree(degree)

    def test_post_construction_refinement_with_extension(self):
        c_major = Scale("C", ScaleType.MAJOR)

        dominant_seventh = c_major.chord_for_degree("V").with_extension("7")
        assert str(dominant_seventh.root) == "G"
        assert str(dominant_seventh.extension) == "7"


class TestCustomScale:
    """Test custom scale functionality."""
    
    def test_create_custom_scale(self):
        """Test creating a custom scale with custom pattern."""
        custom_pattern = (0, 1, 4, 6, 7, 10)  # Custom intervals
        c_custom = CustomScale("C", custom_pattern)
        
        assert str(c_custom.root) == "C"
        assert c_custom.pattern == custom_pattern
        assert c_custom.scale_type is None
    
    def test_custom_scale_notes(self):
        """Test note generation for custom scales."""
        # Create a scale with specific intervals
        custom_pattern = [0, 2, 5, 7, 10]  # Similar to pentatonic but different
        c_custom = CustomScale("C", custom_pattern)
        
        notes = c_custom.notes
        assert len(notes) == 5
        
        # Check specific pitches
        pitch_classes = [note.pitch_class for note in notes]
        expected_pitch_classes = [0, 2, 5, 7, 10]  # C, D, F, G, Bb
        assert pitch_classes == expected_pitch_classes
    
    def test_custom_scale_equality(self):
        """Test equality comparison for custom scales."""
        pattern1 = [0, 2, 4, 7, 9]
        pattern2 = [0, 2, 4, 7, 9]
        pattern3 = [0, 3, 5, 7, 10]
        
        scale1 = CustomScale("C", pattern1)
        scale2 = CustomScale("C", pattern2)
        scale3 = CustomScale("C", pattern3)
        scale4 = CustomScale("D", pattern1)
        
        assert scale1 == scale2  # Same root and pattern
        assert scale1 != scale3  # Different pattern
        assert scale1 != scale4  # Different root


class TestScaleFactoryFunctions:
    """Test convenience factory functions."""
    
    def test_major_scale_factory(self):
        """Test major_scale factory function."""
        c_major = major_scale("C")
        assert isinstance(c_major, Scale)
        assert c_major.scale_type == ScaleType.MAJOR
        assert str(c_major.root) == "C"
    
    def test_minor_scale_factory(self):
        """Test minor_scale factory function."""
        a_minor = minor_scale("A")
        assert isinstance(a_minor, Scale)
        assert a_minor.scale_type == ScaleType.NATURAL_MINOR
        assert str(a_minor.root) == "A"
    
    def test_harmonic_minor_factory(self):
        """Test harmonic_minor_scale factory function."""
        a_harm = harmonic_minor_scale("A")
        assert isinstance(a_harm, Scale)
        assert a_harm.scale_type == ScaleType.HARMONIC_MINOR
        assert str(a_harm.root) == "A"
    
    def test_modal_scale_factories(self):
        """Test modal scale factory functions."""
        d_dorian = dorian_scale("D")
        assert d_dorian.scale_type == ScaleType.DORIAN
        
        g_mixolydian = mixolydian_scale("G")
        assert g_mixolydian.scale_type == ScaleType.MIXOLYDIAN
    
    def test_pentatonic_factories(self):
        """Test pentatonic scale factory functions."""
        c_pent_maj = pentatonic_major_scale("C")
        assert c_pent_maj.scale_type == ScaleType.PENTATONIC_MAJOR
        
        a_pent_min = pentatonic_minor_scale("A")
        assert a_pent_min.scale_type == ScaleType.PENTATONIC_MINOR
    
    def test_blues_factory(self):
        """Test blues scale factory function."""
        c_blues = blues_scale("C")
        assert c_blues.scale_type == ScaleType.BLUES
        assert str(c_blues.root) == "C"


class TestScaleEquality:
    """Test scale equality and hashing."""
    
    def test_scale_equality(self):
        """Test scale equality comparison."""
        c_major1 = Scale("C", ScaleType.MAJOR)
        c_major2 = Scale("C", ScaleType.MAJOR)
        g_major = Scale("G", ScaleType.MAJOR)
        c_minor = Scale("C", ScaleType.NATURAL_MINOR)
        
        assert c_major1 == c_major2
        assert c_major1 != g_major
        assert c_major1 != c_minor
    
    def test_scale_hashing(self):
        """Test that scales can be used in sets and dicts."""
        scales = {
            Scale("C", ScaleType.MAJOR),
            Scale("G", ScaleType.MAJOR),
            Scale("C", ScaleType.MAJOR),  # Duplicate
        }
        
        assert len(scales) == 2  # Duplicate should be removed


class TestScaleStringRepresentation:
    """Test string representations of scales."""
    
    def test_scale_name(self):
        """Test scale name generation."""
        c_major = Scale("C", ScaleType.MAJOR)
        assert c_major.name == "C Major"
        
        a_minor = Scale("A", ScaleType.NATURAL_MINOR)
        assert a_minor.name == "A Natural Minor"
        
        d_dorian = Scale("D", ScaleType.DORIAN)
        assert d_dorian.name == "D Dorian"
        
        c_pent = Scale("C", ScaleType.PENTATONIC_MAJOR)
        assert c_pent.name == "C Major Pentatonic"
    
    def test_str_representation(self):
        """Test __str__ method."""
        c_major = Scale("C", ScaleType.MAJOR)
        assert str(c_major) == "C Major"
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        c_major = Scale("C", ScaleType.MAJOR)
        repr_str = repr(c_major)
        
        assert "Scale" in repr_str
        assert "C" in repr_str
        assert "major" in repr_str
        assert "Notes:" in repr_str
    
    def test_custom_scale_name(self):
        """Test custom scale name generation."""
        custom_pattern = [0, 2, 4, 7, 9]
        c_custom = CustomScale("C", custom_pattern)
        
        expected_name = "C Custom Scale (0-2-4-7-9)"
        assert c_custom.name == expected_name


class TestScaleEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_enharmonic_root_spelling(self):
        """Test scales with enharmonic root spellings."""
        # These should produce the same pitch classes but different note names
        c_sharp_major = Scale("C#", ScaleType.MAJOR)
        d_flat_major = Scale("Db", ScaleType.MAJOR)
        
        # Pitch classes should be the same
        cs_pitch_classes = [note.pitch_class for note in c_sharp_major.notes]
        db_pitch_classes = [note.pitch_class for note in d_flat_major.notes]
        
        assert cs_pitch_classes == db_pitch_classes
        
        # But note names should be different
        cs_note_names = [str(note) for note in c_sharp_major.notes]
        db_note_names = [str(note) for note in d_flat_major.notes]
        
        assert cs_note_names != db_note_names
    
    def test_extreme_accidentals(self):
        """Test scales that might require extreme accidentals."""
        # These might push the limits of double sharps/flats
        gb_major = Scale("Gb", ScaleType.MAJOR)
        fs_major = Scale("F#", ScaleType.MAJOR)
        
        # Should still produce valid notes (though possibly with double accidentals)
        gb_notes = gb_major.notes
        fs_notes = fs_major.notes
        
        assert len(gb_notes) == 7
        assert len(fs_notes) == 7
        
        # All notes should be valid Note objects
        for note in gb_notes + fs_notes:
            assert isinstance(note, Note)
    
    def test_lazy_initialization(self):
        """Test that notes are calculated lazily with cached_property."""
        c_major = Scale("C", ScaleType.MAJOR)
        
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
