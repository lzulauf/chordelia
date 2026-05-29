"""
Test suite for the notes module.

Tests all note functionality including creation, enharmonic equivalents,
transposition, MIDI conversion, and interval calculations.
"""

import pytest
from chordelia.notes import Note, NoteName, Accidental
from chordelia.notes import (
    C, C_SHARP, D_FLAT, D, D_SHARP, E_FLAT, E, F, F_SHARP, G_FLAT,
    G, G_SHARP, A_FLAT, A, A_SHARP, B_FLAT, B
)
from chordelia.intervals import Interval, IntervalQuality
from chordelia.rhythm import Duration
from chordelia.score import ScoreEventContext


class TestNoteName:
    """Test NoteName enum."""
    
    def test_note_name_values(self):
        """Test that note names have correct semitone values."""
        assert NoteName.C.semitones_from_c == 0
        assert NoteName.D.semitones_from_c == 2
        assert NoteName.E.semitones_from_c == 4
        assert NoteName.F.semitones_from_c == 5
        assert NoteName.G.semitones_from_c == 7
        assert NoteName.A.semitones_from_c == 9
        assert NoteName.B.semitones_from_c == 11


class TestAccidental:
    """Test accidental enum behavior exposed in notes."""
    
    def test_accidental_values(self):
        """Test that accidentals have correct semitone values."""
        assert Accidental.DOUBLE_FLAT.value == -2
        assert Accidental.FLAT.value == -1
        assert Accidental.NATURAL.value == 0
        assert Accidental.SHARP.value == 1
        assert Accidental.DOUBLE_SHARP.value == 2
    
    def test_accidental_string_representation(self):
        """Test string representation of accidentals."""
        assert str(Accidental.DOUBLE_FLAT) == "bb"
        assert str(Accidental.FLAT) == "b"
        assert str(Accidental.NATURAL) == ""
        assert str(Accidental.SHARP) == "#"
        assert str(Accidental.DOUBLE_SHARP) == "##"


class TestNoteCreation:
    """Test note creation and initialization."""

    @pytest.mark.parametrize(
        "alias",
        [
            pytest.param("", id="empty"),
            pytest.param("n", id="n"),
            pytest.param("N", id="upper-n"),
            pytest.param("natural", id="natural-lower"),
            pytest.param("NATURAL", id="natural-upper"),
        ],
    )
    def test_create_with_natural_alias_strings(self, alias):
        """Test constructor coercion for natural accidental aliases."""
        note = Note(NoteName.C, alias)
        assert note.accidental is Accidental.NATURAL
    
    def test_create_natural_notes(self):
        """Test creation of natural notes."""
        c = Note(NoteName.C)
        assert c.name == NoteName.C
        assert c.accidental == Accidental.NATURAL
        assert c.octave is None
        
        g = Note(NoteName.G)
        assert g.name == NoteName.G
        assert g.accidental == Accidental.NATURAL
    
    def test_create_notes_with_accidentals(self):
        """Test creation of notes with accidentals."""
        c_sharp = Note(NoteName.C, Accidental.SHARP)
        assert c_sharp.name == NoteName.C
        assert c_sharp.accidental == Accidental.SHARP
        
        b_flat = Note(NoteName.B, Accidental.FLAT)
        assert b_flat.name == NoteName.B
        assert b_flat.accidental == Accidental.FLAT
        
        f_double_sharp = Note(NoteName.F, Accidental.DOUBLE_SHARP)
        assert f_double_sharp.name == NoteName.F
        assert f_double_sharp.accidental == Accidental.DOUBLE_SHARP
    
    def test_create_notes_with_octave(self):
        """Test creation of notes with octave information."""
        middle_c = Note(NoteName.C, Accidental.NATURAL, 4)
        assert middle_c.name == NoteName.C
        assert middle_c.accidental == Accidental.NATURAL
        assert middle_c.octave == 4
        
        a440 = Note(NoteName.A, Accidental.NATURAL, 4)
        assert a440.octave == 4
    
    def test_create_from_string_input(self):
        """Test creating notes with string inputs."""
        c = Note("C")
        assert c.name == NoteName.C
        assert c.accidental == Accidental.NATURAL
        
        f_sharp = Note("F", "#")
        assert f_sharp.name == NoteName.F
        assert f_sharp.accidental == Accidental.SHARP
        
        d_flat = Note("D", "b")
        assert d_flat.name == NoteName.D
        assert d_flat.accidental == Accidental.FLAT
        
        g_double_flat = Note("G", "bb")
        assert g_double_flat.name == NoteName.G
        assert g_double_flat.accidental == Accidental.DOUBLE_FLAT
    
    def test_create_from_integer_accidental(self):
        """Test creating notes with integer accidental values."""
        c_sharp = Note(NoteName.C, 1)
        assert c_sharp.accidental == Accidental.SHARP
        
        e_flat = Note(NoteName.E, -1)
        assert e_flat.accidental == Accidental.FLAT

    @pytest.mark.parametrize("accidental", ["x", "#b", "bbb", "###", object()])
    def test_create_with_invalid_accidental_raises(self, accidental):
        """Test invalid accidental values are rejected through canonical coercion."""
        with pytest.raises(ValueError):
            Note(NoteName.C, accidental)


