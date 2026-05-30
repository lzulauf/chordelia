"""Tests for the score module models and normalization behavior."""

import pytest

from chordelia.degrees import Degree
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.scales import Scale
from chordelia.scale_context import reset_chordelia_context, with_chordelia_context
from chordelia.score import Score, ScoreEvent, ScoreEventContext, ScoreMetadata, score_from_sequenceable
from chordelia.sequenceable import (
    SequenceRender,
    _clear_sequenceable_adapters,
    _register_sequenceable_adapter,
)


@pytest.fixture(autouse=True)
def clear_adapter_registry_between_tests():
    """Keep private adapter registrations isolated to each test."""
    _clear_sequenceable_adapters()
    reset_chordelia_context()
    yield
    _clear_sequenceable_adapters()
    reset_chordelia_context()


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

    def test_with_tempo_returns_updated_copy(self):
        metadata = ScoreMetadata(tempo=120, time_signature=(4, 4), key_signature="C", ppq=480)

        updated = metadata.with_tempo(144)

        assert updated.tempo == 144
        assert updated.time_signature == (4, 4)
        assert updated.key_signature == "C"
        assert updated.ppq == 480
        assert updated.gate_width == 0.9
        assert updated.gate_offset == 0.0
        assert updated.retrigger_policy == "retrigger_all"
        assert metadata.tempo == 120
        assert updated is not metadata

    def test_with_allows_multiple_field_updates(self):
        metadata = ScoreMetadata(tempo=120, time_signature=(4, 4), key_signature="C", ppq=480)

        updated = metadata.with_(
            tempo=96,
            time_signature=(3, 4),
            key_signature="G",
            ppq=960,
            gate_width=0.75,
            gate_offset=0.1,
            retrigger_policy="retrigger_all",
        )

        assert updated.tempo == 96
        assert updated.time_signature == (3, 4)
        assert updated.key_signature == "G"
        assert updated.ppq == 960
        assert updated.gate_width == 0.75
        assert updated.gate_offset == 0.1
        assert updated.retrigger_policy == "retrigger_all"

    def test_with_without_changes_returns_same_instance(self):
        metadata = ScoreMetadata()

        updated = metadata.with_()

        assert updated is metadata

    @pytest.mark.parametrize(
        "kwargs, expected_message",
        [
            ({"tempo": 0}, "tempo must be > 0"),
            ({"time_signature": (4,)}, "time_signature must be"),
            ({"time_signature": (0, 4)}, "numerator must be > 0"),
            ({"time_signature": (4, 0)}, "denominator must be > 0"),
            ({"ppq": 0}, "ppq must be > 0"),
            ({"gate_width": -0.1}, "gate_width must be between 0.0 and 1.0"),
            ({"gate_offset": 1.1}, "gate_offset must be between 0.0 and 1.0"),
            ({"retrigger_policy": "bad"}, "retrigger_policy must be"),
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

    def test_score_duration_returns_timeline_end_for_beats(self):
        events = (
            ScoreEvent(beat=1, duration=2, pitches=(60,)),
            ScoreEvent(beat=4, duration=1, pitches=(64,)),
        )

        score = Score(source="x", metadata=ScoreMetadata(), events=events)

        assert score.duration == Duration.from_beats(5)

    def test_score_duration_returns_timeline_end_for_seconds(self):
        events = (
            ScoreEvent(
                beat=Duration.from_seconds("1.5"),
                duration=Duration.from_seconds("0.5"),
                pitches=(60,),
            ),
            ScoreEvent(
                beat=Duration.from_seconds("0.25"),
                duration=Duration.from_seconds("0.75"),
                pitches=(64,),
            ),
        )

        score = Score(source="x", metadata=ScoreMetadata(), events=events)

        assert score.duration == Duration.from_seconds("2.0")

    def test_score_duration_for_empty_score_is_zero_beats(self):
        score = Score(source="x", metadata=ScoreMetadata(), events=())

        assert score.duration == Duration.from_beats(0)

    def test_from_sequenceable_uses_context_default_note_duration(self):
        with with_chordelia_context(default_note_duration=Duration.from_beats(1, 2)):
            score = Score.from_sequenceable(Note("C4"))

        assert score.events[0].duration == Duration.from_beats(1, 2)

    def test_from_sequenceable_explicit_default_duration_overrides_context(self):
        with with_chordelia_context(default_note_duration=Duration.from_beats(1, 2)):
            score = Score.from_sequenceable(
                Note("C4"),
                default_duration=Duration.from_beats(3, 4),
            )

        assert score.events[0].duration == Duration.from_beats(3, 4)

    def test_with_tempo_updates_score_metadata_only(self):
        score = Score(
            source="x",
            metadata=ScoreMetadata(tempo=120, time_signature=(4, 4), key_signature="C", ppq=480),
            events=(ScoreEvent(beat=0, duration=1, pitches=(60,)),),
        )

        updated = score.with_tempo(140)

        assert updated.metadata.tempo == 140
        assert updated.metadata.time_signature == (4, 4)
        assert updated.metadata.key_signature == "C"
        assert updated.metadata.ppq == 480
        assert updated.metadata.gate_width == 0.9
        assert updated.metadata.gate_offset == 0.0
        assert updated.metadata.retrigger_policy == "retrigger_all"
        assert updated.source == score.source
        assert updated.events == score.events
        assert score.metadata.tempo == 120

    def test_with_supports_multiple_metadata_updates_in_one_call(self):
        score = Score(
            source="x",
            metadata=ScoreMetadata(tempo=120, time_signature=(4, 4), key_signature="C", ppq=480),
            events=(ScoreEvent(beat=0, duration=1, pitches=(60,)),),
        )

        updated = score.with_(
            tempo=90,
            time_signature=(3, 4),
            key_signature="Am",
            ppq=960,
            gate_width=0.8,
            gate_offset=0.15,
            retrigger_policy="retrigger_all",
        )

        assert updated.metadata.tempo == 90
        assert updated.metadata.time_signature == (3, 4)
        assert updated.metadata.key_signature == "Am"
        assert updated.metadata.ppq == 960
        assert updated.metadata.gate_width == 0.8
        assert updated.metadata.gate_offset == 0.15
        assert updated.metadata.retrigger_policy == "retrigger_all"

    def test_with_supports_source_events_and_metadata_override(self):
        score = Score(
            source="source-a",
            metadata=ScoreMetadata(tempo=120, time_signature=(4, 4), key_signature="C", ppq=480),
            events=(ScoreEvent(beat=1, duration=1, pitches=(64,)),),
        )
        replacement_metadata = ScoreMetadata(tempo=110, time_signature=(6, 8), key_signature="D", ppq=240)
        replacement_events = (ScoreEvent(beat=0, duration=1, pitches=(60,)),)

        updated = score.with_(
            source="source-b",
            metadata=replacement_metadata,
            events=replacement_events,
            tempo=132,
            key_signature="G",
            gate_offset=0.2,
        )

        assert updated.source == "source-b"
        assert updated.events == replacement_events
        assert updated.metadata.tempo == 132
        assert updated.metadata.time_signature == (6, 8)
        assert updated.metadata.key_signature == "G"
        assert updated.metadata.ppq == 240
        assert updated.metadata.gate_width == 0.9
        assert updated.metadata.gate_offset == 0.2
        assert updated.metadata.retrigger_policy == "retrigger_all"

    def test_with_rejects_non_metadata_override(self):
        score = Score(source="x", metadata=ScoreMetadata(), events=(ScoreEvent(beat=0, duration=1, pitches=(60,)),))

        with pytest.raises(TypeError, match="ScoreMetadata"):
            score.with_(metadata="bad")

    def test_from_sequenceable_passes_context_and_builds_metadata(self):
        """Score.from_sequenceable should propagate conversion context and metadata values."""
        captured = {}

        def external_adapter(_value, context):
            captured["context"] = context
            return SequenceRender(
                events=(
                    ScoreEvent(
                        beat=context.start_offset,
                        duration=context.default_duration,
                        pitches=(72,),
                        velocity=context.velocity,
                        channel=context.channel,
                        voice=context.voice,
                    ),
                ),
                consumed_duration=context.default_duration,
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
        assert score.metadata.gate_width == 0.9
        assert score.metadata.gate_offset == 0.0
        assert score.metadata.retrigger_policy == "retrigger_all"
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

    @pytest.mark.parametrize(
        "source",
        (
            Scale("C", "major"),
            Degree(1),
        ),
    )
    def test_from_sequenceable_rejects_non_sequenceable_theory_types(self, source):
        """Scale and Degree are theory helpers, not direct sequenceable score sources."""
        with pytest.raises(TypeError, match="not Sequenceable"):
            Score.from_sequenceable(source)

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
