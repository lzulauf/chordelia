"""Tests for sequence-level randomization APIs and built-in algorithms."""

from __future__ import annotations

from fractions import Fraction

import pytest

from chordelia import (
    ChordAnchorWalkSequenceAlgorithm,
    MotifVariationSequenceAlgorithm,
    PureRandomSequenceAlgorithm,
    Random,
    ScaleWalkSequenceAlgorithm,
    SequenceRandomizationAlgorithm,
)
from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.scales import Scale, ScaleType
from chordelia.sequences import Sequence


pytestmark = pytest.mark.usefixtures(
    "reset_global_scale_context_state",
    "reset_global_random_state",
)


def _consumed_beats(sequence: Sequence) -> Fraction:
    return sum((entry.duration.as_beats() for entry in sequence.entries), Fraction(0, 1))


class TestRandomSequenceValidation:
    """Validation behavior for Random.sequence dispatch."""

    @pytest.mark.parametrize("beat_length", [0, -1, -0.5])
    def test_sequence_rejects_non_positive_beat_length(self, beat_length):
        with pytest.raises(ValueError, match="beat_length must be > 0"):
            Random(seed=1).sequence(beat_length)

    def test_sequence_rejects_seconds_mode_length(self):
        with pytest.raises(ValueError, match="beat-mode"):
            Random(seed=1).sequence(Duration.from_seconds(1))

    def test_sequence_rejects_unknown_algorithm_name(self):
        with pytest.raises(ValueError, match="Unknown sequence algorithm"):
            Random(seed=1).sequence(4, algorithm="missing")

    def test_sequence_rejects_unknown_algorithm_weight_keys(self):
        with pytest.raises(ValueError, match="Unknown sequence algorithm"):
            Random(seed=1).sequence(4, algorithm_weights={"missing": 1.0})

    def test_sequence_rejects_weights_with_explicit_algorithm(self):
        with pytest.raises(ValueError, match="cannot be used with an explicit algorithm"):
            Random(seed=1).sequence(
                4,
                algorithm=PureRandomSequenceAlgorithm(),
                algorithm_weights={"pure_random": 1.0},
            )

    def test_sequence_rejects_algorithm_params_wrapper_keyword(self):
        with pytest.raises(TypeError, match="algorithm_params wrapper is not supported"):
            Random(seed=1).sequence(
                4,
                algorithm="pure_random",
                scale="C major",
                algorithm_params={"mutation_probability": 0},
            )

    def test_sequence_rejects_duck_typed_non_subclass_algorithm_instance(self):
        class DuckAlgorithm:
            name = "duck"
            default_selection_weight = 1.0

            def generate(self, **kwargs):
                return Sequence(())

        with pytest.raises(TypeError, match="SequenceRandomizationAlgorithm instance"):
            Random(seed=1).sequence(4, algorithm=DuckAlgorithm())


class TestSequenceAlgorithmDiscovery:
    """Runtime discovery behavior for sequence algorithm subclasses."""

    def test_builtin_algorithms_are_direct_subclasses(self):
        direct = sorted(
            SequenceRandomizationAlgorithm.__subclasses__(),
            key=lambda subclass: subclass.__name__,
        )
        assert PureRandomSequenceAlgorithm in direct
        assert MotifVariationSequenceAlgorithm in direct
        assert ScaleWalkSequenceAlgorithm in direct
        assert ChordAnchorWalkSequenceAlgorithm in direct