class TestNoteFromString:
    """Test note creation from string representation."""
    
    def test_simple_notes(self):
        """Test parsing simple note names."""
        c = Note.from_string("C")
        assert c.name == NoteName.C
        assert c.accidental == Accidental.NATURAL
        assert c.octave is None
        
        g = Note.from_string("G")
        assert g.name == NoteName.G
        assert g.accidental == Accidental.NATURAL
    
    def test_sharp_notes(self):
        """Test parsing sharp notes."""
        c_sharp = Note.from_string("C#")
        assert c_sharp.name == NoteName.C
        assert c_sharp.accidental == Accidental.SHARP
        
        f_double_sharp = Note.from_string("F##")
        assert f_double_sharp.name == NoteName.F
        assert f_double_sharp.accidental == Accidental.DOUBLE_SHARP
    
    def test_flat_notes(self):
        """Test parsing flat notes."""
        b_flat = Note.from_string("Bb")
        assert b_flat.name == NoteName.B
        assert b_flat.accidental == Accidental.FLAT
        
        g_double_flat = Note.from_string("Gbb")
        assert g_double_flat.name == NoteName.G
        assert g_double_flat.accidental == Accidental.DOUBLE_FLAT
    
    def test_notes_with_octave(self):
        """Test parsing notes with octave numbers."""
        c4 = Note.from_string("C4")
        assert c4.name == NoteName.C
        assert c4.accidental == Accidental.NATURAL
        assert c4.octave == 4
        
        f_sharp_5 = Note.from_string("F#5")
        assert f_sharp_5.name == NoteName.F
        assert f_sharp_5.accidental == Accidental.SHARP
        assert f_sharp_5.octave == 5
        
        b_flat_2 = Note.from_string("Bb2")
        assert b_flat_2.name == NoteName.B
        assert b_flat_2.accidental == Accidental.FLAT
        assert b_flat_2.octave == 2
    
    def test_invalid_note_strings(self):
        """Test that invalid note strings raise errors."""
        with pytest.raises(ValueError):
            Note.from_string("H")  # Invalid note name
        
        with pytest.raises(ValueError):
            Note.from_string("C###")  # Too many sharps
        
        with pytest.raises(ValueError):
            Note.from_string("Cbbb")  # Too many flats
        
        with pytest.raises(ValueError):
            Note.from_string("C4#")  # Octave before accidental


class TestNotePitchClass:
    """Test pitch class calculation."""
    
    def test_natural_note_pitch_classes(self):
        """Test pitch classes for natural notes."""
        assert Note(NoteName.C).pitch_class == 0
        assert Note(NoteName.D).pitch_class == 2
        assert Note(NoteName.E).pitch_class == 4
        assert Note(NoteName.F).pitch_class == 5
        assert Note(NoteName.G).pitch_class == 7
        assert Note(NoteName.A).pitch_class == 9
        assert Note(NoteName.B).pitch_class == 11
    
    def test_sharp_note_pitch_classes(self):
        """Test pitch classes for sharp notes."""
        assert Note(NoteName.C, Accidental.SHARP).pitch_class == 1
        assert Note(NoteName.D, Accidental.SHARP).pitch_class == 3
        assert Note(NoteName.F, Accidental.SHARP).pitch_class == 6
        assert Note(NoteName.G, Accidental.SHARP).pitch_class == 8
        assert Note(NoteName.A, Accidental.SHARP).pitch_class == 10
    
    def test_flat_note_pitch_classes(self):
        """Test pitch classes for flat notes."""
        assert Note(NoteName.D, Accidental.FLAT).pitch_class == 1
        assert Note(NoteName.E, Accidental.FLAT).pitch_class == 3
        assert Note(NoteName.G, Accidental.FLAT).pitch_class == 6
        assert Note(NoteName.A, Accidental.FLAT).pitch_class == 8
        assert Note(NoteName.B, Accidental.FLAT).pitch_class == 10
    
    def test_double_accidental_pitch_classes(self):
        """Test pitch classes for double accidentals."""
        assert Note(NoteName.C, Accidental.DOUBLE_SHARP).pitch_class == 2
        assert Note(NoteName.D, Accidental.DOUBLE_FLAT).pitch_class == 0
        assert Note(NoteName.F, Accidental.DOUBLE_SHARP).pitch_class == 7
        assert Note(NoteName.B, Accidental.DOUBLE_FLAT).pitch_class == 9
    
    def test_wrap_around_pitch_classes(self):
        """Test that pitch classes wrap around correctly."""
        # B# = C
        b_sharp = Note(NoteName.B, Accidental.SHARP)
        assert b_sharp.pitch_class == 0
        
        # Cb = B
        c_flat = Note(NoteName.C, Accidental.FLAT)
        assert c_flat.pitch_class == 11


