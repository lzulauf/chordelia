"""MIDI interface playback utilities and canonical live transport API."""

from contextlib import contextmanager
import threading
import time
from typing import Dict, Iterable, List, Optional, Sequence, Set

from chordelia.chords import Chord
from chordelia.notes import Note
from chordelia.rhythm import Duration, Tempo
from chordelia.score import Score, ScoreEvent


try:
    import mido

    _MIDI_AVAILABLE = True
except ImportError:
    _MIDI_AVAILABLE = False
    mido = None


class MidiPlayback:
    """Canonical live MIDI interface transport for interactive and score playback."""

    def __init__(
        self,
        output_name: Optional[str] = None,
        channel: int = 0,
        base_octave: int = 4,
        default_velocity: int = 64,
    ):
        if not _MIDI_AVAILABLE:
            raise ImportError("MIDI playback requires 'mido' package. Install with: pip install mido")

        self._validate_channel(channel)
        if not 0 <= default_velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")

        self.channel = channel
        self.base_octave = base_octave
        self.default_velocity = default_velocity

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._output_port = None
        self._stop_timers: List[threading.Timer] = []
        self._active_thread: Optional[threading.Thread] = None
        self._current_notes: Set[tuple[int, int]] = set()

        self._setup_midi_output(output_name)

    def __enter__(self) -> "MidiPlayback":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.stop()

    @contextmanager
    def session(self):
        """Return a context manager for the existing instance lifecycle."""
        try:
            yield self
        finally:
            self.stop()

    def _setup_midi_output(self, output_name: Optional[str]) -> None:
        available_outputs = list(mido.get_output_names())

        if output_name is not None:
            if output_name not in available_outputs:
                available = ", ".join(available_outputs) if available_outputs else "<none>"
                raise ValueError(
                    f"MIDI output port {output_name!r} not found. Available outputs: {available}"
                )
            selected_output = output_name
        else:
            if not available_outputs:
                raise RuntimeError("No MIDI output ports are available")
            selected_output = available_outputs[0]

        self._output_port = mido.open_output(selected_output)

    @staticmethod
    def _validate_channel(channel: int) -> None:
        if not 0 <= channel <= 15:
            raise ValueError("MIDI channel must be between 0 and 15")

    def _coerce_note_to_midi(self, note: Note) -> int:
        if note.octave is None:
            note = note.with_octave(self.base_octave)
        return note.midi_number

    def _send_note_on(self, channel: int, midi_note: int, velocity: int) -> None:
        if self._output_port:
            msg = mido.Message('note_on', channel=channel, note=midi_note, velocity=velocity)
            self._output_port.send(msg)

    def _send_note_off(self, channel: int, midi_note: int) -> None:
        if self._output_port:
            msg = mido.Message('note_off', channel=channel, note=midi_note, velocity=0)
            self._output_port.send(msg)

    def _stop_all_notes(self) -> None:
        for channel, midi_note in tuple(self._current_notes):
            self._send_note_off(channel, midi_note)
        self._current_notes.clear()

    def update_chord(
        self,
        chord: Optional[Chord],
        *,
        channel: Optional[int] = None,
        velocity: Optional[int] = None,
    ) -> None:
        """Update currently sounding chord by sending only delta note events."""
        active_channel = self.channel if channel is None else channel
        self._validate_channel(active_channel)
        active_velocity = self.default_velocity if velocity is None else velocity

        if not 0 <= active_velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")

        with self._lock:
            if chord is None:
                self._stop_all_notes()
                return

            new_notes = {(active_channel, self._coerce_note_to_midi(note)) for note in chord.notes}

            notes_to_stop = self._current_notes - new_notes
            notes_to_start = new_notes - self._current_notes

            for stop_channel, midi_note in notes_to_stop:
                self._send_note_off(stop_channel, midi_note)

            for start_channel, midi_note in notes_to_start:
                self._send_note_on(start_channel, midi_note, active_velocity)

            self._current_notes = new_notes

    def play_chord_with_duration(
        self,
        chord: Chord,
        duration: Duration,
        tempo: Tempo = Tempo(120),
        *,
        channel: Optional[int] = None,
        velocity: Optional[int] = None,
    ) -> None:
        self.update_chord(chord, channel=channel, velocity=velocity)

        from chordelia.rhythm import TimeSignature

        time_sig = TimeSignature(4, 4)
        duration_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0
        stop_timer = threading.Timer(duration_seconds, lambda: self.update_chord(None))
        self._stop_timers.append(stop_timer)
        stop_timer.start()

    def play_note(
        self,
        note: Note,
        velocity: Optional[int] = None,
        duration: Optional[Duration] = None,
        tempo: Tempo = Tempo(120),
        *,
        channel: Optional[int] = None,
    ) -> None:
        active_channel = self.channel if channel is None else channel
        self._validate_channel(active_channel)

        active_velocity = self.default_velocity if velocity is None else velocity
        if not 0 <= active_velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")

        midi_note = self._coerce_note_to_midi(note)
        stop_timer: Optional[threading.Timer] = None

        with self._lock:
            self._send_note_on(active_channel, midi_note, active_velocity)
            self._current_notes.add((active_channel, midi_note))

            if duration is not None:
                from chordelia.rhythm import TimeSignature

                time_sig = TimeSignature(4, 4)
                duration_seconds = tempo.duration_to_ms(duration, time_sig) / 1000.0

                def _timed_note_off() -> None:
                    with self._lock:
                        self._send_note_off(active_channel, midi_note)
                        self._current_notes.discard((active_channel, midi_note))

                stop_timer = threading.Timer(duration_seconds, _timed_note_off)
                self._stop_timers.append(stop_timer)

        # Start timers outside the playback lock to avoid deadlocks when tests
        # use immediate/synchronous timer doubles.
        if stop_timer is not None:
            stop_timer.start()

    def _duration_to_seconds(self, duration: Duration, tempo_bpm: int) -> float:
        if duration.mode == "seconds":
            return float(duration.as_seconds())
        beats = float(duration.as_beats())
        return beats * 60.0 / float(tempo_bpm)

    @staticmethod
    def _validate_gate_value(value: float, *, field_name: str) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")

    @staticmethod
    def _validate_retrigger_policy(policy: str) -> None:
        if policy not in {"delta", "retrigger_all"}:
            raise ValueError(
                "retrigger_policy must be 'delta' or 'retrigger_all', "
                f"got {policy!r}"
            )

    def _effective_event_window(
        self,
        score: Score,
        event: ScoreEvent,
        *,
        default_gate_width: float,
        default_gate_offset: float,
    ) -> tuple[float, float, int, int]:
        """Compute start/end playback window for one event under gate settings."""
        channel = event.channel
        event_start = self._duration_to_seconds(event.beat, score.metadata.tempo)
        event_duration = self._duration_to_seconds(event.duration, score.metadata.tempo)
        event_end = event_start + event_duration

        gate_width = default_gate_width if event.gate_width is None else event.gate_width
        gate_offset = default_gate_offset if event.gate_offset is None else event.gate_offset
        self._validate_gate_value(gate_width, field_name="gate_width")
        self._validate_gate_value(gate_offset, field_name="gate_offset")

        sounding_start = event_start + (event_duration * gate_offset)
        sounding_end = min(event_end, sounding_start + (event_duration * gate_width))
        return sounding_start, sounding_end, channel, event.velocity

    def _build_score_schedule(
        self,
        score: Score,
        *,
        velocity_scale: float,
        channel_override: Optional[int],
        gate_width: Optional[float],
        gate_offset: Optional[float],
        retrigger_policy: Optional[str],
    ) -> List[tuple[float, int, int, int, int, bool]]:
        if velocity_scale <= 0:
            raise ValueError("velocity_scale must be > 0")

        if channel_override is not None:
            self._validate_channel(channel_override)

        effective_gate_width = score.metadata.gate_width if gate_width is None else gate_width
        effective_gate_offset = score.metadata.gate_offset if gate_offset is None else gate_offset
        effective_retrigger_policy = (
            score.metadata.retrigger_policy
            if retrigger_policy is None
            else retrigger_policy
        )

        self._validate_gate_value(effective_gate_width, field_name="gate_width")
        self._validate_gate_value(effective_gate_offset, field_name="gate_offset")
        self._validate_retrigger_policy(effective_retrigger_policy)

        schedule: list[tuple[float, int, int, int, int, bool]] = []

        if effective_retrigger_policy == "retrigger_all":
            for event in score.events:
                start_s, end_s, event_channel, event_velocity = self._effective_event_window(
                    score,
                    event,
                    default_gate_width=effective_gate_width,
                    default_gate_offset=effective_gate_offset,
                )

                if end_s <= start_s:
                    continue

                channel = channel_override if channel_override is not None else event_channel
                velocity = max(0, min(127, int(round(event_velocity * velocity_scale))))

                for pitch in event.pitches:
                    # order: note_off first at equal timestamp.
                    schedule.append((start_s, 1, channel, pitch, velocity, True))
                    schedule.append((end_s, 0, channel, pitch, 0, False))

            schedule.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
            return schedule

        # Delta mode: preserve currently sounding notes and only retrigger changed notes.
        active: dict[tuple[int, int], float] = {}

        def flush_finished(before_time: float) -> None:
            for key, off_time in tuple(active.items()):
                if off_time < before_time:
                    channel, pitch = key
                    schedule.append((off_time, 0, channel, pitch, 0, False))
                    del active[key]

        for event in score.events:
            start_s, end_s, event_channel, event_velocity = self._effective_event_window(
                score,
                event,
                default_gate_width=effective_gate_width,
                default_gate_offset=effective_gate_offset,
            )

            if end_s <= start_s:
                continue

            flush_finished(start_s)

            channel = channel_override if channel_override is not None else event_channel
            velocity = max(0, min(127, int(round(event_velocity * velocity_scale))))

            for pitch in event.pitches:
                key = (channel, pitch)
                current_off = active.get(key)
                if current_off is not None and current_off >= start_s:
                    if end_s > current_off:
                        active[key] = end_s
                    continue

                schedule.append((start_s, 1, channel, pitch, velocity, True))
                active[key] = end_s

        for key, off_time in active.items():
            channel, pitch = key
            schedule.append((off_time, 0, channel, pitch, 0, False))

        schedule.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        return schedule

    def _sleep_until(self, target_time: float) -> None:
        while not self._stop_event.is_set():
            remaining = target_time - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(remaining, 0.01))

    def _play_schedule(self, schedule: Sequence[tuple[float, int, int, int, int, bool]]) -> None:
        started_at = time.monotonic()
        try:
            for event_time, _order, channel, pitch, velocity, is_on in schedule:
                if self._stop_event.is_set():
                    break
                self._sleep_until(started_at + event_time)
                with self._lock:
                    if is_on:
                        self._send_note_on(channel, pitch, velocity)
                        self._current_notes.add((channel, pitch))
                    else:
                        self._send_note_off(channel, pitch)
                        self._current_notes.discard((channel, pitch))
        finally:
            with self._lock:
                self._stop_all_notes()

    def play_score(
        self,
        score: Score,
        *,
        blocking: bool = True,
        velocity_scale: float = 1.0,
        channel_override: Optional[int] = None,
        gate_width: Optional[float] = None,
        gate_offset: Optional[float] = None,
        retrigger_policy: Optional[str] = None,
    ) -> None:
        schedule = self._build_score_schedule(
            score,
            velocity_scale=velocity_scale,
            channel_override=channel_override,
            gate_width=gate_width,
            gate_offset=gate_offset,
            retrigger_policy=retrigger_policy,
        )

        self._stop_event.clear()
        if blocking:
            self._play_schedule(schedule)
            return

        if self._active_thread is not None and self._active_thread.is_alive():
            raise RuntimeError("A non-blocking playback session is already running")

        self._active_thread = threading.Thread(target=self._play_schedule, args=(schedule,), daemon=True)
        self._active_thread.start()

    def set_velocity(self, velocity: int) -> None:
        if not 0 <= velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")
        self.default_velocity = velocity

    def set_channel(self, channel: int) -> None:
        self._validate_channel(channel)
        with self._lock:
            self._stop_all_notes()
            self.channel = channel

    def stop(self) -> None:
        self._stop_event.set()

        with self._lock:
            for timer in self._stop_timers:
                timer.cancel()
            self._stop_timers.clear()
            self._stop_all_notes()

            if self._output_port is not None:
                self._output_port.close()
                self._output_port = None

    @property
    def current_notes(self) -> Set[tuple[int, int]]:
        with self._lock:
            return self._current_notes.copy()

    @property
    def is_connected(self) -> bool:
        return self._output_port is not None and not self._output_port.closed

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass


def play_chord(
    chord: Chord,
    tempo: Tempo = Tempo(120),
    duration: Optional[Duration] = None,
    channel: int = 0,
    velocity: int = 64,
    output_name: Optional[str] = None,
) -> None:
    """Play a chord via MIDI with simultaneous note onsets."""
    if not _MIDI_AVAILABLE:
        raise ImportError("MIDI playback requires 'mido' package. Install with: pip install mido")

    from chordelia.rhythm import TimeSignature, whole_note

    hold_duration = whole_note() if duration is None else duration
    with MidiPlayback(output_name=output_name, channel=channel, default_velocity=velocity) as playback:
        playback.play_chord_with_duration(chord, hold_duration, tempo, channel=channel, velocity=velocity)
        time_sig = TimeSignature(4, 4)
        duration_seconds = tempo.duration_to_ms(hold_duration, time_sig) / 1000.0
        time.sleep(duration_seconds)


def play_melody(
    notes: Iterable[Note],
    tempo: Tempo = Tempo(120),
    channel: int = 0,
    default_velocity: int = 64,
    output_name: Optional[str] = None,
) -> None:
    """Play a sequence of notes as a melody using default quarter-note durations."""
    if not _MIDI_AVAILABLE:
        raise ImportError("MIDI playback requires 'mido' package. Install with: pip install mido")

    from chordelia.rhythm import TimeSignature

    step_duration = Duration.from_beats(1, None)
    with MidiPlayback(output_name=output_name, channel=channel, default_velocity=default_velocity) as playback:
        for note in notes:
            playback.play_note(
                note,
                velocity=default_velocity,
                duration=step_duration,
                tempo=tempo,
                channel=channel,
            )

            time_sig = TimeSignature(4, 4)
            duration_seconds = tempo.duration_to_ms(step_duration, time_sig) / 1000.0
            time.sleep(duration_seconds)


def get_midi_ports() -> Dict[str, List[str]]:
    """Get available MIDI input and output port names."""
    if not _MIDI_AVAILABLE:
        return {'input': [], 'output': [], 'error': 'mido not installed'}

    try:
        return {
            'input': mido.get_input_names(),
            'output': mido.get_output_names(),
        }
    except Exception as e:
        return {'input': [], 'output': [], 'error': str(e)}


def is_midi_available() -> bool:
    """Check if MIDI functionality is available."""
    return _MIDI_AVAILABLE
