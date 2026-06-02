"""
Test suite for the chords module.

Tests all chord functionality including construction, parsing,
extensions, inversions, and enharmonic spelling.
"""

import pytest
from chordelia import notes
from chordelia import intervals
from chordelia.degrees import Degree
from chordelia.chords import Chord, ChordQuality, ChordExtension
from chordelia.chords import (
    major_chord, minor_chord, diminished_chord, augmented_chord,
    dominant_seventh_chord, major_seventh_chord, minor_seventh_chord,
    sus2_chord, sus4_chord
)
from chordelia.notes import Note, NoteName, Accidental
from chordelia.intervals import Interval, IntervalQuality
from chordelia.rhythm import Duration
from chordelia.score import ScoreEventContext


class TestChordQuality:
    """Test ChordQuality enum."""

    @pytest.mark.parametrize("abbreviation, expected_quality", [
        ("major", ChordQuality.MAJOR),
        ("maj", ChordQuality.MAJOR),
        ("M", ChordQuality.MAJOR),
        ("minor", ChordQuality.MINOR),
        ("min", ChordQuality.MINOR),
        ("m", ChordQuality.MINOR),
        ("-", ChordQuality.MINOR),
        ("diminished", ChordQuality.DIMINISHED),
        ("dim", ChordQuality.DIMINISHED),
        ("°", ChordQuality.DIMINISHED),
        ("augmented", ChordQuality.AUGMENTED),
        ("aug", ChordQuality.AUGMENTED),
        ("+", ChordQuality.AUGMENTED),
        ("sus2", ChordQuality.SUSPENDED_2),
        ("sus4", ChordQuality.SUSPENDED_4),
        ("sus", ChordQuality.SUSPENDED_4),
        ("power", ChordQuality.POWER),
        ("5", ChordQuality.POWER),
    ])
    def test_from_string(self, abbreviation, expected_quality):
        """All abbreviations for a quality should map back to that quality in _QUALITY_HASH."""
        assert ChordQuality.from_string(abbreviation) == expected_quality

    @pytest.mark.parametrize("quality, expected_intervals", [
        (ChordQuality.MAJOR, (0, 4, 7)),
        (ChordQuality.MINOR, (0, 3, 7)),
        (ChordQuality.DIMINISHED, (0, 3, 6)),
        (ChordQuality.AUGMENTED, (0, 4, 8)),
        (ChordQuality.SUSPENDED_2, (0, 2, 7)),
        (ChordQuality.SUSPENDED_4, (0, 5, 7)),
        (ChordQuality.POWER, (0, 7,)),
    ])
    def test_semitone_intervals(self, quality, expected_intervals):
        """The semitone intervals in the enum should match _CHORD_INTERVALS."""
        assert quality.semitone_intervals == expected_intervals

    @pytest.mark.parametrize("quality, expected_str", [
        (ChordQuality.MAJOR, "major"),
        (ChordQuality.MINOR, "minor"),
        (ChordQuality.DIMINISHED, "diminished"),
        (ChordQuality.AUGMENTED, "augmented"),
        (ChordQuality.SUSPENDED_2, "sus2"),
        (ChordQuality.SUSPENDED_4, "sus4"),
        (ChordQuality.POWER, "power"),
    ])
    def test_str(self, quality, expected_str):
        """Test string representation of ChordQuality."""
        assert str(quality) == expected_str

    def test_repr(self):
        """Test repr representation of ChordQuality."""
        quality = ChordQuality.MAJOR
        assert repr(quality) == "<ChordQuality(major)>"


