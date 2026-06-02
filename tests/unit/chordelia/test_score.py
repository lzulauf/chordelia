"""Tests for the score module models and normalization behavior."""

import pytest

from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.score import Score, ScoreEvent, ScoreEventContext, ScoreMetadata, score_from_sequenceable
from chordelia.sequenceable import _clear_sequenceable_adapters, _register_sequenceable_adapter


@pytest.fixture(autouse=True)
def clear_adapter_registry_between_tests():
    """Keep private adapter registrations isolated to each test."""
    _clear_sequenceable_adapters()
    yield
    _clear_sequenceable_adapters()


class TestScoreEvent:
    """Validation and coercion behavior for ScoreEvent."""

    def test_score_event_coerces_durations_and_sequence_fields(self):
        """ScoreEvent should normalize timings to beat-based Duration values."""
        event = ScoreEvent(
            beat=0.5,
            duration=2,
            pitches=[60, 64],
            spelling=["C4", "E4"],
        )

        assert event.beat == Duration.from_beats(1, 2)
        assert event.duration == Duration.from_beats(2)
        assert event.pitches == (60, 64)
        assert event.spelling == ("C4", "E4")

    def test_score_event_rejects_note_fraction_durations(self):
        """ScoreEvent requires beat/time Duration modes, not note-fraction mode."""
        with pytest.raises(ValueError, match="Duration.from_beats"):
            ScoreEvent(beat=Duration("quarter"), duration=Duration.from_beats(1), pitches=(60,))

    @pytest.mark.parametrize(
        "kwargs, expected_message",
        [
            ({"beat": -1, "duration": 1, "pitches": (60,)}, "beat must be >= 0"),
            ({"beat": 0, "duration": 0, "pitches": (60,)}, "duration must be > 0"),
            ({"beat": 0, "duration": 1, "pitches": ()}, "pitches must be non-empty"),
            ({"beat": 0, "duration": 1, "pitches": (200,)}, "pitch values must be 0-127"),
            ({"beat": 0, "duration": 1, "pitches": ("C",)}, "pitch values must be integers"),
            ({"beat": 0, "duration": 1, "pitches": (60,), "velocity": 200}, "velocity must be 0-127"),
            ({"beat": 0, "duration": 1, "pitches": (60,), "channel": -1}, "channel must be >= 0"),
            ({"beat": 0, "duration": 1, "pitches": (60,), "voice": -1}, "voice must be >= 0"),
        ],
    )
    def test_score_event_validation_errors(self, kwargs, expected_message):
        """Invalid event values should raise clear ValueError messages."""
        with pytest.raises(ValueError, match=expected_message):
            ScoreEvent(**kwargs)


class TestScoreEventContext:
    """Validation and copy-constructor behavior for ScoreEventContext."""

    def test_context_coerces_duration_fields(self):
        """Context should normalize timing values to beat-based Duration."""
        context = ScoreEventContext(start_offset=0.25, default_duration=2)

        assert context.start_offset == Duration.from_beats(1, 4)
        assert context.default_duration == Duration.from_beats(2)

    def test_with_start_offset_returns_new_context(self):
        """with_start_offset should preserve immutability and return updated copy."""
        original = ScoreEventContext(
            start_offset=Duration.from_beats(0),
            default_duration=Duration.from_beats(1, 2),
        )

        updated = original.with_start_offset(Duration.from_beats(3, 2))

        assert original.start_offset == Duration.from_beats(0)
        assert updated.start_offset == Duration.from_beats(3, 2)
        assert updated.default_duration == original.default_duration
        assert updated is not original

    def test_context_rejects_note_fraction_durations(self):
        """Context requires beat/time Duration modes for offsets and defaults."""
        with pytest.raises(ValueError, match="Duration.from_beats"):
            ScoreEventContext(start_offset=Duration("quarter"))

    @pytest.mark.parametrize(
        "kwargs, expected_message",
        [
            ({"start_offset": -1}, "start_offset must be >= 0"),
            ({"default_duration": 0}, "default_duration must be > 0"),
            ({"tempo": 0}, "tempo must be > 0"),
            ({"time_signature": (4,)}, "time_signature must be"),
            ({"time_signature": (0, 4)}, "numerator must be > 0"),
            ({"time_signature": (4, 0)}, "denominator must be > 0"),
            ({"velocity": 128}, "velocity must be 0-127"),
            ({"channel": -1}, "channel must be >= 0"),
            ({"voice": -1}, "voice must be >= 0"),
        ],
    )
    def test_context_validation_errors(self, kwargs, expected_message):
        """Invalid context values should be rejected with explicit error messages."""
        with pytest.raises(ValueError, match=expected_message):
            ScoreEventContext(**kwargs)


