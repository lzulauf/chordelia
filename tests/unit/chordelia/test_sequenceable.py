"""Tests for the Sequenceable protocol and score normalization boundary."""

import pytest

from chordelia.chords import Chord
from chordelia.intervals import Interval
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.scale_context import with_global_scale_context
from chordelia.sequences import Rest, Sequence, SequenceEntry
from chordelia.score import Score, ScoreEvent, ScoreEventContext
from chordelia.sequenceable import (
    NotesLike,
    SequenceRender,
    Sequenceable,
    _sequence_render_for,
)


class TestSequenceableProtocol:
    """Runtime protocol checks for canonical sequenceable implementers."""

    class RenderOnly:
        """Implements rendering but intentionally omits transpose."""

        def render_for_context(self, context):
            return SequenceRender(events=(), consumed_duration=context.default_duration)

    def test_note_is_runtime_sequenceable(self):
        """Note exposes the required render_for_context protocol surface."""
        assert isinstance(Note("C4"), Sequenceable)

    def test_chord_is_runtime_sequenceable(self):
        """Chord exposes the required render_for_context protocol surface."""
        assert isinstance(Chord.from_string("C4"), Sequenceable)

    def test_sequence_is_runtime_sequenceable(self):
        """Sequence exposes the required render_for_context protocol surface."""
        seq = Sequence((SequenceEntry(payload=Note("C4"), duration=1),))
        assert isinstance(seq, Sequenceable)

    def test_rest_is_runtime_sequenceable(self):
        """Rest should satisfy Sequenceable and emit silence via the same boundary."""
        assert isinstance(Rest(), Sequenceable)

    def test_render_only_value_is_not_runtime_sequenceable(self):
        """Sequenceable requires transpose as part of the canonical protocol."""
        assert not isinstance(self.RenderOnly(), Sequenceable)

    def test_note_is_runtime_notes_like(self):
        assert isinstance(Note("C4"), NotesLike)

    def test_chord_is_runtime_notes_like(self):
        assert isinstance(Chord.from_string("C4"), NotesLike)

    def test_rest_is_runtime_notes_like(self):
        assert isinstance(Rest(), NotesLike)


class TestSequenceRenderBoundary:
    """SequenceRender conversion behavior without adapter fallback."""

    class ExternalTone:
        """Simple direct Sequenceable value used for conversion tests."""

        def __init__(self, midi_number: int):
            self.midi_number = midi_number

        def render_for_context(self, context):
            return SequenceRender(
                events=(
                    ScoreEvent(
                        beat=context.start_offset,
                        duration=context.default_duration,
                        pitches=(self.midi_number,),
                        velocity=context.velocity,
                        channel=context.channel,
                        voice=context.voice,
                    ),
                ),
                consumed_duration=context.default_duration,
            )

        def transpose(self, _interval):
            return self

    def test_sequence_render_for_uses_sequenceable_values_directly(self):
        """_sequence_render_for should consume Sequenceable values directly."""

        context = ScoreEventContext(start_offset=1, default_duration=2, velocity=88)
        render = _sequence_render_for(self.ExternalTone(72), context)
        events = render.events

        assert len(events) == 1
        assert events[0].beat == Duration.from_beats(1)
        assert events[0].duration == Duration.from_beats(2)
        assert events[0].pitches == (72,)
        assert events[0].velocity == 88
        assert render.consumed_duration == Duration.from_beats(2)

    def test_sequence_render_for_raises_for_unsupported_values(self):
        """Unsupported values should fail with actionable guidance."""
        with pytest.raises(TypeError, match="not Sequenceable"):
            _sequence_render_for(object(), ScoreEventContext())

    def test_sequence_render_normalizes_note_fraction_consumed_duration(self):
        """SequenceRender should normalize note-fraction Duration consumed inputs."""
        render = SequenceRender(events=(), consumed_duration=Duration("quarter"))

        assert render.consumed_duration == Duration.from_beats(1)