class TestChordExtension:
    """Test ChordExtension enum."""
    
    def test_chord_extension_values(self):
        """Test that chord extensions have correct values."""
        assert str(ChordExtension.SEVENTH) == "7"
        assert str(ChordExtension.MAJOR_SEVENTH) == "maj7"
        assert str(ChordExtension.NINTH) == "9"
        assert str(ChordExtension.MAJOR_NINTH) == "maj9"
        assert str(ChordExtension.ELEVENTH) == "11"
        assert str(ChordExtension.THIRTEENTH) == "13"

    
    def test_chord_extension_from_string(self):
        """Test creating ChordExtension from string."""
        assert ChordExtension.from_string("7") == ChordExtension.SEVENTH
        assert ChordExtension.from_string("maj7") == ChordExtension.MAJOR_SEVENTH
        assert ChordExtension.from_string("9") == ChordExtension.NINTH
        assert ChordExtension.from_string("maj9") == ChordExtension.MAJOR_NINTH
        assert ChordExtension.from_string("11") == ChordExtension.ELEVENTH
        assert ChordExtension.from_string("13") == ChordExtension.THIRTEENTH

    @pytest.mark.parametrize("input,expected", [
        ("7", ChordExtension.SEVENTH),
        ("maj7", ChordExtension.MAJOR_SEVENTH),
        ("9", ChordExtension.NINTH),
        ("maj9", ChordExtension.MAJOR_NINTH),
        ("11", ChordExtension.ELEVENTH),
        ("13", ChordExtension.THIRTEENTH),
        ("6", ChordExtension.SIXTH),
        ("foo", None),
        ("", None),
        (None, None),
        (ChordExtension.ELEVENTH, ChordExtension.ELEVENTH),
    ])
    def test_chord_extension_from_unknown(self, input, expected):
        """Test that from_unknown handles acceptable types correctly."""
        if expected is None:
            with pytest.raises(ValueError):
                ChordExtension.from_unknown(input)
        else:
            assert ChordExtension.from_unknown(input) == expected