class TestRandomSequenceDispatchAndDeterminism:
    """Dispatch paths and deterministic behavior checks."""

    def test_weighted_algorithm_selection_is_deterministic(self):
        rng_a = Random(seed=202606)
        rng_b = Random(seed=202606)
        weights = {
            "motif_variation": 40,
            "scale_walk": 30,
            "chord_anchor_walk": 20,
            "pure_random": 10,
        }

        seq_a = rng_a.sequence(8, algorithm_weights=weights, scale="A natural_minor")
        seq_b = rng_b.sequence(8, algorithm_weights=weights, scale="A natural_minor")

        assert seq_a == seq_b

    def test_motif_algorithm_instance_reuse_preserves_stateful_continuity(self):
        rng = Random(seed=77)
        motif = MotifVariationSequenceAlgorithm(motif_beats=2)

        seq_a = rng.sequence(
            8,
            algorithm=motif,
            scale="D minor",
            mutation_probability=0,
        )
        seq_b = rng.sequence(
            8,
            algorithm=motif,
            scale="D minor",
            mutation_probability=0,
        )

        assert motif._motif_template is not None
        assert seq_a == seq_b

    def test_motif_algorithm_accepts_explicit_motif_sequence_constructor_arg(self):
        rng = Random(seed=77)
        motif_sequence = Sequence(
            (
                (Note("C4"), 1),
                (Note("D4"), 1),
            )
        )
        motif = MotifVariationSequenceAlgorithm(
            motif_beats=2,
            motif_sequence=motif_sequence,
        )

        sequence = rng.sequence(
            4,
            algorithm=motif,
            mutation_probability=0,
        )

        expected = Sequence(
            (
                (Note("C4"), 1),
                (Note("D4"), 1),
                (Note("C4"), 1),
                (Note("D4"), 1),
            )
        )
        assert sequence == expected

    def test_motif_algorithm_constructor_rejects_non_sequence_motif_sequence(self):
        with pytest.raises(TypeError, match="motif_sequence must be a chordelia.sequences.Sequence"):
            MotifVariationSequenceAlgorithm(
                motif_sequence=[(Note("C4"), 1)],
            )

    def test_motif_algorithm_constructor_rejects_empty_motif_sequence(self):
        with pytest.raises(ValueError, match="motif_sequence must contain at least one entry"):
            MotifVariationSequenceAlgorithm(
                motif_sequence=Sequence(()),
            )

    def test_motif_algorithm_rejects_call_time_motif_sequence_arg(self):
        rng = Random(seed=77)
        motif = MotifVariationSequenceAlgorithm(motif_beats=2)

        with pytest.raises(TypeError, match="motif_sequence must be provided to"):
            rng.sequence(
                4,
                algorithm=motif,
                motif_sequence=Sequence(((Note("C4"), 1),)),
            )

    def test_motif_algorithm_mutation_handles_out_of_scale_motif_note(self):
        rng = Random(seed=77)
        motif = MotifVariationSequenceAlgorithm(
            motif_sequence=Sequence(((Note("C#4"), 1),))
        )

        sequence = rng.sequence(
            4,
            algorithm=motif,
            scale="C major",
            mutation_probability=1.0,
        )

        assert _consumed_beats(sequence) == Fraction(4, 1)
        assert len(sequence.entries) == 4
        assert all(isinstance(entry.payload, Note) for entry in sequence.entries)


