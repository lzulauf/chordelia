"""Tests for notebook-focused MIDI panel APIs."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from chordelia.score import Score, ScoreEvent, ScoreMetadata


def _sample_score() -> Score:
    return Score(
        source="panel-test",
        metadata=ScoreMetadata(tempo=120, time_signature=(4, 4), ppq=480),
        events=(
            ScoreEvent(beat=0, duration=1, pitches=(60,), velocity=90, channel=0),
        ),
    )


class FakePlayback:
    """Deterministic stand-in for MidiPlayback used by notebook panel tests."""

    def __init__(
        self,
        output_name=None,
        channel=0,
        base_octave=4,
        default_velocity=64,
    ):
        self.channel = channel
        self.base_octave = base_octave
        self.default_velocity = default_velocity
        self.output_name = "Port A" if output_name is None else output_name
        self._output_port = SimpleNamespace(name=self.output_name, closed=False)
        self.stop_calls = 0
        self.play_score_calls = []

    @property
    def is_connected(self):
        return self._output_port is not None and not self._output_port.closed

    def set_channel(self, channel):
        self.channel = channel

    def play_score(self, score, **kwargs):
        self.play_score_calls.append((score, kwargs))

    def stop(self):
        self.stop_calls += 1
        if self._output_port is not None:
            self._output_port.closed = True
        self._output_port = None


class FakeDropdown:
    def __init__(self, *, options, value, description):
        self.options = options
        self.value = value
        self.description = description
        self._observers = []

    def observe(self, callback, names=None):
        del names
        self._observers.append(callback)

    def set_value(self, value):
        self.value = value
        for callback in tuple(self._observers):
            callback({"name": "value", "new": value})


class FakeIntSlider:
    def __init__(self, *, value, min, max, step, description, continuous_update):
        del min, max, step, description, continuous_update
        self.value = value
        self._observers = []

    def observe(self, callback, names=None):
        del names
        self._observers.append(callback)

    def set_value(self, value):
        self.value = value
        for callback in tuple(self._observers):
            callback({"name": "value", "new": value})


class FakeButton:
    def __init__(self, *, description):
        self.description = description
        self._callbacks = []

    def on_click(self, callback):
        self._callbacks.append(callback)

    def click(self):
        for callback in tuple(self._callbacks):
            callback(self)


class FakeLabel:
    def __init__(self, *, value):
        self.value = value


class FakeHBox:
    def __init__(self, children):
        self.children = children


class FakeVBox:
    def __init__(self, children):
        self.children = children

    def _repr_mimebundle_(self):
        return {
            "application/vnd.jupyter.widget-view+json": {"model_id": "fake-model"},
            "text/plain": "FakeVBox",
        }


class TestMidiPlaybackPanel:
    def test_play_score_uses_configured_score(self):
        import chordelia.notebook as notebook_module

        score = _sample_score()

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A", "Port B"]},
        ):
            panel = notebook_module.MidiPlaybackPanel(score=score, output_name="Port A")
            panel.play_score(blocking=False)

            assert panel.playback is not None
            assert len(panel.playback.play_score_calls) == 1
            played_score, kwargs = panel.playback.play_score_calls[0]
            assert played_score is score
            assert kwargs["blocking"] is False

    def test_play_score_requires_score(self):
        import chordelia.notebook as notebook_module

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A"]},
        ):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A")

            with pytest.raises(ValueError, match="No score"):
                panel.play_score()

    def test_channel_updates_existing_playback_instance(self):
        import chordelia.notebook as notebook_module

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A", "Port B"]},
        ):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A", auto_connect=True)
            initial_playback = panel.playback

            panel.set_channel(7)

            assert panel.playback is initial_playback
            assert panel.playback.channel == 7

    def test_output_change_reconnects_with_new_playback_instance(self):
        import chordelia.notebook as notebook_module

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A", "Port B"]},
        ):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A", auto_connect=True)
            initial_playback = panel.playback

            panel.set_output_name("Port B")

            assert initial_playback is not None
            assert initial_playback.stop_calls == 1
            assert panel.playback is not initial_playback
            assert panel.playback.output_name == "Port B"

    def test_display_falls_back_without_notebook_modules(self):
        import chordelia.notebook as notebook_module

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A"]},
        ), patch(
            "chordelia.notebook.importlib.import_module",
            side_effect=ModuleNotFoundError("ipywidgets is missing"),
        ):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A")
            handle = panel.display()

            assert handle.mode == "text"

    def test_widget_changes_update_channel_and_reconnect_on_output_change(self):
        import chordelia.notebook as notebook_module

        fake_widgets_module = SimpleNamespace(
            Dropdown=FakeDropdown,
            IntSlider=FakeIntSlider,
            Button=FakeButton,
            Label=FakeLabel,
            HBox=FakeHBox,
            VBox=FakeVBox,
        )

        display_calls = []
        fake_display_module = SimpleNamespace(display=lambda payload: display_calls.append(payload))

        def fake_import_module(name: str):
            if name == "ipywidgets":
                return fake_widgets_module
            if name == "IPython.display":
                return fake_display_module
            raise ModuleNotFoundError(name)

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A", "Port B"]},
        ), patch("chordelia.notebook.importlib.import_module", side_effect=fake_import_module):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A", auto_connect=True)
            initial_playback = panel.playback

            handle = panel.display()
            assert handle.mode == "notebook"
            assert display_calls

            channel_slider = panel._widgets["channel_slider"]
            channel_slider.set_value(3)

            assert panel.playback is initial_playback
            assert panel.playback.channel == 3

            output_dropdown = panel._widgets["output_dropdown"]
            output_dropdown.set_value("Port B")

            assert panel.playback is not initial_playback
            assert panel.playback.output_name == "Port B"

    def test_ipython_display_hook_delegates_to_display(self):
        import chordelia.notebook as notebook_module

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A"]},
        ):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A")

            with patch.object(panel, "display", wraps=panel.display) as display_mock:
                result = panel._ipython_display_()

            assert result is None
            assert display_mock.call_count == 1

    def test_repr_mimebundle_returns_widget_mimebundle_when_available(self):
        import chordelia.notebook as notebook_module

        fake_widgets_module = SimpleNamespace(
            Dropdown=FakeDropdown,
            IntSlider=FakeIntSlider,
            Button=FakeButton,
            Label=FakeLabel,
            HBox=FakeHBox,
            VBox=FakeVBox,
        )

        fake_display_module = SimpleNamespace(display=lambda _payload: None)

        def fake_import_module(name: str):
            if name == "ipywidgets":
                return fake_widgets_module
            if name == "IPython.display":
                return fake_display_module
            raise ModuleNotFoundError(name)

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A", "Port B"]},
        ), patch("chordelia.notebook.importlib.import_module", side_effect=fake_import_module):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A")
            mimebundle = panel._repr_mimebundle_()

            assert "application/vnd.jupyter.widget-view+json" in mimebundle

    def test_repr_mimebundle_returns_text_fallback_without_notebook_modules(self):
        import chordelia.notebook as notebook_module

        with patch.object(notebook_module, "MidiPlayback", FakePlayback), patch.object(
            notebook_module,
            "get_midi_ports",
            return_value={"output": ["Port A"]},
        ), patch(
            "chordelia.notebook.importlib.import_module",
            side_effect=ModuleNotFoundError("ipywidgets is missing"),
        ):
            panel = notebook_module.MidiPlaybackPanel(output_name="Port A")
            mimebundle = panel._repr_mimebundle_()

            assert mimebundle["text/plain"].startswith("MidiPlaybackPanel")