class TestNoteMIDI:
    """Test MIDI number conversion."""
    
    def test_midi_numbers_without_octave(self):
        """Test that notes without octave return None for MIDI number."""
        c = Note(NoteName.C)
        assert c.midi_number is None
        
        f_sharp = Note(NoteName.F, Accidental.SHARP)
        assert f_sharp.midi_number is None
    
    def test_middle_c_midi(self):
        """Test that middle C (C4) has MIDI number 60."""
        middle_c = Note(NoteName.C, Accidental.NATURAL, 4)
        assert middle_c.midi_number == 60
    
    def test_a440_midi(self):
        """Test that A4 has MIDI number 69."""
        a440 = Note(NoteName.A, Accidental.NATURAL, 4)
        assert a440.midi_number == 69
    
    def test_various_midi_numbers(self):
        """Test MIDI numbers for various notes."""
        # C0 = MIDI 12
        c0 = Note(NoteName.C, Accidental.NATURAL, 0)
        assert c0.midi_number == 12
        
        # C#4 = MIDI 61
        c_sharp_4 = Note(NoteName.C, Accidental.SHARP, 4)
        assert c_sharp_4.midi_number == 61
        
        # Bb4 = MIDI 70
        b_flat_4 = Note(NoteName.B, Accidental.FLAT, 4)
        assert b_flat_4.midi_number == 70
        
        # C8 = MIDI 108
        c8 = Note(NoteName.C, Accidental.NATURAL, 8)
        assert c8.midi_number == 108
    
    def test_from_midi_number_sharps(self):
        """Test creating notes from MIDI numbers with sharp preference."""
        # MIDI 60 = C4
        c4 = Note.from_midi_number(60)
        assert c4.name == NoteName.C
        assert c4.accidental == Accidental.NATURAL
        assert c4.octave == 4
        
        # MIDI 61 = C#4 (with sharp preference)
        c_sharp_4 = Note.from_midi_number(61, prefer_sharps=True)
        assert c_sharp_4.name == NoteName.C
        assert c_sharp_4.accidental == Accidental.SHARP
        assert c_sharp_4.octave == 4
        
        # MIDI 69 = A4
        a4 = Note.from_midi_number(69)
        assert a4.name == NoteName.A
        assert a4.accidental == Accidental.NATURAL
        assert a4.octave == 4
    
    def test_from_midi_number_flats(self):
        """Test creating notes from MIDI numbers with flat preference."""
        # MIDI 61 = Db4 (with flat preference)
        d_flat_4 = Note.from_midi_number(61, prefer_sharps=False)
        assert d_flat_4.name == NoteName.D
        assert d_flat_4.accidental == Accidental.FLAT
        assert d_flat_4.octave == 4
        
        # MIDI 70 = Bb4 (with flat preference)
        b_flat_4 = Note.from_midi_number(70, prefer_sharps=False)
        assert b_flat_4.name == NoteName.B
        assert b_flat_4.accidental == Accidental.FLAT
        assert b_flat_4.octave == 4
    
    def test_midi_boundary_values(self):
        """Test MIDI boundary values."""
        with pytest.raises(ValueError):
            Note.from_midi_number(-1)
        
        with pytest.raises(ValueError):
            Note.from_midi_number(128)
        
        # Valid boundaries
        low_note = Note.from_midi_number(0)
        assert low_note.octave == -1
        
        high_note = Note.from_midi_number(127)
        assert high_note.octave == 9