class TestChordCreation:
    """Test chord creation and initialization."""
    
    def test_create_major_chord(self):
        """Test creation of major chords."""
        c_major = Chord(Note(NoteName.C), ChordQuality.MAJOR)
        assert c_major.root.name == NoteName.C
        assert c_major.quality == ChordQuality.MAJOR
        assert c_major.extension is None
        assert c_major.additions == ()
        assert c_major.omissions == ()
        assert c_major.bass_note is None
        assert c_major.inversion == 0
    
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
    
    def test_create_with_extension(self):
        """Test creating chords with extensions."""
        c7 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)
        assert c7.extension == ChordExtension.SEVENTH
        
        cmaj7 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH)
        assert cmaj7.extension == ChordExtension.MAJOR_SEVENTH
    
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

    def test_c5_is_major_chord_rooted_at_octave_5(self):
        """C5 should parse as a C major chord with root octave 5."""
        chord = Chord.from_string("C5")
        assert chord.root == Note("C5")
        assert chord.quality == ChordQuality.MAJOR

    def test_c7_is_major_chord_rooted_at_octave_7(self):
        """C7 should parse as a C major chord with root octave 7."""
        chord = Chord.from_string("C7")
        assert chord.root == Note("C7")
        assert chord.quality == ChordQuality.MAJOR
        assert chord.extension is None

    def test_parenthesized_5_is_power_chord(self):
        """C(5) should parse as an explicit C power chord."""
        chord = Chord.from_string("C(5)")
        assert chord.root == Note("C")
        assert chord.quality == ChordQuality.POWER
    
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
    
    @pytest.mark.parametrize("chord_str, root, quality, extension, additions, bass_note", [
        ("C", notes.C, ChordQuality.MAJOR, None, None, None),
        ("CM", notes.C, ChordQuality.MAJOR, None, None, None),
        ("Cm", notes.C, ChordQuality.MINOR, None, None, None),
        ("Cmin", notes.C, ChordQuality.MINOR, None, None, None),
        ("Cminor", notes.C, ChordQuality.MINOR, None, None, None),
        ("C#", notes.C_SHARP, ChordQuality.MAJOR, None, None, None),
        ("CbM", notes.C_FLAT, ChordQuality.MAJOR, None, None, None),
        ("D#m", notes.D_SHARP, ChordQuality.MINOR, None, None, None),
        ("Bmin", notes.B, ChordQuality.MINOR, None, None, None),
        ("Bbminor", notes.B_FLAT, ChordQuality.MINOR, None, None, None),
    ])
    def test_basic_chord_parsing(self, chord_str, root, quality, extension, additions, bass_note):
        expected_chord = Chord(
            root,
            quality,
            extension=extension,
            additions=additions,
            bass_note=bass_note
        )
        assert Chord.from_string(chord_str) == expected_chord

    @pytest.mark.parametrize("chord_str, root, quality, extension", [
        ("C(7)", notes.C, ChordQuality.MAJOR, ChordExtension.SEVENTH),
        ("Cmaj7", notes.C, ChordQuality.MAJOR, ChordExtension.MAJOR_SEVENTH),
        ("C(maj7)", notes.C, ChordQuality.MAJOR, ChordExtension.MAJOR_SEVENTH),
        ("Cm7", notes.C, ChordQuality.MINOR, ChordExtension.SEVENTH),
        ("C-7", notes.C, ChordQuality.MINOR, ChordExtension.SEVENTH),
        ("Cmin7", notes.C, ChordQuality.MINOR, ChordExtension.SEVENTH),
        ("Cmin(7)", notes.C, ChordQuality.MINOR, ChordExtension.SEVENTH),
        ("Cmin(maj7)", notes.C, ChordQuality.MINOR, ChordExtension.MAJOR_SEVENTH),
        ("C(6)", notes.C, ChordQuality.MAJOR, ChordExtension.SIXTH),
        ("C(9)", notes.C, ChordQuality.MAJOR, ChordExtension.NINTH),
        ("Cmaj9", notes.C, ChordQuality.MAJOR, ChordExtension.MAJOR_NINTH),
        ("C(11)", notes.C, ChordQuality.MAJOR, ChordExtension.ELEVENTH),
        ("Cmaj11", notes.C, ChordQuality.MAJOR, ChordExtension.MAJOR_ELEVENTH),
        ("Cm(maj11)", notes.C, ChordQuality.MINOR, ChordExtension.MAJOR_ELEVENTH),
        ("C(13)", notes.C, ChordQuality.MAJOR, ChordExtension.THIRTEENTH),
        ("Cmaj13", notes.C, ChordQuality.MAJOR, ChordExtension.MAJOR_THIRTEENTH),
    ])
    def test_extension_chord_parsing(self, chord_str, root, quality, extension):
        expected_chord = Chord(root, quality, extension=extension)
        assert Chord.from_string(chord_str) == expected_chord

    @pytest.mark.parametrize("chord_str, expected_chord", [
        ("Csus2", Chord(notes.C, ChordQuality.SUSPENDED_2)),
        ("Csus4", Chord(notes.C, ChordQuality.SUSPENDED_4)),
        ("Csus",  Chord(notes.C, ChordQuality.SUSPENDED_4)),
        ("Asus2", Chord(notes.A, ChordQuality.SUSPENDED_2)),
        ("Asus4", Chord(notes.A, ChordQuality.SUSPENDED_4)),
        ("Asus",  Chord(notes.A, ChordQuality.SUSPENDED_4)),
    ])
    def test_suspended_chord_parsing(self, chord_str, expected_chord):
        assert Chord.from_string(chord_str) == expected_chord

    @pytest.mark.parametrize("chord_str, expected_chord", [
        ("Dbadd9", Chord(notes.D_FLAT, ChordQuality.MAJOR, additions=[Interval(IntervalQuality.MAJOR, 9)])),
        ("Db(add9)", Chord(notes.D_FLAT, ChordQuality.MAJOR, additions=[Interval(IntervalQuality.MAJOR, 9)])),
        ("Cadd2", Chord(notes.C, ChordQuality.MAJOR, additions=[intervals.MAJOR_SECOND])),
        ("C(add2)", Chord(notes.C, ChordQuality.MAJOR, additions=[intervals.MAJOR_SECOND])),
    ])
    def test_addition_chord_parsing(self, chord_str, expected_chord):
        assert Chord.from_string(chord_str) == expected_chord

    @pytest.mark.parametrize("chord_str, expected_chord", [
        ("C/E", Chord(notes.C, ChordQuality.MAJOR, bass_note=notes.E)),
        ("Am/C", Chord(notes.A, ChordQuality.MINOR, bass_note=notes.C)),
    ])
    def test_slash_chord_parsing(self, chord_str, expected_chord):
        assert Chord.from_string(chord_str) == expected_chord

    @pytest.mark.parametrize("chord_str, expected_chord_kwargs", [
        ("C(7)(11)", {"root": notes.C, "quality": ChordQuality.MAJOR, "extension": ChordExtension.SEVENTH, "additions": ["P11"], "bass_note": None}),
        ("C(7)(add11)", {"root": notes.C, "quality": ChordQuality.MAJOR, "extension": ChordExtension.SEVENTH, "additions": ["P11"], "bass_note": None}),
        ("C(7)add11", {"root": notes.C, "quality": ChordQuality.MAJOR, "extension": ChordExtension.SEVENTH, "additions": ["P11"], "bass_note": None}),
        ("C(7)(11)(13)", {"root": notes.C, "quality": ChordQuality.MAJOR, "extension": ChordExtension.SEVENTH, "additions": ["P11", "13"], "bass_note": None}),
        ("B(7)(9)", {"root": notes.B, "quality": ChordQuality.MAJOR, "extension": ChordExtension.SEVENTH, "additions": [Interval(IntervalQuality.MAJOR, 9)]}),
        ("F#maj7(#11)", {"root": notes.F_SHARP, "quality": ChordQuality.MAJOR, "extension": ChordExtension.MAJOR_SEVENTH, "additions": [Interval(IntervalQuality.AUGMENTED, 11)]}),
        ("Cmaj7(add9)", {"root": notes.C, "quality": ChordQuality.MAJOR, "extension": ChordExtension.MAJOR_SEVENTH, "additions": [Interval(IntervalQuality.MAJOR, 9)]}),
        ("Cmaj7add9/E", {"root": notes.C, "quality": ChordQuality.MAJOR, "extension": ChordExtension.MAJOR_SEVENTH, "additions": [Interval(IntervalQuality.MAJOR, 9)], "bass_note": notes.E}),
        ("F##", {"root": Note(NoteName.F, accidental=Accidental.DOUBLE_SHARP), "quality": ChordQuality.MAJOR}),
        ("Bb(13)", {"root": Note(NoteName.B, accidental=Accidental.FLAT), "quality": ChordQuality.MAJOR, "extension": ChordExtension.THIRTEENTH}),
    ])
    def test_advanced_chord_parsing(self, chord_str, expected_chord_kwargs):
        assert Chord.from_string(chord_str) == Chord(**expected_chord_kwargs)


