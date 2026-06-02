"""Pure-random sequence generation algorithm."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, ClassVar, TYPE_CHECKING

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.randomization import (
    SequenceRandomizationAlgorithm,
    _choose_duration_for_remaining,
    _coerce_duration_weight_map,
    _coerce_event_type_weights,
    _coerce_probability,
    _resolve_optional_chord,
    _resolve_optional_scale,
    _sample_chord_for_context,
    _sample_note_for_context,
)
from chordelia.scales import Scale
from chordelia.sequences import Rest, Sequence

if TYPE_CHECKING:
    from chordelia.randomization import Random


class PureRandomSequenceAlgorithm(SequenceRandomizationAlgorithm):
    """Random selector over notes, rests, chords, and continuation actions.

    Accepted generate kwargs:
    - duration_weights: WeightInput[TimelineLike]
      Relative weights for candidate event durations in beats.
      Defaults to quarter/half/whole/multi-beat mix.
    - event_type_weights: WeightInput[str]
      Relative weights for action names: "note", "rest", "chord", "tie".
      "tie" extends the most recent pitched entry duration.
      Defaults to note-heavy behavior.
    - pitch_change_probability: float in [0, 1]
      Probability of selecting a new note when action is "note" and a previous
      note exists; otherwise the prior note is reused.
      Default is 0.65.
    """

    name: ClassVar[str] = "pure_random"
    default_selection_weight: ClassVar[float] = 10.0

    def generate(
        self,
        *,
        rng: "Random",
        beat_length: Fraction,
        scale: Scale | str | None = None,
        chord: Chord | str | None = None,
        **params: Any,
    ) -> Sequence:
        """Generate a sequence using random action and duration sampling."""
        scale_obj = _resolve_optional_scale(scale)
        chord_obj = _resolve_optional_chord(chord)

        duration_weights = _coerce_duration_weight_map(params.get("duration_weights"))
        event_type_weights = _coerce_event_type_weights(params.get("event_type_weights"))
        pitch_change_probability = _coerce_probability(
            params.get("pitch_change_probability", 0.65),
            label="pitch_change_probability",
        )

        entries: list[list[Any]] = []
        last_pitched_index: int | None = None
        last_note: Note | None = None

        remaining = beat_length
        while remaining > 0:
            duration = _choose_duration_for_remaining(
                rng,
                remaining,
                duration_weights,
            )

            selection_weights = dict(event_type_weights)
            if last_pitched_index is None:
                selection_weights["tie"] = 0.0

            action = rng.weighted_choice_map(selection_weights)
            if action == "tie" and last_pitched_index is not None:
                entries[last_pitched_index][1] += duration
                remaining -= duration
                continue

            if action == "rest":
                payload: Any = Rest()
            elif action == "chord":
                payload = _sample_chord_for_context(
                    rng,
                    scale=scale_obj,
                    chord=chord_obj,
                )
            else:
                if last_note is not None and rng.engine.random() > pitch_change_probability:
                    payload = last_note
                else:
                    payload = _sample_note_for_context(
                        rng,
                        scale=scale_obj,
                        chord=chord_obj,
                    )

            entries.append([payload, duration])
            if not isinstance(payload, Rest):
                last_pitched_index = len(entries) - 1
                if isinstance(payload, Note):
                    last_note = payload

            remaining -= duration

        return Sequence((payload, duration) for payload, duration in entries)