class TestBuiltInSequenceAlgorithms:
    """Behavior checks for built-in sequence randomization algorithms."""

    @pytest.mark.parametrize(
        "algorithm, kwargs",
        [
            pytest.param(PureRandomSequenceAlgorithm(), {}, id="pure-random"),
            pytest.param(MotifVariationSequenceAlgorithm(), {}, id="motif-variation"),
            pytest.param(ScaleWalkSequenceAlgorithm(), {}, id="scale-walk"),
            pytest.param(
                ChordAnchorWalkSequenceAlgorithm(),
                {"chord": "Am"},
                id="chord-anchor-walk",
            ),
        ],
    )
    def test_algorithms_fill_exact_requested_beat_span(self, algorithm, kwargs):
        sequence = Random(seed=5).sequence(
            Fraction(15, 2),
            algorithm=algorithm,
            scale="C major",
            **kwargs,
        )

        assert _consumed_beats(sequence) == Fraction(15, 2)

    def test_scale_walk_notes_stay_in_scale(self):
        scale = Scale("E", ScaleType.NATURAL_MINOR)
        sequence = Random(seed=9).sequence(8, algorithm="scale_walk", scale=scale)

        allowed = {note.pitch_class for note in scale.notes}
        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.pitch_class in allowed

    def test_scale_walk_starts_and_ends_on_chord_tones_when_chord_provided(self):
        sequence = Random(seed=9).sequence(
            8,
            algorithm="scale_walk",
            scale="C major",
            chord="G",
        )

        chord_tones = {note.pitch_class for note in Chord.from_string("G").notes}
        first_note = sequence.entries[0].payload
        final_note = sequence.entries[-1].payload
        assert isinstance(first_note, Note)
        assert isinstance(final_note, Note)
        assert first_note.pitch_class in chord_tones
        assert final_note.pitch_class in chord_tones

    def test_scale_walk_out_of_scale_steps_are_chromatic_and_direction_changes_only_in_scale(self):
        sequence = Random(seed=12).sequence(
            16,
            algorithm="scale_walk",
            scale="C major",
            chord="F#",
            duration_weights={1: 1.0},
            direction_change_probability=1.0,
            run_step_probability=0.0,
        )

        scale_pitch_classes = tuple(note.pitch_class for note in Scale("C", ScaleType.MAJOR).notes)
        scale_set = set(scale_pitch_classes)
        scale_index_by_pitch_class = {
            pitch_class: index for index, pitch_class in enumerate(scale_pitch_classes)
        }
        chord_tones = {note.pitch_class for note in Chord.from_string("F#").notes}

        pitch_classes = [entry.payload.pitch_class for entry in sequence.entries]
        assert pitch_classes[0] in chord_tones
        assert pitch_classes[-1] in chord_tones

        directions: list[int] = []
        for index in range(len(pitch_classes) - 1):
            current_pitch_class = pitch_classes[index]
            next_pitch_class = pitch_classes[index + 1]

            if current_pitch_class in scale_set:
                scale_index = scale_index_by_pitch_class[current_pitch_class]
                upward = {
                    scale_pitch_classes[(scale_index + 1) % len(scale_pitch_classes)],
                    scale_pitch_classes[(scale_index + 2) % len(scale_pitch_classes)],
                }
                downward = {
                    scale_pitch_classes[(scale_index - 1) % len(scale_pitch_classes)],
                    scale_pitch_classes[(scale_index - 2) % len(scale_pitch_classes)],
                }
                delta = (next_pitch_class - current_pitch_class) % 12
                assert next_pitch_class in upward | downward or delta in {1, 11}
                if next_pitch_class in upward or delta == 1:
                    step_direction = 1
                else:
                    step_direction = -1
            else:
                delta = (next_pitch_class - current_pitch_class) % 12
                assert delta in {1, 11}
                step_direction = 1 if delta == 1 else -1

            directions.append(step_direction)

        for index in range(1, len(directions)):
            if directions[index] != directions[index - 1]:
                # Direction flips are only allowed when the move originated in-scale.
                assert pitch_classes[index] in scale_set

    def test_chord_anchor_walk_starts_and_ends_on_chord_tones(self):
        sequence = Random(seed=13).sequence(
            8,
            algorithm="chord_anchor_walk",
            scale="C major",
            chord="Am",
        )

        chord_tones = {note.pitch_class for note in Chord.from_string("Am").notes}
        first = sequence.entries[0].payload
        last = sequence.entries[-1].payload
        assert isinstance(first, Note)
        assert isinstance(last, Note)
        assert first.pitch_class in chord_tones
        assert last.pitch_class in chord_tones

    def test_pure_random_can_extend_prior_pitched_entry_via_tie(self):
        sequence = Random(seed=1).sequence(
            4,
            algorithm=PureRandomSequenceAlgorithm(),
            scale="C major",
            event_type_weights={"note": 1.0, "tie": 100.0, "rest": 0.0, "chord": 0.0},
            duration_weights={1: 1.0},
        )

        # At least one tie should collapse events into fewer entries than durations.
        assert len(sequence.entries) < 4
        assert _consumed_beats(sequence) == Fraction(4, 1)

    def test_pure_random_note_events_include_octave_for_octaveless_scale(self):
        sequence = Random(seed=17).sequence(
            4,
            algorithm="pure_random",
            scale=Scale("C", ScaleType.MAJOR),
            event_type_weights={"note": 1.0, "tie": 0.0, "rest": 0.0, "chord": 0.0},
            duration_weights={1: 1.0},
        )

        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.octave == 4

    def test_scale_walk_assigns_octave_when_scale_context_has_none(self):
        sequence = Random(seed=9).sequence(
            8,
            algorithm="scale_walk",
            scale=Scale("E", ScaleType.NATURAL_MINOR),
        )

        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.octave is not None

    def test_chord_anchor_assigns_octave_when_scale_context_has_none(self):
        sequence = Random(seed=13).sequence(
            8,
            algorithm="chord_anchor_walk",
            scale=Scale("C", ScaleType.MAJOR),
            chord="Am",
        )

        for entry in sequence.entries:
            assert isinstance(entry.payload, Note)
            assert entry.payload.octave is not None