class TestScoreFromSequenceable:
    """Score normalization behavior from direct sequenceable values."""

    class ExternalPattern:
        """Sequenceable helper used to verify deterministic score sorting."""

        def render_for_context(self, _context):
            return SequenceRender(
                events=(
                    ScoreEvent(beat=2, duration=1, pitches=(64,), channel=1),
                    ScoreEvent(beat=1, duration=1, pitches=(60,), channel=1),
                    ScoreEvent(beat=1, duration=1, pitches=(67,), channel=0),
                ),
                consumed_duration=Duration.from_beats(3),
            )

        def transpose(self, _interval):
            return self

    def test_score_from_sequenceable_includes_metadata(self):
        """Score constructor should preserve metadata defaults and overrides."""
        score = Score.from_sequenceable(
            Note("D4"),
            tempo=96,
            time_signature=(3, 4),
            key_signature="D",
        )

        assert len(score.events) == 1
        assert score.events[0].pitches == (62,)
        assert score.metadata.tempo == 96
        assert score.metadata.time_signature == (3, 4)
        assert score.metadata.key_signature == "D"

    def test_score_from_sequenceable_sorts_events_deterministically(self):
        """Score should normalize event ordering for any Sequenceable source."""

        score = Score.from_sequenceable(self.ExternalPattern())

        assert [event.pitches for event in score.events] == [(67,), (60,), (64,)]
        assert [event.beat for event in score.events] == [
            Duration.from_beats(1),
            Duration.from_beats(1),
            Duration.from_beats(2),
        ]
        assert score.duration == Duration.from_beats(3)