class TestScoreMetadata:
    """Validation behavior for ScoreMetadata."""

    @pytest.mark.parametrize(
        "kwargs, expected_message",
        [
            ({"tempo": 0}, "tempo must be > 0"),
            ({"time_signature": (4,)}, "time_signature must be"),
            ({"time_signature": (0, 4)}, "numerator must be > 0"),
            ({"time_signature": (4, 0)}, "denominator must be > 0"),
            ({"ppq": 0}, "ppq must be > 0"),
        ],
    )
    def test_metadata_validation_errors(self, kwargs, expected_message):
        """Invalid metadata should raise ValueError."""
        with pytest.raises(ValueError, match=expected_message):
            ScoreMetadata(**kwargs)


class TestScore:
    """Score sorting and conversion behavior."""

    class External:
        """Simple adapted source type for conversion tests."""

    def test_score_sorts_with_full_deterministic_key(self):
        """Sorting should use beat, channel, voice, pitches, then duration."""
        events = (
            ScoreEvent(beat=1, duration=2, pitches=(62,), channel=1, voice=0),
            ScoreEvent(beat=1, duration=1, pitches=(64,), channel=0, voice=2),
            ScoreEvent(beat=1, duration=1, pitches=(65,), channel=0, voice=1),
            ScoreEvent(beat=0, duration=1, pitches=(60,), channel=5, voice=5),
        )

        score = Score(source="x", metadata=ScoreMetadata(), events=events)

        assert [event.pitches for event in score.events] == [(60,), (65,), (64,), (62,)]

    def test_score_len_and_iter_return_normalized_events(self):
        """Score should expose normalized event count and iteration."""
        events = (
            ScoreEvent(beat=2, duration=1, pitches=(64,)),
            ScoreEvent(beat=1, duration=1, pitches=(60,)),
        )

        score = Score(source="x", metadata=ScoreMetadata(), events=events)

        assert len(score) == 2
        assert [event.pitches for event in score] == [(60,), (64,)]

    def test_from_sequenceable_passes_context_and_builds_metadata(self):
        """Score.from_sequenceable should propagate conversion context and metadata values."""
        captured = {}

        def external_adapter(_value, context):
            captured["context"] = context
            return (
                ScoreEvent(
                    beat=context.start_offset,
                    duration=context.default_duration,
                    pitches=(72,),
                    velocity=context.velocity,
                    channel=context.channel,
                    voice=context.voice,
                ),
            )

        _register_sequenceable_adapter(self.External, external_adapter)

        score = Score.from_sequenceable(
            self.External(),
            tempo=88,
            time_signature=(6, 8),
            key_signature="G",
            ppq=960,
        )

        context = captured["context"]
        assert context.tempo == 88
        assert context.time_signature == (6, 8)
        assert context.key_signature == "G"
        assert context.start_offset == Duration.from_beats(0)
        assert context.default_duration == Duration.from_beats(1)

        assert score.metadata.tempo == 88
        assert score.metadata.time_signature == (6, 8)
        assert score.metadata.key_signature == "G"
        assert score.metadata.ppq == 960
        assert score.events[0].pitches == (72,)

    def test_score_rejects_mixed_timing_modes(self):
        """Scores must use a single timing mode across all events."""
        with pytest.raises(ValueError, match="same timing mode"):
            Score(
                source="x",
                metadata=ScoreMetadata(),
                events=(
                    ScoreEvent(beat=Duration.from_beats(0), duration=Duration.from_beats(1), pitches=(60,)),
                    ScoreEvent(
                        beat=Duration.from_seconds("0.5"),
                        duration=Duration.from_seconds("0.25"),
                        pitches=(64,),
                    ),
                ),
            )

    def test_from_sequenceable_raises_for_unsupported_source(self):
        """Unsupported values should raise TypeError via sequenceable conversion boundary."""
        with pytest.raises(TypeError, match="_register_sequenceable_adapter"):
            Score.from_sequenceable(object())

    def test_score_from_sequenceable_helper_delegates_to_classmethod(self):
        """Compatibility helper should delegate behavior to Score.from_sequenceable."""
        score = score_from_sequenceable(
            Note("C4"),
            tempo=92,
            time_signature=(5, 4),
            key_signature="C",
        )

        assert isinstance(score, Score)
        assert score.metadata.tempo == 92
        assert score.metadata.time_signature == (5, 4)
        assert score.metadata.key_signature == "C"
        assert score.metadata.ppq == 480
        assert score.events[0].pitches == (60,)
