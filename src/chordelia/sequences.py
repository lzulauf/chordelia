"""First-class sequence composition models built on the Sequenceable boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Iterable, TypeAlias

from chordelia.chords import Chord
from chordelia.intervals import IntervalLike, coerce_chromatic_semitones
from chordelia.notes import Note
from chordelia.rhythm import Duration, TimelineLike, coerce_timeline_duration
from chordelia.scale_context import coerce_scale_context_value
from chordelia.score import ScoreEvent, ScoreEventContext
from chordelia.sequenceable import NotesLike, SequenceRender, Sequenceable, _sequence_render_for

if TYPE_CHECKING:
    from chordelia.scales import Scale


DurationLike: TypeAlias = TimelineLike


def _coerce_duration(value: DurationLike, *, field_name: str) -> Duration:
    """Coerce values into beat/time Duration values for deterministic scheduling."""
    return coerce_timeline_duration(value, field_name=field_name)


def _is_negative(value: Duration) -> bool:
    """Check whether a duration value is negative in its own mode."""
    if value.mode == "seconds":
        return value.as_seconds() < 0
    return value.as_beats() < 0


def _is_non_positive(value: Duration) -> bool:
    """Check whether a duration value is <= 0 in its own mode."""
    if value.mode == "seconds":
        return value.as_seconds() <= 0
    return value.as_beats() <= 0


def _coerce_payload(value: Any) -> Any:
    """Normalize ergonomic payload forms into canonical sequenceable payloads."""
    if isinstance(value, Sequenceable):
        return value
    if isinstance(value, (str, bytes)):
        return value
    if isinstance(value, Iterable):
        layers: list[Sequenceable] = []
        for item in value:
            layer = _coerce_layer(item)
            if layer is None:
                return value
            layers.append(layer)

        if not layers:
            return Rest()
        # Keep ergonomic note-list support as one chord payload.
        if all(isinstance(layer, Note) for layer in layers):
            return Chord.from_notes(tuple(layers))
        if len(layers) == 1:
            return layers[0]
        return _SimultaneousPayload(tuple(layers))
    return value


def _coerce_layer(value: Any) -> Sequenceable | None:
    """Coerce a simultaneous-layer item while preserving object boundaries."""
    if isinstance(value, Sequenceable):
        return value
    if isinstance(value, str):
        return Note.from_string(value)
    if isinstance(value, NotesLike):
        notes = value.to_notes()
        if not notes:
            return Rest()
        if len(notes) == 1:
            return notes[0]
        return Chord.from_notes(notes)
    return None


@dataclass(frozen=True, slots=True)
class _SimultaneousPayload:
    """Private sequenceable wrapper for simultaneous layer emission."""

    layers: tuple[Sequenceable, ...]

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        events: list[ScoreEvent] = []
        for layer in self.layers:
            events.extend(_sequence_render_for(layer, context).events)
        return SequenceRender(events=tuple(events), consumed_duration=context.default_duration)

    def transpose(self, interval: IntervalLike | int) -> "_SimultaneousPayload":
        """Return a transposed copy while preserving simultaneous boundaries."""
        return _SimultaneousPayload(
            tuple(_transpose_payload(layer, interval) for layer in self.layers)
        )

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "_SimultaneousPayload":
        """Return a diatonically shifted copy while preserving simultaneous boundaries."""
        return _SimultaneousPayload(
            tuple(_shift_payload(layer, steps, scale=scale) for layer in self.layers)
        )


@dataclass(frozen=True, slots=True)
class Rest:
    """Explicit silent payload marker for sequence timelines."""

    def to_notes(self) -> tuple[Note, ...]:
        """Represent this rest as an empty note collection."""
        return ()

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Rests are sequenceable and emit no score events while consuming span."""
        return SequenceRender(events=(), consumed_duration=context.default_duration)

    def transpose(self, interval: IntervalLike | int) -> "Rest":
        """Transpose is a no-op for rests but accepted for recursive sequence transforms."""
        coerce_chromatic_semitones(interval)
        return self

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "Rest":
        """Shift is a no-op for rests but accepted for recursive sequence transforms."""
        if not isinstance(steps, int) or isinstance(steps, bool):
            raise TypeError(f"steps must be an int, got {type(steps).__name__}")
        if scale is not None:
            coerce_scale_context_value(scale)
        return self


