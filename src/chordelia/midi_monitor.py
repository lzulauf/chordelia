"""Real-time MIDI monitor session primitives for runtime and notebook workflows."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
import threading
import time
from typing import Callable, Sequence

from chordelia.midi_playback import MidiMessageEvent, MidiPlayback


@lru_cache(maxsize=1)
def _load_ipython_display_module():
    """Load IPython.display lazily for notebook-only rendering paths."""
    try:
        import IPython.display as display_module
    except ModuleNotFoundError:
        return None
    return display_module


@dataclass(frozen=True, slots=True)
class MidiMonitorEvent:
    """Immutable monitor event captured from MidiPlayback outbound messages."""

    event_index: int
    monotonic_time_seconds: float
    wall_time_iso: str | None
    elapsed_seconds_from_session_start: float | None
    elapsed_beats_from_session_start: float | None
    direction: str
    port_name: str | None
    source_method: str
    message_type: str
    channel: int
    note: int
    velocity: int
    raw_message_repr: str

    def __repr__(self) -> str:
        return (
            f"MidiMonitorEvent(index={self.event_index} type={self.message_type} "
            f"ch={self.channel} note={self.note} vel={self.velocity} "
            f"elapsed_s={self.elapsed_seconds_from_session_start} "
            f"elapsed_beats={self.elapsed_beats_from_session_start})"
        )

    def __str__(self) -> str:
        return (
            f"<midi {self.message_type:<8} "
            f"ch={self.channel:>2} "
            f"note={self.note:>3} "
            f"vel={self.velocity:>3}>"
        )


class MidiMonitorDisplayHandle:
    """Handle returned by display_live for stopping live refresh updates."""

    def __init__(
        self,
        *,
        mode: str,
        stop_callback: Callable[[], None],
        display_id: str | None = None,
    ):
        self.mode = mode
        self.display_id = display_id
        self._stop_callback = stop_callback

    def stop(self) -> None:
        self._stop_callback()


class MidiMonitorSession:
    """Thread-safe monitor session that records outbound playback events."""

    def __init__(
        self,
        playback: MidiPlayback | None = None,
        *,
        max_events: int = 5000,
        include_message_types: Sequence[str] | None = None,
        tempo_bpm: float | None = None,
        log_file: str | Path | None = None,
        include_wall_time: bool = True,
        include_elapsed_seconds: bool = True,
        include_elapsed_beats: bool = False,
    ):
        if max_events < 1:
            raise ValueError("max_events must be >= 1")

        self._playback = playback
        self._max_events = int(max_events)
        self._include_message_types = (
            tuple(message_type.lower().strip() for message_type in include_message_types)
            if include_message_types is not None
            else None
        )
        self._log_file = None if log_file is None else Path(log_file)
        self._include_wall_time = bool(include_wall_time)
        self._include_elapsed_seconds = bool(include_elapsed_seconds)
        self._include_elapsed_beats = bool(include_elapsed_beats)

        self._lock = threading.Lock()
        self._tempo_bpm: float | None = None
        self.set_tempo_bpm(tempo_bpm)

        self._events: deque[MidiMonitorEvent] = deque(maxlen=self._max_events)
        self._listener_id: int | None = None
        self._start_monotonic_seconds: float = 0.0
        self._event_index = 0
        self._running = False
        self._display_refresh_controls: list[tuple[threading.Event, threading.Thread]] = []

    def _validate_log_file(self) -> None:
        if self._log_file is None:
            return

        if self._log_file.exists() and self._log_file.is_dir():
            raise ValueError(f"log_file points to a directory: {self._log_file}")

        try:
            if self._log_file.parent and not self._log_file.parent.exists():
                self._log_file.parent.mkdir(parents=True, exist_ok=True)
            with self._log_file.open("a", encoding="utf-8"):
                pass
        except OSError as exc:
            raise RuntimeError(f"Unable to open log file '{self._log_file}': {exc}") from exc

    def _append_log_row(self, event: MidiMonitorEvent) -> None:
        if self._log_file is None:
            return

        row = {
            "event_index": event.event_index,
            "monotonic_time_seconds": event.monotonic_time_seconds,
            "direction": event.direction,
            "port_name": event.port_name,
            "source_method": event.source_method,
            "message_type": event.message_type,
            "channel": event.channel,
            "note": event.note,
            "velocity": event.velocity,
            "raw_message_repr": event.raw_message_repr,
        }
        if self._include_wall_time:
            row["wall_time_iso"] = event.wall_time_iso
        if self._include_elapsed_seconds:
            row["elapsed_seconds_from_session_start"] = event.elapsed_seconds_from_session_start
        if self._include_elapsed_beats:
            row["elapsed_beats_from_session_start"] = event.elapsed_beats_from_session_start

        serialized = json.dumps(row, sort_keys=True)
        try:
            with self._log_file.open("a", encoding="utf-8") as log_handle:
                log_handle.write(serialized)
                log_handle.write("\n")
        except OSError as exc:
            raise RuntimeError(f"Unable to write monitor event to '{self._log_file}': {exc}") from exc

    def __enter__(self) -> "MidiMonitorSession":
        return self.start()

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.stop()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    @property
    def events(self) -> tuple[MidiMonitorEvent, ...]:
        """Read-only alias for all captured events."""
        return self.snapshot()

    def start(self, playback: MidiPlayback | None = None) -> "MidiMonitorSession":
        with self._lock:
            if self._running:
                raise ValueError("Monitor session is already running")
            if playback is not None:
                self._playback = playback
            if self._playback is None:
                raise ValueError("A MidiPlayback instance is required to start monitoring")

            self._validate_log_file()

            self._start_monotonic_seconds = time.monotonic()
            self._event_index = 0
            self._running = True

        listener_id = self._playback.add_message_listener(self._handle_playback_event)

        with self._lock:
            self._listener_id = listener_id

        return self

    def stop(self) -> None:
        playback: MidiPlayback | None = None
        listener_id: int | None = None

        with self._lock:
            if not self._running:
                return
            self._running = False
            playback = self._playback
            listener_id = self._listener_id
            self._listener_id = None

        if playback is not None and listener_id is not None:
            playback.remove_message_listener(listener_id)

        self._stop_all_display_refreshes()

    def _stop_all_display_refreshes(self) -> None:
        with self._lock:
            refresh_controls = list(self._display_refresh_controls)
            self._display_refresh_controls.clear()

        for stop_event, refresh_thread in refresh_controls:
            stop_event.set()
            if refresh_thread.is_alive():
                refresh_thread.join(timeout=0.1)

    @staticmethod
    def _render_events_text(events: Sequence[MidiMonitorEvent]) -> str:
        if not events:
            return "No MIDI monitor events yet."

        lines = [str(event) for event in events]
        return "\n".join(lines)

    def _stop_display_refresh(
        self,
        stop_event: threading.Event,
        refresh_thread: threading.Thread,
    ) -> None:
        stop_event.set()
        if refresh_thread.is_alive():
            refresh_thread.join(timeout=0.1)

        with self._lock:
            try:
                self._display_refresh_controls.remove((stop_event, refresh_thread))
            except ValueError:
                pass

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._event_index = 0

    def snapshot(self, limit: int | None = None) -> tuple[MidiMonitorEvent, ...]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be >= 0")

        with self._lock:
            events = tuple(self._events)

        if limit is None:
            return events
        if limit == 0:
            return tuple()
        return events[-limit:]

    def to_rows(self, limit: int | None = None) -> list[dict[str, object]]:
        return [asdict(event) for event in self.snapshot(limit=limit)]

    def set_tempo_bpm(self, tempo_bpm: float | None) -> None:
        if tempo_bpm is not None and tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be > 0")

        with self._lock:
            self._tempo_bpm = None if tempo_bpm is None else float(tempo_bpm)

    def display_live(self, *, refresh_hz: float = 8.0, max_rows: int = 30):
        if refresh_hz <= 0:
            raise ValueError("refresh_hz must be > 0")
        if max_rows < 1:
            raise ValueError("max_rows must be >= 1")

        def fallback_handle() -> MidiMonitorDisplayHandle:
            return MidiMonitorDisplayHandle(mode="text", stop_callback=lambda: None)

        display_module = _load_ipython_display_module()
        if display_module is None:
            return fallback_handle()

        display_fn = getattr(display_module, "display", None)
        update_display_fn = getattr(display_module, "update_display", None)
        markdown_cls = getattr(display_module, "Markdown", None)
        if display_fn is None or update_display_fn is None:
            return fallback_handle()

        refresh_seconds = 1.0 / float(refresh_hz)
        stop_event = threading.Event()
        display_id = f"chordelia-midi-monitor-{id(self)}-{time.time_ns()}"

        def render_payload() -> object:
            events = self.snapshot(limit=max_rows)
            snapshot_text = self._render_events_text(events)
            if markdown_cls is not None:
                return markdown_cls(f"```text\n{snapshot_text}\n```")
            return snapshot_text

        try:
            display_fn(render_payload(), display_id=display_id)
        except Exception:
            return fallback_handle()

        def refresh_loop() -> None:
            while not stop_event.is_set():
                try:
                    update_display_fn(render_payload(), display_id=display_id)
                except Exception:
                    stop_event.set()
                    return
                stop_event.wait(refresh_seconds)

        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()

        with self._lock:
            self._display_refresh_controls.append((stop_event, refresh_thread))

        return MidiMonitorDisplayHandle(
            mode="notebook",
            stop_callback=lambda: self._stop_display_refresh(stop_event, refresh_thread),
            display_id=display_id,
        )

    def _handle_playback_event(self, event: MidiMessageEvent) -> None:
        message_type = str(event.get("message_type", "other")).lower()
        include_message_types = self._include_message_types
        if include_message_types is not None and message_type not in include_message_types:
            return

        monotonic_time_seconds = float(event.get("monotonic_time_seconds", time.monotonic()))
        direction = str(event.get("direction", "outbound"))
        source_method = str(event.get("source_method", "unknown"))
        port_name_raw = event.get("port_name")
        port_name = None if port_name_raw is None else str(port_name_raw)
        channel = int(event.get("channel", 0))
        note = int(event.get("note", 0))
        velocity = int(event.get("velocity", 0))
        raw_message_repr = str(event.get("raw_message_repr", ""))
        wall_time_iso = (
            datetime.now(timezone.utc).isoformat()
            if self._include_wall_time
            else None
        )

        logged_event: MidiMonitorEvent | None = None
        with self._lock:
            if not self._running:
                return

            self._event_index += 1
            elapsed_seconds = (
                max(0.0, monotonic_time_seconds - self._start_monotonic_seconds)
                if self._include_elapsed_seconds or self._include_elapsed_beats
                else None
            )
            elapsed_beats = (
                None
                if not self._include_elapsed_beats or self._tempo_bpm is None or elapsed_seconds is None
                else elapsed_seconds * self._tempo_bpm / 60.0
            )

            logged_event = MidiMonitorEvent(
                event_index=self._event_index,
                monotonic_time_seconds=monotonic_time_seconds,
                wall_time_iso=wall_time_iso,
                elapsed_seconds_from_session_start=(
                    elapsed_seconds if self._include_elapsed_seconds else None
                ),
                elapsed_beats_from_session_start=elapsed_beats,
                direction=direction,
                port_name=port_name,
                source_method=source_method,
                message_type=message_type,
                channel=channel,
                note=note,
                velocity=velocity,
                raw_message_repr=raw_message_repr,
            )
            self._events.append(logged_event)

        if logged_event is not None:
            self._append_log_row(logged_event)