class TestChordNotes:
    """Test chord note generation."""
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C", ChordQuality.MAJOR, None, None, [0, 4, 7]),
    ])
    def test_major_triad_notes(self, root, quality, extension, additions, expected):
        """Test major triad note generation."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("A", ChordQuality.MINOR, None, None, [9, 0, 4]),
    ])
    def test_minor_triad_notes(self, root, quality, extension, additions, expected):
        """Test minor triad note generation."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("B", ChordQuality.DIMINISHED, None, None, [11, 2, 5]),
    ])
    def test_diminished_triad_notes(self, root, quality, extension, additions, expected):
        """Test diminished triad note generation."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C", ChordQuality.AUGMENTED, None, None, [0, 4, 8]),
    ])
    def test_augmented_triad_notes(self, root, quality, extension, additions, expected):
        """Test augmented triad note generation."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C", ChordQuality.SUSPENDED_2, None, None, [0, 2, 7]),
        ("C", ChordQuality.SUSPENDED_4, None, None, [0, 5, 7]),
    ])
    def test_suspended_chord_notes(self, root, quality, extension, additions, expected):
        """Test suspended chord note generation."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C", ChordQuality.MAJOR, ChordExtension.SEVENTH, None, [0, 4, 7, 10]),
        ("C", ChordQuality.MAJOR, ChordExtension.MAJOR_SEVENTH, None, [0, 4, 7, 11]),
    ])
    def test_seventh_chord_notes(self, root, quality, extension, additions, expected):
        """Test seventh chord note generation."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C", ChordQuality.MAJOR, ChordExtension.NINTH, None, [0, 4, 7, 10, 2]),
    ])
    def test_extended_chord_notes(self, root, quality, extension, additions, expected):
        """Test extended chord note generation."""
        chord = Chord(Note(root).with_octave(1), quality, extension=extension, additions=additions)
        #assert chord.notes == expected
        assert [note.pitch_class for note in chord.notes] == expected

    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C", ChordQuality.MAJOR, None, ["9"], [0, 4, 7, 2]),
    ])
    def test_added_tone_chord_notes(self, root, quality, extension, additions, expected):
        """Test chord notes with added tones."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [note.pitch_class for note in chord.notes] == expected

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
        c4_maj9 = Chord("C4", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_NINTH)
        notes = c4_maj9.notes
        
        # Extended notes should go into higher octaves
        for note in notes:
            assert note.octave in [4, 5]


class TestChordScoreEvents:
    """Test score event conversion behavior for Chord."""

    def test_chord_emits_single_score_event_with_all_tones(self):
        """Chord conversion should emit one event containing all chord pitches."""
        context = ScoreEventContext(default_duration=Duration.from_beats(3, 4), velocity=75)

        events = Chord.from_string("C4").score_events_for_context(context)

        assert len(events) == 1
        event = events[0]
        assert event.beat == Duration.from_beats(0)
        assert event.duration == Duration.from_beats(3, 4)
        assert event.pitches == (60, 64, 67)
        assert event.velocity == 75
        assert event.spelling == ("C4", "E4", "G4")

    def test_chord_without_octave_raises_value_error(self):
        """Chord conversion requires octave information on all notes."""
        with pytest.raises(ValueError, match="requires octave information"):
            Chord.from_string("C").score_events_for_context(ScoreEventContext())

    def test_chord_event_uses_context_channel_voice_and_offset(self):
        """Chord event should preserve context timing and playback routing fields."""
        context = ScoreEventContext(
            start_offset=Duration.from_beats(2),
            default_duration=Duration.from_beats(1, 8),
            velocity=70,
            channel=7,
            voice=4,
        )

        event = Chord("C4").score_events_for_context(context)[0]

        assert event.beat == Duration.from_beats(2)
        assert event.duration == Duration.from_beats(1, 8)
        assert event.velocity == 70
        assert event.channel == 7
        assert event.voice == 4

    def test_chord_with_inversion_emits_inverted_pitch_order(self):
        """Chord inversion should be reflected in the emitted pitch and spelling order."""
        event = Chord("C4", inversion=1).score_events_for_context(ScoreEventContext())[0]

        assert event.pitches == (64, 67, 72)
        assert event.spelling == ("E4", "G4", "C5")

    def test_chord_with_bass_note_inserts_bass_first(self):
        """Slash-chord bass notes not in the triad should be inserted at the bottom."""
        event = Chord("C4", bass_note="B3").score_events_for_context(ScoreEventContext())[0]

        assert event.pitches == (59, 60, 64, 67)
        assert event.spelling == ("B3", "C4", "E4", "G4")

    def test_chord_with_any_tone_missing_octave_raises_value_error(self):
        """Custom-note chords require octave information for every emitted tone."""
        chord = Chord.from_notes(["C4", "E", "G4"])

        with pytest.raises(ValueError, match="requires octave information"):
            chord.score_events_for_context(ScoreEventContext())


class TestChordNotesWithOctaves:
    """Test that chord notes have correct octaves based on proper voice leading."""
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("B3", ChordQuality.MAJOR, None, None, ["B3", "D#4", "F#4"]),
        ("C4", ChordQuality.MAJOR, None, None, ["C4", "E4", "G4"]),
        ("G3", ChordQuality.MAJOR, None, None, ["G3", "B3", "D4"]),
    ])
    def test_major_chord_octave_distribution(self, root, quality, extension, additions, expected):
        """Test major chord octave distribution follows proper voice leading."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [str(n) for n in chord.notes] == expected
    
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("A3", ChordQuality.MINOR, None, None, ["A3", "C4", "E4"]),
        ("D4", ChordQuality.MINOR, None, None, ["D4", "F4", "A4"]),
    ])
    def test_minor_chord_octave_distribution(self, root, quality, extension, additions, expected):
        """Test minor chord octave distribution follows proper voice leading."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [str(n) for n in chord.notes] == expected
    
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C4", ChordQuality.MAJOR, ChordExtension.MAJOR_SEVENTH, None, ["C4", "E4", "G4", "B4"]),
        ("G3", ChordQuality.MAJOR, ChordExtension.SEVENTH, None, ["G3", "B3", "D4", "F4"]),
    ])
    def test_seventh_chord_octave_distribution(self, root, quality, extension, additions, expected):
        """Test seventh chord octave distribution."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [str(n) for n in chord.notes] == expected
    
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C4", ChordQuality.MAJOR, ChordExtension.MAJOR_NINTH, None, ["C4", "E4", "G4", "B4", "D5"]),
        ("F3", ChordQuality.MINOR, ChordExtension.SEVENTH, [intervals.MAJOR_SECOND], ["F3", "G3", "Ab3", "C4", "Eb4"]),
    ])
    def test_extended_chord_octave_distribution(self, root, quality, extension, additions, expected):
        """Test extended chord octave distribution across multiple octaves."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        print(str(chord))
        assert [str(n) for n in chord.notes] == expected
    
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("F#3", ChordQuality.MAJOR, None, None, ["F#3", "A#3", "C#4"]),
        ("Bb3", ChordQuality.MAJOR, None, None, ["Bb3", "D4", "F4"]),
    ])
    def test_sharp_flat_chord_octave_distribution(self, root, quality, extension, additions, expected):
        """Test octave distribution with sharp and flat notes."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [str(n) for n in chord.notes] == expected
    
    @pytest.mark.parametrize("root,quality,extension,additions,expected", [
        ("C4", ChordQuality.DIMINISHED, None, None, ["C4", "Eb4", "Gb4"]),
        ("C4", ChordQuality.AUGMENTED, None, None, ["C4", "E4", "G#4"]),
    ])
    def test_diminished_augmented_chord_octaves(self, root, quality, extension, additions, expected):
        """Test octave distribution for diminished and augmented chords."""
        chord = Chord(root, quality, extension=extension, additions=additions)
        assert [str(n) for n in chord.notes] == expected


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
        
        assert c7.extension == ChordExtension.SEVENTH
        assert c7.root == c_major.root
        assert c7.quality == c_major.quality
        
        # Original chord should be unchanged
        assert c_major.extension is None


