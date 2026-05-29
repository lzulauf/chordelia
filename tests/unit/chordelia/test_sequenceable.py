"""Tests for the Sequenceable protocol, adapter registry, and score normalization."""

import pytest

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.rhythm import Duration
from chordelia.score import Score, ScoreEvent, ScoreEventContext
from chordelia.sequenceable import (
    Sequenceable,
    _clear_sequenceable_adapters,
    _register_sequenceable_adapter,
    _score_events_for,
)


@pytest.fixture(autouse=True)
def clear_adapter_registry_between_tests():
    """Keep adapter registry isolated between test cases."""
    _clear_sequenceable_adapters()
    yield
    _clear_sequenceable_adapters()


class TestSequenceableProtocol:
    """Runtime protocol checks for canonical sequenceable implementers."""

    def test_note_is_runtime_sequenceable(self):
        """Note exposes the required score_events_for_context protocol surface."""
        assert isinstance(Note("C4"), Sequenceable)

    def test_chord_is_runtime_sequenceable(self):
        """Chord exposes the required score_events_for_context protocol surface."""
        assert isinstance(Chord.from_string("C4"), Sequenceable)


class TestAdapterRegistry:
    """Adapter registration and fallback behavior."""

    class ExternalTone:
        """Example non-sequenceable value for adapter tests."""

        def __init__(self, midi_number: int):
            self.midi_number = midi_number

    class ExternalToneVariant(ExternalTone):
        """Subclass used to verify MRO-based adapter lookup."""

    def test_score_events_for_uses_registered_adapter(self):
        """_score_events_for should route unknown values through registered adapters."""

        def tone_adapter(value, context):
            return (
                ScoreEvent(
                    beat=context.start_offset,
                    duration=context.default_duration,
                    pitches=(value.midi_number,),
                    velocity=context.velocity,
                    channel=context.channel,
                    voice=context.voice,
                ),
            )

        _register_sequenceable_adapter(self.ExternalTone, tone_adapter)

        context = ScoreEventContext(start_offset=1, default_duration=2, velocity=88)
        events = _score_events_for(self.ExternalTone(72), context)

        assert len(events) == 1
        assert events[0].beat == Duration.from_beats(1)
        assert events[0].duration == Duration.from_beats(2)
        assert events[0].pitches == (72,)
        assert events[0].velocity == 88

    def test_adapter_lookup_uses_base_class_registration(self):
        """Adapter lookup should resolve through MRO for subclass values."""

        def tone_adapter(value, _context):
            return (ScoreEvent(beat=0, duration=1, pitches=(value.midi_number,)),)

        _register_sequenceable_adapter(self.ExternalTone, tone_adapter)

        events = _score_events_for(self.ExternalToneVariant(69), ScoreEventContext())

        assert events[0].pitches == (69,)

    def test_score_events_for_raises_for_unsupported_values(self):
        """Unsupported values should fail with actionable guidance."""
        with pytest.raises(TypeError, match="_register_sequenceable_adapter"):
            _score_events_for(object(), ScoreEventContext())


class TestScoreFromSequenceable:
    """Score normalization behavior from sequenceable and adapted values."""

    class ExternalPattern:
        """Non-sequenceable test value converted via adapter."""

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
        """Score should normalize event ordering regardless of adapter output order."""

        def pattern_adapter(_value, _context):
            return (
                ScoreEvent(beat=2, duration=1, pitches=(64,), channel=1),
                ScoreEvent(beat=1, duration=1, pitches=(60,), channel=1),
                ScoreEvent(beat=1, duration=1, pitches=(67,), channel=0),
            )

        _register_sequenceable_adapter(self.ExternalPattern, pattern_adapter)

        score = Score.from_sequenceable(self.ExternalPattern())

        assert [event.pitches for event in score.events] == [(67,), (60,), (64,)]
        assert [event.beat for event in score.events] == [
            Duration.from_beats(1),
            Duration.from_beats(1),
            Duration.from_beats(2),
        ]
