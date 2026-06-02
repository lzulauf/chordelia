"""Focused tests for explicit parallel composition and immutable recomposition APIs."""

import pytest

from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.score import Score
from chordelia.sequences import ParallelSequence, Sequence


pytestmark = pytest.mark.usefixtures("reset_chordelia_context_state")


class TestParallelSequenceScheduling:
    """Parallel scheduling semantics and score integration behavior."""

    def test_zero_offsets_emit_simultaneous_events(self):
        lead = Sequence(((Note("C4"), 1),))
        bass = Sequence(((Note("E3"), 2),))

        parallel = ParallelSequence((lead, bass))
        score = Score.from_sequenceable(parallel)

        assert [event.beat for event in score.events] == [Duration.from_beats(0), Duration.from_beats(0)]
        assert [event.pitches for event in score.events] == [(52,), (60,)]
        assert score.duration == Duration.from_beats(2)

    def test_positive_offset_shifts_only_target_child(self):
        lead = Sequence(((Note("C4"), 1),))
        bass = Sequence(((Note("C3"), 1),))

        parallel = ParallelSequence(
            (
                ("lead", lead, 0),
                ("bass", bass, 2),
            )
        )
        score = Score.from_sequenceable(parallel)

        assert [event.pitches for event in score.events] == [(60,), (48,)]
        assert [event.beat for event in score.events] == [Duration.from_beats(0), Duration.from_beats(2)]

    def test_negative_child_offset_is_rejected(self):
        with pytest.raises(ValueError, match="offset must be >= 0"):
            ParallelSequence(((Sequence(((Note("C4"), 1),)), -1),))


class TestParallelSequenceRecomposition:
    """Name/path lookup and replacement behavior for immutable composition trees."""

    def test_rejects_duplicate_sibling_names(self):
        child = Sequence(((Note("C4"), 1),))

        with pytest.raises(ValueError, match="Duplicate child name"):
            ParallelSequence((("voice", child, 0), ("voice", child, 1)))

    def test_get_child_by_name_and_replace_preserve_immutability(self):
        lead = Sequence(((Note("C4"), 1),))
        bass = Sequence(((Note("C3"), 1),))
        parallel = ParallelSequence((("lead", lead, 0), ("bass", bass, 0)))

        looked_up = parallel.get_child_by_name("lead")
        updated = parallel.replace_child_by_name("lead", Sequence(((Note("E4"), 1),)))

        assert looked_up is lead
        assert parallel.get_child_by_name("lead") is lead
        assert updated.get_child_by_name("lead") != lead

        updated_score = Score.from_sequenceable(updated)
        assert [event.pitches for event in updated_score.events] == [(48,), (64,)]

    def test_get_and_replace_by_path_for_nested_parallel_children(self):
        lead = Sequence(((Note("C4"), 1),))
        bass = Sequence(((Note("C3"), 1),))
        section = ParallelSequence((("lead", lead, 0), ("bass", bass, 0)), name="section")
        arrangement = ParallelSequence((("section", section, 0),), name="song")

        assert arrangement.get_child_by_path("section.lead") is lead

        updated = arrangement.replace_child_by_path(
            "section.lead",
            Sequence(((Note("D4"), 1),)),
        )

        original_score = Score.from_sequenceable(arrangement)
        updated_score = Score.from_sequenceable(updated)

        assert [event.pitches for event in original_score.events] == [(48,), (60,)]
        assert [event.pitches for event in updated_score.events] == [(48,), (62,)]


class TestScoreFromParallelSequences:
    """Explicit parallel score constructor behavior."""

    def test_from_parallel_sequences_builds_score(self):
        lead = Sequence(((Note("C4"), 1),))
        bass = Sequence(((Note("C3"), 2),))

        score = Score.from_parallel_sequences((lead, bass), tempo=90, time_signature=(3, 4))

        assert score.metadata.tempo == 90
        assert score.metadata.time_signature == (3, 4)
        assert [event.pitches for event in score.events] == [(48,), (60,)]
        assert score.duration == Duration.from_beats(2)

    def test_from_parallel_sequences_rejects_empty_sources(self):
        with pytest.raises(ValueError, match="at least one"):
            Score.from_parallel_sequences(())