class TestNoteScoreEvents:
    """Test score event conversion behavior for Note."""

    def test_note_emits_single_score_event(self):
        """Notes emit one event using timing and playback values from context."""
        context = ScoreEventContext(
            start_offset=Duration.from_beats(3, 2),
            default_duration=Duration.from_beats(1, 2),
            velocity=90,
            channel=2,
            voice=1,
        )

        events = Note("C4").score_events_for_context(context)

        assert len(events) == 1
        event = events[0]
        assert event.beat == Duration.from_beats(3, 2)
        assert event.duration == Duration.from_beats(1, 2)
        assert event.pitches == (60,)
        assert event.velocity == 90
        assert event.channel == 2
        assert event.voice == 1
        assert event.spelling == ("C4",)

    def test_note_without_octave_raises_value_error(self):
        """Notes without octave cannot emit MIDI pitch values."""
        with pytest.raises(ValueError, match="requires octave information"):
            Note("C").score_events_for_context(ScoreEventContext())

    def test_note_emits_accidental_midi_pitch_and_spelling(self):
        """Accidental notes should emit the matching MIDI pitch and spelling."""
        context = ScoreEventContext(
            start_offset=Duration.from_beats(1, 4),
            default_duration=Duration.from_beats(3, 8),
            channel=3,
            voice=2,
        )

        event = Note("F#4").score_events_for_context(context)[0]

        assert event.beat == Duration.from_beats(1, 4)
        assert event.duration == Duration.from_beats(3, 8)
        assert event.pitches == (66,)
        assert event.channel == 3
        assert event.voice == 2
        assert event.spelling == ("F#4",)


class TestNoteTransposition:
    """Test note transposition with intervals."""
    
    def test_simple_transposition(self):
        """Test simple interval transpositions."""
        c = Note(NoteName.C)
        major_third = Interval(IntervalQuality.MAJOR, 3)
        
        e = c.transpose(major_third)
        assert e.pitch_class == 4  # E
        
        f = Note(NoteName.F)
        perfect_fifth = Interval(IntervalQuality.PERFECT, 5)
        
        result = f.transpose(perfect_fifth)
        assert result.pitch_class == 0  # C (F + P5 = C)
    
    def test_transposition_with_octave(self):
        """Test transposition preserving octave relationships."""
        c4 = Note(NoteName.C, Accidental.NATURAL, 4)
        octave = Interval(IntervalQuality.PERFECT, 8)
        
        c5 = c4.transpose(octave)
        assert c5.name == NoteName.C
        assert c5.accidental == Accidental.NATURAL
        assert c5.octave == 5
        
        # Test compound interval
        major_ninth = Interval(IntervalQuality.MAJOR, 9)
        d5 = c4.transpose(major_ninth)
        assert d5.pitch_class == 2  # D
        assert d5.octave == 5
    
    def test_descending_transposition(self):
        """Test transposition with descending intervals."""
        c4 = Note(NoteName.C, Accidental.NATURAL, 4)
        
        # Create descending interval by using negative semitones
        desc_fifth = Interval.from_semitones(-7)
        f3 = c4.transpose(desc_fifth)
        
        assert f3.pitch_class == 5  # F
        assert f3.octave == 3


class TestNoteIntervals:
    """Test interval calculation between notes."""
    
    def test_simple_intervals(self):
        """Test calculating simple intervals between notes."""
        c = Note(NoteName.C)
        e = Note(NoteName.E)
        
        interval = c.interval_to(e)
        assert interval.semitones == 4  # Major third
        
        f = Note(NoteName.F)
        c_high = Note(NoteName.C)
        
        # F to C within octave
        interval = f.interval_to(c_high)
        assert interval.semitones in [7, -5]  # Perfect fifth up or fourth down
    
    def test_intervals_with_octave(self):
        """Test intervals between notes with octave information."""
        c4 = Note(NoteName.C, Accidental.NATURAL, 4)
        c5 = Note(NoteName.C, Accidental.NATURAL, 5)
        
        interval = c4.interval_to(c5)
        assert interval.semitones == 12  # Octave
        
        g4 = Note(NoteName.G, Accidental.NATURAL, 4)
        interval = c4.interval_to(g4)
        assert interval.semitones == 7  # Perfect fifth