class TestSequenceScheduling:
    """Sequence-specific deterministic scheduling behavior."""

    def test_sequence_entry_coerce_from_two_tuple(self):
        entry = SequenceEntry.coerce((Note("C4"), 2))

        assert isinstance(entry, SequenceEntry)
        assert entry.duration == Duration.from_beats(2)
        assert entry.offset is None

    def test_sequence_entry_coerce_from_three_tuple(self):
        entry = SequenceEntry.coerce((Note("C4"), 2, 1))

        assert isinstance(entry, SequenceEntry)
        assert entry.duration == Duration.from_beats(2)
        assert entry.offset == Duration.from_beats(1)

    def test_sequence_entry_coerce_rejects_bad_tuple_arity(self):
        with pytest.raises(ValueError, match="tuple form must be"):
            SequenceEntry.coerce((Note("C4"),))

    def test_sequence_coerces_iterable_of_notes_to_chord_payload(self):
        seq = Sequence(
            (
                (["C4", "E4", "G4"], 1),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 1
        assert events[0].pitches == (60, 64, 67)

    def test_sequence_coerces_iterable_of_chords_to_simultaneous_layers(self):
        seq = Sequence(
            (
                (
                    [
                        Chord.from_notes(["C4", "E4"]),
                        Chord.from_notes(["G4"]),
                    ],
                    1,
                ),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 2
        assert events[0].beat == Duration.from_beats(0)
        assert events[1].beat == Duration.from_beats(0)
        assert events[0].pitches == (60, 64)
        assert events[1].pitches == (67,)

    def test_sequence_coerces_mixed_iterable_notes_like_to_simultaneous_layers(self):
        seq = Sequence(
            (
                (
                    [
                        Rest(),
                        Note("C4"),
                        Chord.from_notes(["E4", "G4"]),
                    ],
                    1,
                ),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 2
        assert events[0].pitches == (60,)
        assert events[1].pitches == (64, 67)

    def test_sequence_preserves_boundaries_for_simultaneous_layers(self):
        seq = Sequence(
            (
                (
                    [
                        Chord.from_notes(["C4", "E4"]),
                        Note("G4"),
                    ],
                    2,
                ),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 2
        assert [event.beat for event in events] == [Duration.from_beats(0), Duration.from_beats(0)]
        assert [event.duration for event in events] == [Duration.from_beats(2), Duration.from_beats(2)]
        assert [event.pitches for event in events] == [(60, 64), (67,)]

    def test_sequence_preserves_boundaries_for_mixed_note_strings_and_chords(self):
        seq = Sequence(
            (
                (
                    [
                        "C4",
                        Chord.from_notes(["E4", "G4"]),
                    ],
                    1,
                ),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 2
        assert [event.beat for event in events] == [Duration.from_beats(0), Duration.from_beats(0)]
        assert [event.pitches for event in events] == [(60,), (64, 67)]

    def test_sequence_schedules_entries_sequentially(self):
        seq = Sequence(
            (
                SequenceEntry(payload=Note("C4"), duration=1),
                SequenceEntry(payload=Note("E4"), duration=2),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 2
        assert events[0].beat == Duration.from_beats(0)
        assert events[0].duration == Duration.from_beats(1)
        assert events[0].pitches == (60,)
        assert events[1].beat == Duration.from_beats(1)
        assert events[1].duration == Duration.from_beats(2)
        assert events[1].pitches == (64,)

    def test_sequence_offsets_are_relative_to_context_start(self):
        seq = Sequence(
            (
                SequenceEntry(payload=Note("C4"), duration=1, offset=2),
                SequenceEntry(payload=Note("D4"), duration=1),
            )
        )

        events = seq.render_for_context(ScoreEventContext(start_offset=Duration.from_beats(3))).events

        assert [event.beat for event in events] == [
            Duration.from_beats(5),
            Duration.from_beats(6),
        ]

    def test_sequence_entry_accepts_note_fraction_duration_and_offset(self):
        seq = Sequence(
            (
                SequenceEntry(
                    payload=Note("C4"),
                    duration=Duration("eighth"),
                    offset=Duration("quarter"),
                ),
            )
        )

        render = seq.render_for_context(ScoreEventContext())

        assert render.events[0].beat == Duration.from_beats(1)
        assert render.events[0].duration == Duration.from_beats(1, 2)
        assert render.consumed_duration == Duration.from_beats(3, 2)

    def test_sequence_rest_entries_emit_no_events(self):
        seq = Sequence(
            (
                SequenceEntry(payload=Note("C4"), duration=1),
                SequenceEntry(payload=Rest(), duration=2),
                SequenceEntry(payload=Note("D4"), duration=1),
            )
        )

        events = seq.render_for_context(ScoreEventContext()).events

        assert len(events) == 2
        assert events[0].beat == Duration.from_beats(0)
        assert events[1].beat == Duration.from_beats(3)

    def test_sequence_supports_nested_sequences(self):
        inner = Sequence((SequenceEntry(payload=Note("E4"), duration=1),))
        outer = Sequence(
            (
                SequenceEntry(payload=Note("C4"), duration=1),
                SequenceEntry(payload=inner, duration=2),
            )
        )

        events = outer.render_for_context(ScoreEventContext()).events

        assert [event.pitches for event in events] == [(60,), (64,)]
        assert [event.beat for event in events] == [
            Duration.from_beats(0),
            Duration.from_beats(1),
        ]

    def test_sequence_constructor_supports_child_sequences_with_span_consumption(self):
        motif = Sequence(
            (
                (Note("C4"), 1),
                (Note("D4"), 1),
            )
        )
        combined = Sequence((motif, motif))

        render = combined.render_for_context(ScoreEventContext())
        events = render.events

        assert [event.pitches for event in events] == [(60,), (62,), (60,), (62,)]
        assert [event.beat for event in events] == [
            Duration.from_beats(0),
            Duration.from_beats(1),
            Duration.from_beats(2),
            Duration.from_beats(3),
        ]
        assert render.consumed_duration == Duration.from_beats(4)

    def test_sequence_consumed_duration_for_child_note_and_chord_sequences(self):
        child_notes = Sequence(
            (
                (Note("C4"), 2),
                (Note("D4"), 1),
            )
        )
        child_chords = Sequence(
            (
                (Chord.from_notes(["E4", "G4"]), 3),
                (Chord.from_notes(["F4", "A4"]), 1),
            )
        )
        parent = Sequence((child_notes, child_chords))

        render = parent.render_for_context(ScoreEventContext())
        events = render.events

        assert [event.beat for event in events] == [
            Duration.from_beats(0),
            Duration.from_beats(2),
            Duration.from_beats(3),
            Duration.from_beats(6),
        ]
        assert [event.duration for event in events] == [
            Duration.from_beats(2),
            Duration.from_beats(1),
            Duration.from_beats(3),
            Duration.from_beats(1),
        ]
        assert render.consumed_duration == Duration.from_beats(7)

    def test_sequence_consumed_duration_for_repeated_child_sequences(self):
        child_notes = Sequence(
            (
                (Note("A3"), 1),
                (Note("B3"), 2),
            )
        )
        child_chords = Sequence(
            (
                (Chord.from_notes(["C4", "E4", "G4"]), 2),
            )
        )
        parent = Sequence([child_notes, child_chords, child_notes])

        render = parent.render_for_context(ScoreEventContext())

        # child_notes span=3, child_chords span=2, child_notes span=3
        assert render.consumed_duration == Duration.from_beats(8)
        assert [event.beat for event in render.events] == [
            Duration.from_beats(0),
            Duration.from_beats(1),
            Duration.from_beats(3),
            Duration.from_beats(5),
            Duration.from_beats(6),
        ]

    def test_sequence_constructor_supports_list_multiplied_child_sequences(self):
        motif = Sequence(
            (
                (Chord.from_notes(["A3", "C4", "E4"]), 1),
                (Chord.from_notes(["D3", "F4", "A4"]), 1),
            )
        )
        repeated = Sequence([motif] * 3)

        render = repeated.render_for_context(ScoreEventContext())
        events = render.events

        assert len(events) == 6
        assert [event.beat for event in events] == [
            Duration.from_beats(0),
            Duration.from_beats(1),
            Duration.from_beats(2),
            Duration.from_beats(3),
            Duration.from_beats(4),
            Duration.from_beats(5),
        ]
        assert render.consumed_duration == Duration.from_beats(6)

    def test_sequence_constructor_accepts_bare_sequenceable_values(self):
        seq = Sequence(
            (
                Note("C4"),
                Chord.from_notes(["E4", "G4"]),
            )
        )

        render = seq.render_for_context(ScoreEventContext())
        events = render.events

        assert len(events) == 2
        assert [event.pitches for event in events] == [(60,), (64, 67)]
        assert [event.beat for event in events] == [Duration.from_beats(0), Duration.from_beats(1)]
        assert [event.duration for event in events] == [Duration.from_beats(1), Duration.from_beats(1)]
        assert render.consumed_duration == Duration.from_beats(2)

    def test_sequence_constructor_treats_child_sequence_like_other_sequenceables(self):
        motif = Sequence(
            (
                (Note("C4"), 2),
                (Note("D4"), 3),
            )
        )
        seq = Sequence((motif,))

        assert len(seq.entries) == 1
        assert seq.entries[0].duration == Duration.from_beats(1)

        render = seq.render_for_context(ScoreEventContext())
        assert render.consumed_duration == Duration.from_beats(5)
        assert [event.beat for event in render.events] == [Duration.from_beats(0), Duration.from_beats(2)]

    def test_rest_emits_no_events_via_sequenceable_boundary(self):
        """Rest conversion should succeed through _sequence_render_for and return no events."""
        render = _sequence_render_for(Rest(), ScoreEventContext())
        assert render.events == ()
        assert render.consumed_duration == Duration.from_beats(1)


@pytest.mark.usefixtures("reset_global_scale_context_state")
class TestSequenceTransforms:
    """Sequence transform behavior and recursive transpose semantics."""

    def test_sequence_transpose_preserves_timing_and_updates_pitches(self):
        seq = Sequence(
            (
                SequenceEntry(payload=Note("C4"), duration=2, offset=1),
                SequenceEntry(payload=Chord("E4"), duration=1),
            )
        )

        transposed = seq.transpose("2")
        original_render = seq.render_for_context(ScoreEventContext())
        transposed_render = transposed.render_for_context(ScoreEventContext())

        assert [event.beat for event in transposed_render.events] == [
            Duration.from_beats(1),
            Duration.from_beats(3),
        ]
        assert [event.duration for event in transposed_render.events] == [
            Duration.from_beats(2),
            Duration.from_beats(1),
        ]
        assert [event.pitches for event in transposed_render.events] == [(62,), (66, 70, 73)]
        assert transposed_render.consumed_duration == Duration.from_beats(4)

        # Transpose should return a new sequence and leave the original unchanged.
        assert transposed is not seq
        assert [event.pitches for event in original_render.events] == [(60,), (64, 68, 71)]

    def test_sequence_transpose_recurses_into_nested_sequences(self):
        motif = Sequence(
            (
                (Note("C4"), 1),
                (Note("E4"), 1),
            )
        )
        arrangement = Sequence(
            (
                motif,
                SequenceEntry(payload=Chord("G4"), duration=2),
            )
        )

        transposed = arrangement.transpose(Interval.from_semitones(-2))
        render = transposed.render_for_context(ScoreEventContext())

        assert [event.beat for event in render.events] == [
            Duration.from_beats(0),
            Duration.from_beats(1),
            Duration.from_beats(2),
        ]
        assert [event.pitches for event in render.events] == [(58,), (62,), (65, 69, 72)]
        assert render.consumed_duration == Duration.from_beats(4)

    def test_sequence_transpose_recurses_into_simultaneous_layers(self):
        seq = Sequence(
            (
                (
                    [
                        Chord("C4"),
                        Note("G4"),
                    ],
                    1,
                ),
            )
        )

        transposed = seq.transpose("2")
        render = transposed.render_for_context(ScoreEventContext())

        assert [event.pitches for event in render.events] == [(62, 66, 69), (69,)]
        assert [event.beat for event in render.events] == [Duration.from_beats(0), Duration.from_beats(0)]

    def test_sequence_transpose_int_uses_semitones(self):
        seq = Sequence(((Note("C4"), 1),))

        transposed = seq.transpose(1)
        render = transposed.render_for_context(ScoreEventContext())

        assert [event.pitches for event in render.events] == [(61,)]

    def test_sequence_transpose_raises_for_unsupported_payloads(self):
        seq = Sequence((SequenceEntry(payload=object(), duration=1),))

        with pytest.raises(ValueError, match="transpose\(interval\)"):
            seq.transpose("2")

    def test_sequence_shift_preserves_timing_and_updates_pitches(self):
        seq = Sequence(
            (
                SequenceEntry(payload=Note("C4"), duration=2, offset=1),
                SequenceEntry(payload=Chord("E4"), duration=1),
            )
        )

        shifted = seq.shift(1, scale="C")
        original_render = seq.render_for_context(ScoreEventContext())
        shifted_render = shifted.render_for_context(ScoreEventContext())

        assert [event.beat for event in shifted_render.events] == [
            Duration.from_beats(1),
            Duration.from_beats(3),
        ]
        assert [event.duration for event in shifted_render.events] == [
            Duration.from_beats(2),
            Duration.from_beats(1),
        ]
        assert [event.pitches for event in shifted_render.events] == [(62,), (65, 69, 72)]
        assert shifted_render.consumed_duration == Duration.from_beats(4)

        assert shifted is not seq
        assert [event.pitches for event in original_render.events] == [(60,), (64, 68, 71)]

    def test_sequence_shift_recurses_into_nested_sequences(self):
        motif = Sequence(
            (
                (Note("C4"), 1),
                (Note("E4"), 1),
            )
        )
        arrangement = Sequence(
            (
                motif,
                SequenceEntry(payload=Chord("G4"), duration=2),
            )
        )

        shifted = arrangement.shift(-1, scale="C")
        render = shifted.render_for_context(ScoreEventContext())

        assert [event.beat for event in render.events] == [
            Duration.from_beats(0),
            Duration.from_beats(1),
            Duration.from_beats(2),
        ]
        assert [event.pitches for event in render.events] == [(59,), (62,), (65, 69, 72)]
        assert render.consumed_duration == Duration.from_beats(4)

    def test_sequence_shift_recurses_into_simultaneous_layers(self):
        seq = Sequence(
            (
                (
                    [
                        Chord("C4"),
                        Note("G4"),
                    ],
                    1,
                ),
            )
        )

        shifted = seq.shift(1, scale="C")
        render = shifted.render_for_context(ScoreEventContext())

        assert [event.pitches for event in render.events] == [(62, 66, 69), (69,)]
        assert [event.beat for event in render.events] == [Duration.from_beats(0), Duration.from_beats(0)]

    def test_sequence_shift_uses_global_scale_context_when_scale_not_provided(self):
        seq = Sequence(((Note("E4"), 1),))

        with with_global_scale_context("C"):
            shifted = seq.shift(2)

        render = shifted.render_for_context(ScoreEventContext())
        assert [event.pitches for event in render.events] == [(67,)]

    def test_sequence_shift_without_any_scale_context_raises(self):
        seq = Sequence(((Note("C4"), 1),))

        with pytest.raises(ValueError, match="requires a scale context"):
            seq.shift(1)

    def test_sequence_shift_raises_for_unsupported_payloads(self):
        seq = Sequence((SequenceEntry(payload=object(), duration=1),))

        with pytest.raises(ValueError, match="shift\(steps\)"):
            seq.shift(1, scale="C")