class TestChordImmutability:
    """Test that Chord instances are immutable and copy-constructor methods work correctly."""
    
    def test_chord_immutability(self):
        """Test that chord attributes cannot be modified after creation."""
        chord = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)
        
        # Test that attributes cannot be modified
        with pytest.raises(AttributeError):
            chord.root = Note("D")
        
        with pytest.raises(AttributeError):
            chord.quality = ChordQuality.MINOR
        
        with pytest.raises(AttributeError):
            chord.extension = ChordExtension.NINTH
        
        with pytest.raises(AttributeError):
            chord.bass_note = Note("E")
        
        with pytest.raises(AttributeError):
            chord.inversion = 1
    
    def test_immutable_collections(self):
        """Test that collections returned by properties are immutable tuples."""
        chord = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.NINTH)
        
        # Test that extension returns a ChordExtension
        extension = chord.extension
        assert isinstance(extension, ChordExtension)
        assert extension == ChordExtension.NINTH
        
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
        assert original.extension is None
        
        # New chord should have the extension
        assert with_seventh.extension == ChordExtension.SEVENTH
        
        # Other properties should be preserved
        assert with_seventh.root == original.root
        assert with_seventh.quality == original.quality
        assert with_seventh.bass_note == original.bass_note
        assert with_seventh.inversion == original.inversion
    
    def test_with_root_copy_constructor(self):
        """Test with_root copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)
        
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
        assert with_new_root.extension == original.extension
        assert with_new_root.bass_note == original.bass_note
        assert with_new_root.inversion == original.inversion

    def test_with_octave_copy_constructor(self):
        """Test with_octave copy constructor method."""
        original = Chord("B", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH, bass_note="G#", inversion=2)

        # Change octave
        with_new_octave = original.with_octave(5)

        # Should return new instance
        assert with_new_octave is not original

        # Original should be unchanged
        assert original.root.name == NoteName.B
        assert original.root.octave == None

        assert with_new_octave.root.name == NoteName.B
        assert with_new_octave.root.octave == 5

        # Other properties should be preserved
        assert with_new_octave.quality == original.quality
        assert with_new_octave.extension == original.extension
        assert with_new_octave.bass_note == original.bass_note
        assert with_new_octave.inversion == original.inversion

    def test_with_octave_none_copy_constructor(self):
        """Test with_octave copy constructor method with None."""
        original = Chord("B4", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH, bass_note="G#3", inversion=2)

        # Change octave to None
        with_no_octave = original.with_octave(None)

        # Should return new instance
        assert with_no_octave is not original

        # Original should be unchanged
        assert original.root.name == NoteName.B
        assert original.root.octave == 4

        assert with_no_octave.root.name == NoteName.B
        assert with_no_octave.root.octave == None

        # Other properties should be preserved
        assert with_no_octave.quality == original.quality
        assert with_no_octave.extension == original.extension
        assert with_no_octave.bass_note == original.bass_note
        assert with_no_octave.inversion == original.inversion
    
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
        assert with_bass.extension == original.extension
        assert with_bass.inversion == original.inversion
    
    def test_with_inversion_copy_constructor(self):
        """Test with_inversion copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Set inversion
        with_inversion = original.with_inversion(1)
        
        # Should return new instance
        assert with_inversion is not original
        
        # Original should be unchanged
        assert original.inversion == 0
        
        # New chord should have the inversion
        assert with_inversion.inversion == 1
        
        # Other properties should be preserved
        assert with_inversion.root == original.root
        assert with_inversion.quality == original.quality
        assert with_inversion.extension == original.extension
        assert with_inversion.bass_note == original.bass_note
    
    def test_with_method_generic_copy_constructor(self):
        """Test the generic with_() copy constructor method."""
        original = Chord("C", ChordQuality.MAJOR)
        
        # Modify multiple properties
        modified = original.with_(
            root="G",
            quality=ChordQuality.MINOR,
            extension=ChordExtension.SEVENTH,
            bass_note="D"
        )
        
        # Should return new instance
        assert modified is not original
        
        # Original should be unchanged
        assert original.root.name == NoteName.C
        assert original.quality == ChordQuality.MAJOR
        assert original.extension is None
        assert original.bass_note is None
        
        # New chord should have all modifications
        assert modified.root.name == NoteName.G
        assert modified.quality == ChordQuality.MINOR
        assert modified.extension == ChordExtension.SEVENTH
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
        assert original.extension is None
        assert original.bass_note is None
        assert original.inversion == 0
        
        # Final should have all modifications
        assert final.root.name == NoteName.C
        assert final.quality == ChordQuality.MAJOR
        assert final.extension == ChordExtension.SEVENTH
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
        assert g_major.extension == c_major.extension
    
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
        cmaj7 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH)
        minor_third = Interval(IntervalQuality.MINOR, 3)
        
        eb_maj7 = cmaj7.transpose(minor_third)
        
        assert eb_maj7.root.name == NoteName.E
        assert eb_maj7.root.accidental == Accidental.FLAT
        assert eb_maj7.quality == ChordQuality.MAJOR
        assert eb_maj7.extension == ChordExtension.MAJOR_SEVENTH

    def test_transpose_accepts_interval_like_string(self):
        """String interval representations should be coerced for transposition."""
        c_major = Chord("C", ChordQuality.MAJOR)

        g_major = c_major.transpose("5")

        assert g_major.root.name == NoteName.G
        assert g_major.quality == ChordQuality.MAJOR