class TestNoteEnharmonics:
    """Test enharmonic equivalents."""
    
    def test_basic_enharmonics(self):
        """Test basic enharmonic equivalents."""
        c_sharp = Note(NoteName.C, Accidental.SHARP)
        d_flat = Note(NoteName.D, Accidental.FLAT)
        
        assert c_sharp.is_enharmonic_with(d_flat)
        assert d_flat.is_enharmonic_with(c_sharp)
        
        f_sharp = Note(NoteName.F, Accidental.SHARP)
        g_flat = Note(NoteName.G, Accidental.FLAT)
        
        assert f_sharp.is_enharmonic_with(g_flat)
    
    def test_enharmonic_equivalents_list(self):
        """Test getting list of enharmonic equivalents."""
        c_sharp = Note(NoteName.C, Accidental.SHARP)
        equivalents = c_sharp.enharmonic_equivalents()
        
        # Should include Db
        assert any(note.name == NoteName.D and note.accidental == Accidental.FLAT 
                  for note in equivalents)
        
        # Should not include the original note
        assert not any(note.name == NoteName.C and note.accidental == Accidental.SHARP 
                      for note in equivalents)
    
    def test_enharmonics_with_octave(self):
        """Test enharmonic equivalents preserve octave information."""
        c_sharp_4 = Note(NoteName.C, Accidental.SHARP, 4)
        equivalents = c_sharp_4.enharmonic_equivalents()
        
        d_flat_4 = next((note for note in equivalents 
                        if note.name == NoteName.D and note.accidental == Accidental.FLAT), None)
        
        assert d_flat_4 is not None
        assert d_flat_4.octave == 4


class TestNoteFrequency:
    """Test frequency calculation."""
    
    def test_a440_frequency(self):
        """Test that A4 has frequency 440 Hz."""
        a4 = Note(NoteName.A, Accidental.NATURAL, 4)
        assert abs(a4.frequency - 440.0) < 0.001
    
    def test_middle_c_frequency(self):
        """Test middle C frequency."""
        c4 = Note(NoteName.C, Accidental.NATURAL, 4)
        # Middle C should be approximately 261.63 Hz
        assert abs(c4.frequency - 261.63) < 0.1
    
    def test_octave_frequency_relationship(self):
        """Test that octaves have 2:1 frequency relationship."""
        a3 = Note(NoteName.A, Accidental.NATURAL, 3)
        a4 = Note(NoteName.A, Accidental.NATURAL, 4)
        a5 = Note(NoteName.A, Accidental.NATURAL, 5)
        
        assert abs(a4.frequency / a3.frequency - 2.0) < 0.001
        assert abs(a5.frequency / a4.frequency - 2.0) < 0.001
    
    def test_frequency_without_octave(self):
        """Test that notes without octave return None for frequency."""
        a = Note(NoteName.A)
        assert a.frequency is None


class TestNoteComparison:
    """Test note comparison and sorting."""
    
    def test_equality(self):
        """Test note equality."""
        c1 = Note(NoteName.C, Accidental.NATURAL, 4)
        c2 = Note(NoteName.C, Accidental.NATURAL, 4)
        c_sharp = Note(NoteName.C, Accidental.SHARP, 4)
        
        assert c1 == c2
        assert c1 != c_sharp
    
    def test_sorting_with_octave(self):
        """Test sorting notes with octave information."""
        notes = [
            Note(NoteName.C, Accidental.NATURAL, 5),
            Note(NoteName.C, Accidental.NATURAL, 4),
            Note(NoteName.B, Accidental.NATURAL, 4),
            Note(NoteName.D, Accidental.NATURAL, 4),
        ]
        
        sorted_notes = sorted(notes)
        
        # Should be sorted by MIDI number: C4(60), D4(62), B4(71), C5(72)
        assert sorted_notes[0].name == NoteName.C and sorted_notes[0].octave == 4
        assert sorted_notes[1].name == NoteName.D and sorted_notes[1].octave == 4
        assert sorted_notes[2].name == NoteName.B and sorted_notes[2].octave == 4
        assert sorted_notes[3].name == NoteName.C and sorted_notes[3].octave == 5
    
    def test_sorting_without_octave(self):
        """Test sorting notes without octave information."""
        notes = [
            Note(NoteName.G),
            Note(NoteName.C),
            Note(NoteName.A, Accidental.SHARP),
            Note(NoteName.D, Accidental.FLAT),
        ]
        
        sorted_notes = sorted(notes)
        
        # Should be sorted by pitch class: C, Db, G, A#
        expected_pitch_classes = [0, 1, 7, 10]
        actual_pitch_classes = [note.pitch_class for note in sorted_notes]
        
        assert actual_pitch_classes == expected_pitch_classes