@dataclass(frozen=True, slots=True)
class SequenceEntry:
    """One scheduled payload plus timing metadata inside a Sequence."""

    payload: Any
    duration: DurationLike = Duration.from_beats(1, None)
    offset: DurationLike | None = None
    name: str | None = None

    @classmethod
    def coerce(cls, value: 'SequenceEntryLike') -> 'SequenceEntry':
        """Coerce tuple and model forms into SequenceEntry."""
        if isinstance(value, cls):
            return value
        if isinstance(value, tuple):
            if len(value) == 2:
                payload, duration = value
                return cls(payload=payload, duration=duration)
            if len(value) == 3:
                payload, duration, offset = value
                return cls(payload=payload, duration=duration, offset=offset)
            if len(value) == 4:
                payload, duration, offset, name = value
                return cls(payload=payload, duration=duration, offset=offset, name=name)
            raise ValueError(
                "SequenceEntry tuple form must be (payload, duration) "
                "or (payload, duration, offset[, name])."
            )
        raise ValueError(
            "Sequence entry must be SequenceEntry or tuple form "
            "(payload, duration[, offset[, name]])."
        )

    def __post_init__(self) -> None:
        payload = _coerce_payload(self.payload)
        duration = _coerce_duration(self.duration, field_name="duration")
        offset = (
            _coerce_duration(self.offset, field_name="offset")
            if self.offset is not None
            else None
        )

        if _is_non_positive(duration):
            raise ValueError(f"duration must be > 0, got {duration}")
        if offset is not None and _is_negative(offset):
            raise ValueError(f"offset must be >= 0, got {offset}")
        if offset is not None and offset.mode != duration.mode:
            raise ValueError(
                "offset and duration must use the same timing mode "
                f"(got {offset.mode!r} and {duration.mode!r})"
            )
        if self.name is not None:
            _validate_child_name(self.name)

        object.__setattr__(self, "payload", payload)
        object.__setattr__(self, "duration", duration)
        object.__setattr__(self, "offset", offset)