class TestChordDegreeHelpers:
    """Test DegreeLike helpers on Chord APIs."""

    def test_tone_at_accepts_degree_like(self):
        c_major = Chord("C", ChordQuality.MAJOR)

        assert str(c_major.tone_at(1)) == "C"
        assert str(c_major.tone_at(Degree(2))) == "E"
        assert str(c_major.tone_at("III")) == "G"

    def test_tone_at_invalid_degree_raises(self):
        c_major = Chord("C", ChordQuality.MAJOR)

        with pytest.raises(ValueError):
            c_major.tone_at(0)

        with pytest.raises(ValueError):
            c_major.tone_at(4)

        with pytest.raises(ValueError):
            c_major.tone_at("bIII")

    def test_degree_for_tone_returns_degree(self):
        g7 = Chord("G", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)

        assert g7.degree_for_tone(Note("G")) == Degree(1)
        assert g7.degree_for_tone(Note("B")) == Degree(2)
        assert g7.degree_for_tone(Note("D")) == Degree(3)
        assert g7.degree_for_tone(Note("F")) == Degree(4)
        assert g7.degree_for_tone(Note("C")) is None


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
        assert c7.extension == ChordExtension.SEVENTH
        
        cmaj7 = major_seventh_chord("C")
        assert cmaj7.extension == ChordExtension.MAJOR_SEVENTH

        cm7 = minor_seventh_chord("C")
        assert cm7.quality == ChordQuality.MINOR
        assert cm7.extension == ChordExtension.SEVENTH

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
        c7_1 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)
        c7_2 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)
        cmaj7 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH)

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

        c_power = Chord("C", ChordQuality.POWER)
        assert c_power.name == "C(5)"
    
    def test_chord_name_with_extensions(self):
        """Test chord names with extensions."""
        assert Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH).name == "C(7)"
        assert Chord("C", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH).name == "C(maj7)"
        assert Chord("C", ChordQuality.MINOR, extension=ChordExtension.SEVENTH).name == "Cm(7)"
    
    def test_chord_name_with_additions(self):
        """Test chord names with additions."""
        cadd9 = Chord("C", ChordQuality.MAJOR, additions=["9"])
        assert "(add9)" in cadd9.name
    
    def test_chord_name_with_bass(self):
        """Test chord names with bass notes."""
        c_over_e = Chord("C", ChordQuality.MAJOR, bass_note="E")
        assert c_over_e.name == "C/E"
        
        am_over_c = Chord("A", ChordQuality.MINOR, bass_note="C")
        assert am_over_c.name == "Am/C"
    
    def test_str(self):
        """Test __str__ method."""
        c_major = Chord("C", ChordQuality.MAJOR)
        assert str(c_major) == "C"
        
        c7 = Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH)
        assert str(c7) == "C(7)"
    
    def test_repr(self):
        """Test __repr__ method."""
        assert repr(Chord("C", ChordQuality.MAJOR)) == '<Chord(C)[C, E, G]>'
        assert repr(Chord("C3", ChordQuality.MAJOR, "maj7")) == '<Chord(C3(maj7))[C3, E3, G3, B3]>'