class TestNoteStringRepresentation:
    """Test string representations of notes."""
    
    def test_str_representation(self):
        """Test __str__ method."""
        assert str(Note(NoteName.C)) == "C"
        assert str(Note(NoteName.C, Accidental.SHARP)) == "C#"
        assert str(Note(NoteName.B, Accidental.FLAT)) == "Bb"
        assert str(Note(NoteName.F, Accidental.DOUBLE_SHARP)) == "F##"
        assert str(Note(NoteName.G, Accidental.DOUBLE_FLAT)) == "Gbb"
        
        # With octave
        assert str(Note(NoteName.C, Accidental.NATURAL, 4)) == "C4"
        assert str(Note(NoteName.F, Accidental.SHARP, 5)) == "F#5"
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        note = Note(NoteName.C, Accidental.SHARP, 4)
        repr_str = repr(note)
        
        assert "Note" in repr_str
        assert "C" in repr_str
        assert "SHARP" in repr_str
        assert "4" in repr_str


class TestNoteConstants:
    """Test predefined note constants."""
    
    def test_constant_values(self):
        """Test that note constants have correct values."""
        assert C.name == NoteName.C and C.accidental == Accidental.NATURAL
        assert C_SHARP.name == NoteName.C and C_SHARP.accidental == Accidental.SHARP
        assert D_FLAT.name == NoteName.D and D_FLAT.accidental == Accidental.FLAT
        assert D.name == NoteName.D and D.accidental == Accidental.NATURAL
        assert E.name == NoteName.E and E.accidental == Accidental.NATURAL
        assert F.name == NoteName.F and F.accidental == Accidental.NATURAL
        assert G.name == NoteName.G and G.accidental == Accidental.NATURAL
        assert A.name == NoteName.A and A.accidental == Accidental.NATURAL
        assert B.name == NoteName.B and B.accidental == Accidental.NATURAL
    
    def test_enharmonic_constants(self):
        """Test that enharmonic constants are equivalent."""
        assert C_SHARP.is_enharmonic_with(D_FLAT)
        assert D_SHARP.is_enharmonic_with(E_FLAT)
        assert F_SHARP.is_enharmonic_with(G_FLAT)
        assert G_SHARP.is_enharmonic_with(A_FLAT)
        assert A_SHARP.is_enharmonic_with(B_FLAT)