@dataclass(frozen=True, slots=True)
class Sequence:
    """Immutable ordered collection of sequence entries."""

    entries: tuple[SequenceEntry, ...]
    name: str | None = None

    def __init__(self, entries: Iterable['SequenceInputLike'] = (), *, name: str | None = None):
        normalized_entries: list[SequenceEntry] = []
        for entry_value in entries:
            if isinstance(entry_value, Sequenceable):
                normalized_entries.append(SequenceEntry(payload=entry_value))
                continue
            normalized_entries.append(SequenceEntry.coerce(entry_value))

        if name is not None:
            _validate_child_name(name)
        _validate_unique_child_names(tuple(entry.name for entry in normalized_entries))

        object.__setattr__(self, "entries", tuple(normalized_entries))
        object.__setattr__(self, "name", name)

    def appended(self, *entries: 'SequenceInputLike') -> "Sequence":
        """Return a new sequence with entries appended in order."""
        return Sequence((*self.entries, *entries), name=self.name)

    def transpose(self, interval: IntervalLike | int) -> "Sequence":
        """Return a recursively transposed sequence with unchanged timing metadata."""
        semitone_steps = coerce_chromatic_semitones(interval)
        transposed_entries = tuple(
            SequenceEntry(
                payload=_transpose_payload(entry.payload, semitone_steps),
                duration=entry.duration,
                offset=entry.offset,
                name=entry.name,
            )
            for entry in self.entries
        )
        return Sequence(transposed_entries, name=self.name)

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "Sequence":
        """Return a recursively shifted sequence with unchanged timing metadata."""
        if not isinstance(steps, int) or isinstance(steps, bool):
            raise TypeError(f"steps must be an int, got {type(steps).__name__}")

        scale_obj = coerce_scale_context_value(scale) if scale is not None else None
        shifted_entries = tuple(
            SequenceEntry(
                payload=_shift_payload(entry.payload, steps, scale=scale_obj),
                duration=entry.duration,
                offset=entry.offset,
                name=entry.name,
            )
            for entry in self.entries
        )
        return Sequence(shifted_entries, name=self.name)

    def get_child_by_name(self, name: str, *, recursive: bool = False) -> Any:
        """Return a named direct child payload, optionally searching nested children."""
        _validate_child_name(name)

        for entry in self.entries:
            if entry.name == name:
                return entry.payload

        if recursive:
            for entry in self.entries:
                getter = getattr(entry.payload, "get_child_by_name", None)
                if getter is None:
                    continue
                try:
                    return getter(name, recursive=True)
                except KeyError:
                    continue

        raise KeyError(f"No child named {name!r}.")

    def replace_child_by_name(
        self,
        name: str,
        new_child: Any,
        *,
        recursive: bool = False,
    ) -> "Sequence":
        """Return a new sequence with a named child payload replaced."""
        _validate_child_name(name)

        replaced_entries: list[SequenceEntry] = []
        replaced = False
        for entry in self.entries:
            if not replaced and entry.name == name:
                replaced_entries.append(
                    SequenceEntry(
                        payload=new_child,
                        duration=entry.duration,
                        offset=entry.offset,
                        name=entry.name,
                    )
                )
                replaced = True
                continue
            replaced_entries.append(entry)

        if replaced:
            return Sequence(replaced_entries, name=self.name)

        if recursive:
            for idx, entry in enumerate(self.entries):
                replacer = getattr(entry.payload, "replace_child_by_name", None)
                if replacer is None:
                    continue
                try:
                    updated_payload = replacer(name, new_child, recursive=True)
                except KeyError:
                    continue
                updated_entries = list(self.entries)
                updated_entries[idx] = SequenceEntry(
                    payload=updated_payload,
                    duration=entry.duration,
                    offset=entry.offset,
                    name=entry.name,
                )
                return Sequence(updated_entries, name=self.name)

        raise KeyError(f"No child named {name!r}.")

    def get_child_by_path(self, path: str) -> Any:
        """Return a nested child payload addressed by dot-separated names."""
        return _get_child_by_path(self, path)

    def replace_child_by_path(self, path: str, new_child: Any) -> "Sequence":
        """Return a new sequence with one nested path target replaced."""
        return _replace_child_by_path(self, path, new_child)

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Render sequence entries into score events using deterministic span scheduling."""
        events: list[ScoreEvent] = []
        cursor = context.start_offset

        for entry in self.entries:
            if entry.duration.mode != cursor.mode:
                raise ValueError(
                    "SequenceEntry duration mode must match context timing mode "
                    f"(got {entry.duration.mode!r} and {cursor.mode!r})"
                )

            if entry.offset is None:
                start = cursor
            else:
                if entry.offset.mode != cursor.mode:
                    raise ValueError(
                        "SequenceEntry offset mode must match context timing mode "
                        f"(got {entry.offset.mode!r} and {cursor.mode!r})"
                    )
                start = context.start_offset + entry.offset

            child_context = replace(
                context,
                start_offset=start,
                default_duration=entry.duration,
            )
            child_render = _sequence_render_for(entry.payload, child_context)
            if child_render.consumed_duration.mode != cursor.mode:
                raise ValueError(
                    "Rendered child consumed_duration mode must match context timing mode "
                    f"(got {child_render.consumed_duration.mode!r} and {cursor.mode!r})"
                )
            events.extend(child_render.events)

            end = start + child_render.consumed_duration
            if entry.offset is None:
                cursor = end
            elif end > cursor:
                cursor = end

        return SequenceRender(
            events=tuple(events),
            consumed_duration=cursor - context.start_offset,
        )

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def sheet_music_should_render_tempo_metadata(self) -> bool:
        """Signal SheetMusic to render tempo metadata for sequence-backed sources."""
        return True


@dataclass(frozen=True, slots=True)
class ParallelChild:
    """One child source scheduled inside a ParallelSequence container."""

    source: Sequenceable
    offset: DurationLike = Duration.from_beats(0, None)
    name: str | None = None

    @classmethod
    def coerce(cls, value: 'ParallelChildInputLike') -> 'ParallelChild':
        """Coerce tuple and model forms into ParallelChild."""
        if isinstance(value, cls):
            return value
        if isinstance(value, Sequenceable):
            return cls(source=value)
        if isinstance(value, tuple):
            if len(value) == 2:
                source, offset = value
                return cls(source=source, offset=offset)
            if len(value) == 3:
                name, source, offset = value
                return cls(source=source, offset=offset, name=name)
            raise ValueError(
                "ParallelChild tuple form must be (source, offset) "
                "or (name, source, offset)."
            )
        raise TypeError(
            "Parallel child must be Sequenceable, ParallelChild, or tuple form "
            "(source, offset) / (name, source, offset)."
        )

    def __post_init__(self) -> None:
        if not isinstance(self.source, Sequenceable):
            raise TypeError(
                "Parallel child source must be Sequenceable, "
                f"got {type(self.source).__name__}."
            )

        offset = _coerce_duration(self.offset, field_name="offset")
        if _is_negative(offset):
            raise ValueError(f"offset must be >= 0, got {offset}")
        if self.name is not None:
            _validate_child_name(self.name)

        object.__setattr__(self, "offset", offset)


@dataclass(frozen=True, slots=True)
class ParallelSequence:
    """Immutable simultaneous composition container with optional child names."""

    children: tuple[ParallelChild, ...]
    name: str | None = None

    def __init__(
        self,
        children: Iterable['ParallelChildInputLike'] = (),
        *,
        name: str | None = None,
    ):
        normalized_children_list: list[ParallelChild] = []
        for idx, child in enumerate(children):
            try:
                normalized_children_list.append(ParallelChild.coerce(child))
            except (TypeError, ValueError) as exc:
                raise type(exc)(f"Invalid parallel child at index {idx}: {exc}") from exc
        normalized_children = tuple(normalized_children_list)

        if name is not None:
            _validate_child_name(name)
        _validate_unique_child_names(tuple(child.name for child in normalized_children))

        object.__setattr__(self, "children", normalized_children)
        object.__setattr__(self, "name", name)

    def transpose(self, interval: IntervalLike | int) -> "ParallelSequence":
        """Return a recursively transposed parallel container."""
        semitone_steps = coerce_chromatic_semitones(interval)
        return ParallelSequence(
            tuple(
                ParallelChild(
                    source=_transpose_payload(child.source, semitone_steps),
                    offset=child.offset,
                    name=child.name,
                )
                for child in self.children
            ),
            name=self.name,
        )

    def shift(self, steps: int, *, scale: 'Scale | str | None' = None) -> "ParallelSequence":
        """Return a recursively shifted parallel container."""
        if not isinstance(steps, int) or isinstance(steps, bool):
            raise TypeError(f"steps must be an int, got {type(steps).__name__}")

        scale_obj = coerce_scale_context_value(scale) if scale is not None else None
        return ParallelSequence(
            tuple(
                ParallelChild(
                    source=_shift_payload(child.source, steps, scale=scale_obj),
                    offset=child.offset,
                    name=child.name,
                )
                for child in self.children
            ),
            name=self.name,
        )

    def render_for_context(self, context: ScoreEventContext) -> SequenceRender:
        """Render all children from the same container start plus each child offset."""
        if not self.children:
            return SequenceRender(events=(), consumed_duration=context.default_duration)

        events: list[ScoreEvent] = []
        span_end = context.start_offset

        for idx, child in enumerate(self.children):
            if child.offset.mode != context.start_offset.mode:
                raise ValueError(
                    f"Parallel child at index {idx} offset mode must match context timing mode "
                    f"(got {child.offset.mode!r} and {context.start_offset.mode!r})"
                )

            child_start = context.start_offset + child.offset
            child_context = replace(context, start_offset=child_start)
            child_render = _sequence_render_for(child.source, child_context)

            if child_render.consumed_duration.mode != context.start_offset.mode:
                raise ValueError(
                    f"Rendered child at index {idx} consumed_duration mode must match context timing mode "
                    f"(got {child_render.consumed_duration.mode!r} and {context.start_offset.mode!r})"
                )

            events.extend(child_render.events)
            child_end = child_start + child_render.consumed_duration
            if child_end > span_end:
                span_end = child_end

        return SequenceRender(
            events=tuple(events),
            consumed_duration=span_end - context.start_offset,
        )

    def get_child_by_name(self, name: str, *, recursive: bool = False) -> Sequenceable:
        """Return a named direct child source, optionally searching nested children."""
        _validate_child_name(name)

        for child in self.children:
            if child.name == name:
                return child.source

        if recursive:
            for child in self.children:
                getter = getattr(child.source, "get_child_by_name", None)
                if getter is None:
                    continue
                try:
                    return getter(name, recursive=True)
                except KeyError:
                    continue

        raise KeyError(f"No child named {name!r}.")

    def replace_child_by_name(
        self,
        name: str,
        new_child: Sequenceable,
        *,
        recursive: bool = False,
    ) -> "ParallelSequence":
        """Return a new parallel container with one named child replaced."""
        _validate_child_name(name)

        replaced_children: list[ParallelChild] = []
        replaced = False
        for child in self.children:
            if not replaced and child.name == name:
                replaced_children.append(
                    ParallelChild(source=new_child, offset=child.offset, name=child.name)
                )
                replaced = True
                continue
            replaced_children.append(child)

        if replaced:
            return ParallelSequence(replaced_children, name=self.name)

        if recursive:
            for idx, child in enumerate(self.children):
                replacer = getattr(child.source, "replace_child_by_name", None)
                if replacer is None:
                    continue
                try:
                    updated_source = replacer(name, new_child, recursive=True)
                except KeyError:
                    continue
                updated_children = list(self.children)
                updated_children[idx] = ParallelChild(
                    source=updated_source,
                    offset=child.offset,
                    name=child.name,
                )
                return ParallelSequence(updated_children, name=self.name)

        raise KeyError(f"No child named {name!r}.")

    def get_child_by_path(self, path: str) -> Sequenceable:
        """Return a nested child source addressed by dot-separated names."""
        return _get_child_by_path(self, path)

    def replace_child_by_path(self, path: str, new_child: Sequenceable) -> "ParallelSequence":
        """Return a new parallel container with one nested path target replaced."""
        return _replace_child_by_path(self, path, new_child)

    def __len__(self) -> int:
        return len(self.children)

    def __iter__(self):
        return iter(self.children)

    def sheet_music_should_render_tempo_metadata(self) -> bool:
        """Signal SheetMusic to render tempo metadata for sequence-backed sources."""
        return True


SequenceEntryLike: TypeAlias = (
    SequenceEntry
    | tuple[Any, DurationLike]
    | tuple[Any, DurationLike, DurationLike | None]
    | tuple[Any, DurationLike, DurationLike | None, str]
)

SequenceInputLike: TypeAlias = SequenceEntryLike | Sequenceable
ParallelChildInputLike: TypeAlias = (
    ParallelChild
    | Sequenceable
    | tuple[Sequenceable, DurationLike]
    | tuple[str, Sequenceable, DurationLike]
)


def _validate_child_name(name: str) -> None:
    """Validate child names used for immutable lookup and replacement paths."""
    if not isinstance(name, str):
        raise TypeError(f"name must be a string, got {type(name).__name__}")
    if not name.strip():
        raise ValueError("name must be a non-empty string")
    if "." in name:
        raise ValueError("name cannot contain '.' because dot is reserved for path traversal")


def _validate_unique_child_names(names: tuple[str | None, ...]) -> None:
    """Enforce sibling-level name uniqueness for deterministic path addressing."""
    seen: set[str] = set()
    for name in names:
        if name is None:
            continue
        if name in seen:
            raise ValueError(f"Duplicate child name {name!r} among siblings.")
        seen.add(name)


def _split_child_path(path: str) -> tuple[str, ...]:
    """Split and validate dot-separated child path input."""
    if not isinstance(path, str):
        raise TypeError(f"path must be a string, got {type(path).__name__}")

    parts = tuple(segment.strip() for segment in path.split("."))
    if not parts or any(not segment for segment in parts):
        raise ValueError("path must be a non-empty dot-separated child name path")
    return parts


def _get_child_by_path(root: Any, path: str) -> Any:
    """Walk a dot-separated path through get_child_by_name boundaries."""
    parts = _split_child_path(path)
    current = root
    resolved = ""

    for part in parts:
        getter = getattr(current, "get_child_by_name", None)
        if getter is None:
            _raise_unresolved_path(part, resolved)
        try:
            current = getter(part)
        except KeyError as exc:
            _raise_unresolved_path(part, resolved, exc)
        resolved = f"{resolved}.{part}" if resolved else part

    return current


def _replace_child_by_path(root: Any, path: str, new_child: Any) -> Any:
    """Replace one dot-separated path target through immutable replacement helpers."""
    parts = _split_child_path(path)
    return _replace_child_by_path_parts(root, parts, new_child, resolved="")


def _replace_child_by_path_parts(
    current: Any,
    parts: tuple[str, ...],
    new_child: Any,
    *,
    resolved: str,
) -> Any:
    """Recursive path replacement helper for immutable composition containers."""
    head = parts[0]
    replacer = getattr(current, "replace_child_by_name", None)
    if replacer is None:
        _raise_unresolved_path(head, resolved)

    if len(parts) == 1:
        try:
            return replacer(head, new_child)
        except KeyError as exc:
            _raise_unresolved_path(head, resolved, exc)

    getter = getattr(current, "get_child_by_name", None)
    if getter is None:
        _raise_unresolved_path(head, resolved)
    try:
        child = getter(head)
    except KeyError as exc:
        _raise_unresolved_path(head, resolved, exc)

    next_resolved = f"{resolved}.{head}" if resolved else head
    replaced_child = _replace_child_by_path_parts(
        child,
        parts[1:],
        new_child,
        resolved=next_resolved,
    )
    try:
        return replacer(head, replaced_child)
    except KeyError as exc:
        _raise_unresolved_path(head, resolved, exc)


def _raise_unresolved_path(segment: str, resolved: str, exc: Exception | None = None) -> None:
    """Raise a consistent KeyError for missing path segments."""
    prefix = resolved if resolved else "<root>"
    message = f"Path segment {segment!r} could not be resolved from {prefix}."
    if exc is not None:
        raise KeyError(message) from exc
    raise KeyError(message)


def _transpose_payload(payload: Any, interval: IntervalLike | int) -> Any:
    """Transpose one payload value or raise an actionable capability error."""
    if isinstance(payload, Sequenceable):
        return payload.transpose(interval)

    raise ValueError(
        "Sequence.transpose requires Sequenceable payloads that implement transpose(interval). "
        f"Unsupported payload type: {type(payload).__name__}."
    )


def _shift_payload(payload: Any, steps: int, *, scale: 'Scale | str | None' = None) -> Any:
    """Diatonically shift one payload value or raise an actionable capability error."""
    if isinstance(payload, Sequenceable):
        shift_method = getattr(payload, "shift", None)
        if shift_method is None:
            raise ValueError(
                "Sequence.shift requires Sequenceable payloads that implement shift(steps). "
                f"Unsupported payload type: {type(payload).__name__}."
            )
        if scale is None:
            return shift_method(steps)
        return shift_method(steps, scale=scale)

    raise ValueError(
        "Sequence.shift requires Sequenceable payloads that implement shift(steps). "
        f"Unsupported payload type: {type(payload).__name__}."
    )