class TestChordRoundTrip:
    """Test round-trip conversion between Chord objects and chord strings."""

    @pytest.mark.parametrize("chord", [
        Chord("C", ChordQuality.MAJOR),
        Chord("C5", ChordQuality.MAJOR),
        Chord("F#3", ChordQuality.MINOR),
        Chord("Bb2", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH),
        Chord("E4", ChordQuality.AUGMENTED),
        Chord("D3", ChordQuality.DIMINISHED),
        Chord("G4", ChordQuality.SUSPENDED_2),
        Chord("A3", ChordQuality.SUSPENDED_4),
        Chord("C", ChordQuality.POWER),
        Chord("C4", ChordQuality.POWER),
        Chord("C", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH),
        Chord("C", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH),
        Chord("C", ChordQuality.MINOR, extension=ChordExtension.SEVENTH),
        Chord("E", ChordQuality.MINOR, extension=ChordExtension.MAJOR_SEVENTH),
        Chord("F#", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_NINTH),
        Chord("Bb", ChordQuality.MAJOR, extension=ChordExtension.THIRTEENTH),
        Chord("C", ChordQuality.MAJOR, additions=["9"]),
        Chord("D", ChordQuality.MAJOR, additions=["#11"]),
        Chord("A", ChordQuality.MINOR, additions=["11"]),
        Chord("C", ChordQuality.MAJOR, extension=ChordExtension.MAJOR_SEVENTH, additions=["9"]),
        Chord("G", ChordQuality.MAJOR, extension=ChordExtension.SEVENTH, additions=["9", "13"]),
        Chord("C", ChordQuality.MAJOR, omissions=["3"]),
        Chord("D", ChordQuality.MINOR, extension=ChordExtension.SEVENTH, omissions=["5"]),
        Chord("C", ChordQuality.MAJOR, bass_note="E"),
        Chord("A", ChordQuality.MINOR, bass_note="C"),
        Chord("G", ChordQuality.MAJOR, bass_note="B"),
        Chord("C4", ChordQuality.MAJOR, bass_note="E3"),
        Chord("F#3", ChordQuality.MINOR, extension=ChordExtension.SEVENTH, bass_note="A2"),
    ])
    def test_from_string_of_str_round_trip(self, chord):
        """Chord.from_string(str(x)) should recreate x for supported string forms."""
        assert Chord.from_string(str(chord)) == chord


class TestChordEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_power_chord(self):
        """Test power chord (just root and fifth)."""
        c5 = Chord("C", ChordQuality.POWER)
        notes = c5.notes
        
        expected_pitch_classes = [0, 7]  # C, G
        actual_pitch_classes = [note.pitch_class for note in notes]
        
        assert actual_pitch_classes == expected_pitch_classes
    
    def test_chord_with_extensions_and_additions(self):
        """Test chord with multiple extensions."""
        complex_chord = Chord(
            "C", ChordQuality.MAJOR,
            extension=ChordExtension.MAJOR_SEVENTH,
            additions=["11", "13"]
        )
        
        pitch_classes = set(note.pitch_class for note in complex_chord.notes)
        assert pitch_classes == {
            0,   # Root
            4,   # Third
            7,   # Fifth
            11,  # Major seventh
            5,   # Eleventh (same as fourth)
            9,   # Thirteenth (same as sixth)
        }
    
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