class TestNoteCopyConstructor:
    """Test copy-constructor API methods for immutable Note objects."""
    
    def test_with_octave(self):
        """Test with_octave method."""
        original = Note("C4")
        
        # Test changing octave
        with_octave_5 = original.with_octave(5)
        assert with_octave_5.name == original.name
        assert with_octave_5.accidental == original.accidental
        assert with_octave_5.octave == 5
        assert with_octave_5 != original  # Different objects
        
        # Test removing octave
        without_octave = original.with_octave(None)
        assert without_octave.name == original.name
        assert without_octave.accidental == original.accidental
        assert without_octave.octave is None
        
        # Test that original is unchanged
        assert original.octave == 4
    
    def test_with_accidental(self):
        """Test with_accidental method."""
        original = Note("C4")
        
        # Test with enum
        with_sharp = original.with_accidental(Accidental.SHARP)
        assert with_sharp.name == original.name
        assert with_sharp.accidental == Accidental.SHARP
        assert with_sharp.octave == original.octave
        assert with_sharp != original
        
        # Test with string
        with_flat = original.with_accidental("b")
        assert with_flat.accidental == Accidental.FLAT
        
        # Test with int
        with_double_sharp = original.with_accidental(2)
        assert with_double_sharp.accidental == Accidental.DOUBLE_SHARP
        
        # Test that original is unchanged
        assert original.accidental == Accidental.NATURAL
    
    def test_with_name(self):
        """Test with_name method."""
        original = Note("C#4")
        
        # Test with enum
        with_d = original.with_name(NoteName.D)
        assert with_d.name == NoteName.D
        assert with_d.accidental == original.accidental
        assert with_d.octave == original.octave
        assert with_d != original
        
        # Test with string
        with_f = original.with_name("F")
        assert with_f.name == NoteName.F
        
        # Test that original is unchanged
        assert original.name == NoteName.C
    
    def test_with_combined(self):
        """Test the combined with_ method."""
        original = Note("C4")
        
        # Test single parameter changes
        with_octave = original.with_(octave=5)
        assert with_octave == Note("C5")
        
        with_accidental = original.with_(accidental=Accidental.SHARP)
        assert with_accidental == Note("C#4")
        
        with_name = original.with_(name=NoteName.D)
        assert with_name == Note("D4")
        
        # Test multiple parameter changes
        multi_change = original.with_(
            name=NoteName.F,
            accidental=Accidental.SHARP,
            octave=6
        )
        assert multi_change == Note("F#6")
        
        # Test explicit None for octave removal
        without_octave = original.with_(octave=None)
        assert without_octave.octave is None
        assert without_octave == Note("C")
        
        # Test no parameters (should create equivalent but different object)
        copy_note = original.with_()
        assert copy_note == original
        assert copy_note is not original
    
    def test_copy_constructor_immutability(self):
        """Test that copy-constructor methods preserve immutability."""
        original = Note("C#4")
        
        # Apply various transformations
        transformed = original.with_octave(5).with_name(NoteName.F).with_accidental(Accidental.FLAT)
        
        # Original should be completely unchanged
        assert original.name == NoteName.C
        assert original.accidental == Accidental.SHARP
        assert original.octave == 4
        
        # Transformed should have all changes
        assert transformed.name == NoteName.F
        assert transformed.accidental == Accidental.FLAT
        assert transformed.octave == 5
    
    def test_copy_constructor_chaining(self):
        """Test fluent chaining of copy-constructor methods."""
        result = (Note("C")
                  .with_octave(4)
                  .with_accidental(Accidental.SHARP)
                  .with_name(NoteName.F))
        
        expected = Note("F#4")
        assert result == expected
    
    def test_copy_constructor_with_complex_notes(self):
        """Test copy-constructor with double accidentals and edge cases."""
        # Test with double accidentals
        original = Note(NoteName.C, Accidental.DOUBLE_SHARP, 3)
        
        result = original.with_(name=NoteName.B, accidental=Accidental.DOUBLE_FLAT, octave=7)
        assert result.name == NoteName.B
        assert result.accidental == Accidental.DOUBLE_FLAT
        assert result.octave == 7
        
        # Test removing octave from note without octave
        no_octave = Note("F#")
        still_no_octave = no_octave.with_octave(None)
        assert still_no_octave.octave is None
        assert still_no_octave == no_octave
    
    def test_copy_constructor_equality_and_hashing(self):
        """Test that copy-constructed notes work properly with equality and hashing."""
        original = Note("C4")
        copy1 = original.with_()
        copy2 = original.with_(octave=4)  # Same values
        different = original.with_(octave=5)
        
        # Test equality
        assert copy1 == original
        assert copy2 == original
        assert different != original
        
        # Test hashing (important for sets/dicts)
        note_set = {original, copy1, copy2, different}
        assert len(note_set) == 2  # original/copy1/copy2 are same, different is separate
        
        # Test as dict keys
        note_dict = {original: "original", different: "different"}
        assert note_dict[copy1] == "original"  # copy1 should map to same value as original
    
    def test_copy_constructor_string_inputs(self):
        """Test copy-constructor methods with string inputs."""
        original = Note("C4")
        
        # Test string accidental input
        with_sharp_str = original.with_accidental("#")
        with_sharp_enum = original.with_accidental(Accidental.SHARP)
        assert with_sharp_str == with_sharp_enum
        
        # Test string name input
        with_d_str = original.with_name("D")
        with_d_enum = original.with_name(NoteName.D)
        assert with_d_str == with_d_enum
    
    def test_copy_constructor_performance(self):
        """Test that copy-constructor methods are reasonably performant."""
        import time
        
        original = Note("C4")
        iterations = 10000
        
        # Time the with_octave method
        start = time.perf_counter()
        for _ in range(iterations):
            _ = original.with_octave(5)
        elapsed = time.perf_counter() - start
        
        # Should be very fast (less than 10 microseconds per call)
        per_call_microseconds = (elapsed / iterations) * 1_000_000
        assert per_call_microseconds < 10, f"Copy-constructor too slow: {per_call_microseconds:.2f}μs per call"
