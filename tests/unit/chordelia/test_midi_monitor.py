"""Tests for MidiMonitorSession and monitor session helpers."""

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from chordelia.notes import C, D, E
from chordelia.rhythm import Duration


@pytest.fixture
def mock_midi():
    """Fixture providing mocked MIDI module and output port."""
    with patch("chordelia.midi_playback.mido") as mock_mido, patch(
        "chordelia.midi_playback._MIDI_AVAILABLE", True
    ):
        mock_port = Mock()
        mock_port.closed = False
        mock_mido.get_output_names.return_value = ["Test MIDI Port"]
        mock_mido.open_output.return_value = mock_port
        mock_mido.Message = Mock(side_effect=lambda msg_type, **kwargs: {"type": msg_type, **kwargs})
        yield {"mido": mock_mido, "port": mock_port}


class TestMidiMonitorSession:
    def test_start_requires_playback(self):
        from chordelia.midi_monitor import MidiMonitorSession

        session = MidiMonitorSession()
        with pytest.raises(ValueError, match="MidiPlayback"):
            session.start()

    def test_start_twice_raises(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback)
        session.start()

        with pytest.raises(ValueError, match="already running"):
            session.start()

        session.stop()
        playback.stop()

    def test_monitor_captures_events_then_stops(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback)
        session.start()

        playback.play_note(C.with_octave(4), duration=None)
        events = session.snapshot()

        assert len(events) == 1
        assert events[0].message_type == "note_on"
        assert events[0].source_method == "play_note"
        assert events[0].channel == 0
        assert events[0].note == 60
        assert events[0].direction == "outbound"

        session.stop()
        before_count = len(session.snapshot())
        playback.play_note(D.with_octave(4), duration=None)
        assert len(session.snapshot()) == before_count

        playback.stop()

    def test_clear_and_snapshot_limit(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback)
        session.start()

        playback.play_note(C.with_octave(4), duration=None)
        playback.play_note(D.with_octave(4), duration=None)
        playback.play_note(E.with_octave(4), duration=None)

        limited = session.snapshot(limit=2)
        assert len(limited) == 2
        assert [event.note for event in limited] == [62, 64]

        session.clear()
        assert session.snapshot() == tuple()

        session.stop()
        playback.stop()

    def test_max_events_discards_oldest(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback, max_events=2)
        session.start()

        playback.play_note(C.with_octave(4), duration=None)
        playback.play_note(D.with_octave(4), duration=None)
        playback.play_note(E.with_octave(4), duration=None)

        events = session.snapshot()
        assert len(events) == 2
        assert [event.event_index for event in events] == [2, 3]
        assert [event.note for event in events] == [62, 64]

        session.stop()
        playback.stop()

    def test_include_message_types_filter(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        class ImmediateTimer:
            def __init__(self, _seconds, callback):
                self._callback = callback

            def start(self):
                self._callback()

            def cancel(self):
                return None

        with patch("chordelia.midi_playback.threading.Timer", ImmediateTimer):
            playback = MidiPlayback()
            session = MidiMonitorSession(playback=playback, include_message_types=("note_off",))
            session.start()

            playback.play_note(C.with_octave(4), duration=Duration.from_beats(1, None))

            events = session.snapshot()
            assert len(events) == 1
            assert events[0].message_type == "note_off"

            session.stop()
            playback.stop()

    def test_elapsed_beats_with_tempo(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(
            playback=playback,
            tempo_bpm=120,
            include_elapsed_beats=True,
        )
        session.start()

        playback.play_note(C.with_octave(4), duration=None)
        event = session.snapshot()[-1]

        assert event.elapsed_beats_from_session_start is not None
        assert event.elapsed_beats_from_session_start >= 0.0

        session.stop()
        playback.stop()

    def test_elapsed_beats_without_tempo_emits_none(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(
            playback=playback,
            include_elapsed_beats=True,
        )
        session.start()

        playback.play_note(C.with_octave(4), duration=None)
        event = session.snapshot()[-1]

        assert event.elapsed_beats_from_session_start is None

        session.stop()
        playback.stop()

    def test_invalid_validation_inputs(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession

        with pytest.raises(ValueError, match="max_events"):
            MidiMonitorSession(max_events=0)

        with pytest.raises(ValueError, match="tempo_bpm"):
            MidiMonitorSession(tempo_bpm=0)

        session = MidiMonitorSession()
        with pytest.raises(ValueError, match="limit"):
            session.snapshot(limit=-1)


class TestMidiMonitorEventFormatting:
    def test_event_str_uses_padded_columns_for_alignment(self):
        from chordelia.midi_monitor import MidiMonitorEvent

        event = MidiMonitorEvent(
            event_index=7,
            monotonic_time_seconds=10.5,
            wall_time_iso=None,
            elapsed_seconds_from_session_start=0.25,
            elapsed_beats_from_session_start=0.5,
            direction="outbound",
            port_name="Test MIDI Port",
            source_method="play_note",
            message_type="note_on",
            channel=2,
            note=72,
            velocity=96,
            raw_message_repr="Message('note_on', channel=2, note=72, velocity=96)",
        )

        assert str(event) == "<midi note_on  ch= 2 note= 72 vel= 96>"

    def test_event_str_keeps_column_widths_for_small_and_large_values(self):
        from chordelia.midi_monitor import MidiMonitorEvent

        small = MidiMonitorEvent(
            event_index=1,
            monotonic_time_seconds=1.0,
            wall_time_iso=None,
            elapsed_seconds_from_session_start=None,
            elapsed_beats_from_session_start=None,
            direction="outbound",
            port_name=None,
            source_method="play_note",
            message_type="note_on",
            channel=0,
            note=7,
            velocity=8,
            raw_message_repr="Message('note_on', channel=0, note=7, velocity=8)",
        )
        large = MidiMonitorEvent(
            event_index=2,
            monotonic_time_seconds=2.0,
            wall_time_iso=None,
            elapsed_seconds_from_session_start=None,
            elapsed_beats_from_session_start=None,
            direction="outbound",
            port_name=None,
            source_method="play_note",
            message_type="note_off",
            channel=15,
            note=127,
            velocity=127,
            raw_message_repr="Message('note_off', channel=15, note=127, velocity=127)",
        )

        small_text = str(small)
        large_text = str(large)

        assert small_text == "<midi note_on  ch= 0 note=  7 vel=  8>"
        assert large_text == "<midi note_off ch=15 note=127 vel=127>"

    def test_event_repr_includes_key_fields(self):
        from chordelia.midi_monitor import MidiMonitorEvent

        event = MidiMonitorEvent(
            event_index=12,
            monotonic_time_seconds=99.0,
            wall_time_iso="2026-06-05T00:00:00+00:00",
            elapsed_seconds_from_session_start=1.25,
            elapsed_beats_from_session_start=2.5,
            direction="outbound",
            port_name=None,
            source_method="play_score",
            message_type="note_off",
            channel=0,
            note=60,
            velocity=0,
            raw_message_repr="Message('note_off', channel=0, note=60, velocity=0)",
        )

        rendered = repr(event)
        assert "MidiMonitorEvent(index=12" in rendered
        assert "type=note_off" in rendered
        assert "ch=0" in rendered
        assert "note=60" in rendered
        assert "vel=0" in rendered
        assert "elapsed_s=1.25" in rendered
        assert "elapsed_beats=2.5" in rendered

    def test_render_events_text_uses_event_str(self):
        from chordelia.midi_monitor import MidiMonitorEvent, MidiMonitorSession

        event = MidiMonitorEvent(
            event_index=1,
            monotonic_time_seconds=1.0,
            wall_time_iso=None,
            elapsed_seconds_from_session_start=None,
            elapsed_beats_from_session_start=None,
            direction="outbound",
            port_name=None,
            source_method="play_note",
            message_type="note_on",
            channel=1,
            note=64,
            velocity=90,
            raw_message_repr="Message('note_on', channel=1, note=64, velocity=90)",
        )

        rendered = MidiMonitorSession._render_events_text((event,))
        assert rendered == str(event)


class TestMidiMonitorSessionStartPatterns:
    def test_constructor_then_start_pattern(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback, max_events=10).start()

        assert session.is_running is True
        playback.play_note(C.with_octave(4), duration=None)
        rows = session.to_rows()
        assert rows
        assert rows[-1]["message_type"] == "note_on"

        session.stop()
        playback.stop()


class TestMidiMonitorContextManager:
    def test_context_manager_starts_and_stops_session(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()

        with MidiMonitorSession(playback=playback, max_events=10) as monitor:
            assert monitor.is_running is True
            playback.play_note(C.with_octave(4), duration=None)

        assert monitor.is_running is False
        assert len(monitor.events) == 1
        assert monitor.events[0].message_type == "note_on"
        playback.stop()

    def test_context_manager_does_not_swallow_exceptions(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = None

        with pytest.raises(RuntimeError, match="boom"):
            with MidiMonitorSession(playback=playback) as monitor:
                session = monitor
                raise RuntimeError("boom")

        assert session is not None
        assert session.is_running is False
        playback.stop()


class TestMidiMonitorLogging:
    def test_log_file_contains_ordered_jsonl_rows(self, mock_midi, tmp_path):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        log_file = tmp_path / "midi_monitor.jsonl"
        session = MidiMonitorSession(
            playback=playback,
            log_file=log_file,
            include_wall_time=False,
            include_elapsed_seconds=True,
            include_elapsed_beats=True,
        )
        session.start()

        playback.play_note(C.with_octave(4), duration=None)
        playback.play_note(D.with_octave(4), duration=None)

        session.stop()
        playback.stop()

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

        row_1 = json.loads(lines[0])
        row_2 = json.loads(lines[1])

        assert row_1["event_index"] == 1
        assert row_2["event_index"] == 2
        assert row_1["note"] == 60
        assert row_2["note"] == 62
        assert "wall_time_iso" not in row_1
        assert "elapsed_seconds_from_session_start" in row_1
        assert "elapsed_beats_from_session_start" in row_1

    def test_log_file_directory_path_raises_value_error(self, mock_midi, tmp_path):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()

        with pytest.raises(ValueError, match="directory"):
            MidiMonitorSession(
                playback=playback,
                log_file=tmp_path,
            ).start()

        playback.stop()


class TestMidiMonitorLiveDisplay:
    def test_display_live_validates_refresh_hz_and_max_rows(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback)

        with pytest.raises(ValueError, match="refresh_hz"):
            session.display_live(refresh_hz=0)

        with pytest.raises(ValueError, match="max_rows"):
            session.display_live(max_rows=0)

        playback.stop()

    def test_display_live_falls_back_without_ipython(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback)

        with patch("chordelia.midi_monitor._load_ipython_display_module", return_value=None):
            handle = session.display_live()

        assert handle.mode == "text"
        handle.stop()
        playback.stop()

    def test_display_live_returns_notebook_handle_when_ipython_is_available(self, mock_midi):
        from chordelia.midi_monitor import MidiMonitorSession
        from chordelia.midi_playback import MidiPlayback

        playback = MidiPlayback()
        session = MidiMonitorSession(playback=playback)

        display_calls = []
        update_calls = []

        def fake_display(payload, display_id=None):
            display_calls.append((payload, display_id))

        def fake_update(payload, display_id=None):
            update_calls.append((payload, display_id))

        fake_module = SimpleNamespace(
            display=fake_display,
            update_display=fake_update,
            Markdown=lambda text: text,
        )

        with patch("chordelia.midi_monitor._load_ipython_display_module", return_value=fake_module):
            handle = session.display_live(refresh_hz=100.0)
            assert handle.mode == "notebook"
            assert handle.display_id is not None
            handle.stop()

        assert display_calls
        assert display_calls[0][1] == handle.display_id

        playback.stop()
