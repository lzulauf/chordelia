"""Notebook-focused interactive utilities for MIDI playback workflows."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Any

from chordelia.midi_playback import MidiPlayback, get_midi_ports
from chordelia.score import Score


@dataclass(frozen=True, slots=True)
class MidiPlaybackPanelDisplayHandle:
    """Result from MidiPlaybackPanel.display with runtime display mode metadata."""

    mode: str
    panel: "MidiPlaybackPanel"
    widget: Any = None


class MidiPlaybackPanel:
    """Notebook widget panel for selecting MIDI output and channel for playback."""

    def __init__(
        self,
        *,
        score: Score | None = None,
        output_name: str | None = None,
        channel: int = 0,
        base_octave: int = 4,
        default_velocity: int = 64,
        auto_connect: bool = False,
    ):
        self._validate_channel(channel)
        self._validate_velocity(default_velocity)

        self._score = score
        self._output_name = output_name
        self._channel = channel
        self._base_octave = base_octave
        self._default_velocity = default_velocity

        self._playback: MidiPlayback | None = None
        self._widgets: dict[str, Any] = {}
        self._status: str = "disconnected"

        if auto_connect:
            self.connect(output_name=output_name)

    @staticmethod
    def _validate_channel(channel: int) -> None:
        if not 0 <= channel <= 15:
            raise ValueError("MIDI channel must be between 0 and 15")

    @staticmethod
    def _validate_velocity(velocity: int) -> None:
        if not 0 <= velocity <= 127:
            raise ValueError("MIDI velocity must be between 0 and 127")

    @property
    def playback(self) -> MidiPlayback | None:
        """Return the active underlying MidiPlayback instance, if connected."""
        return self._playback

    @property
    def output_name(self) -> str | None:
        return self._output_name

    @property
    def channel(self) -> int:
        return self._channel

    @property
    def is_connected(self) -> bool:
        return self._playback is not None and self._playback.is_connected

    @property
    def status(self) -> str:
        return self._status

    def set_score(self, score: Score) -> None:
        """Update the panel's default score used by play_score when omitted."""
        self._score = score

    def refresh_ports(self) -> list[str]:
        """Refresh and return available MIDI output port names."""
        outputs = self._list_output_ports()

        if self._output_name is None and outputs:
            self._output_name = outputs[0]
        elif self._output_name is not None and self._output_name not in outputs:
            self._output_name = outputs[0] if outputs else None

        self._sync_widgets()
        return outputs

    def connect(self, *, output_name: str | None = None) -> MidiPlayback:
        """Connect (or reconnect) the panel to a MIDI output and return playback."""
        requested_output = self._output_name if output_name is None else output_name
        existing = self._playback
        if existing is not None:
            existing.stop()

        playback = MidiPlayback(
            output_name=requested_output,
            channel=self._channel,
            base_octave=self._base_octave,
            default_velocity=self._default_velocity,
        )
        self._playback = playback

        active_name = requested_output
        output_port = getattr(playback, "_output_port", None)
        if output_port is not None:
            active_name = getattr(output_port, "name", requested_output)

        self._output_name = active_name
        self._update_status(f"connected to {self._output_name}")
        self._sync_widgets()
        return playback

    def set_output_name(self, output_name: str | None) -> None:
        """Set output selection and reconnect active playback when connected."""
        if output_name == self._output_name:
            return

        self._output_name = output_name
        if self._playback is not None:
            self.connect(output_name=output_name)
            return

        self._update_status(
            "output selected; connect or play to open port"
            if output_name is not None
            else "output cleared"
        )
        self._sync_widgets()

    def set_channel(self, channel: int) -> None:
        """Update panel channel and propagate it to current playback when connected."""
        self._validate_channel(channel)
        self._channel = channel

        if self._playback is not None and self._playback.is_connected:
            self._playback.set_channel(channel)
            self._update_status(f"channel set to {channel}")

        self._sync_widgets()

    def play_score(
        self,
        score: Score | None = None,
        *,
        blocking: bool = False,
        velocity_scale: float = 1.0,
        channel_override: int | None = None,
        gate_width: float | None = None,
        gate_offset: float | None = None,
        retrigger_policy: str | None = None,
    ) -> None:
        """Play a score via the owned MidiPlayback instance."""
        if score is not None:
            self._score = score
        if self._score is None:
            raise ValueError("No score configured. Pass score=... or call set_score(...)")

        playback = self._require_playback()
        playback.play_score(
            self._score,
            blocking=blocking,
            velocity_scale=velocity_scale,
            channel_override=channel_override,
            gate_width=gate_width,
            gate_offset=gate_offset,
            retrigger_policy=retrigger_policy,
        )

    def stop(self) -> None:
        """Stop playback and close any active MIDI output connection."""
        if self._playback is None:
            return

        self._playback.stop()
        self._playback = None
        self._update_status("disconnected")
        self._sync_widgets()

    def close(self) -> None:
        """Alias for stop for explicit panel lifecycle teardown."""
        self.stop()

    def _require_playback(self) -> MidiPlayback:
        if self._playback is None or not self._playback.is_connected:
            return self.connect(output_name=self._output_name)
        return self._playback

    def _update_status(self, status: str) -> None:
        self._status = status
        status_widget = self._widgets.get("status")
        if status_widget is not None:
            status_widget.value = status

    def _run_ui_action(self, action) -> None:
        try:
            action()
        except Exception as exc:
            self._update_status(f"error: {exc}")

    def _sync_widgets(self) -> None:
        output_dropdown = self._widgets.get("output_dropdown")
        channel_slider = self._widgets.get("channel_slider")
        status_widget = self._widgets.get("status")

        if output_dropdown is not None:
            options = [("Auto", None)] + [(name, name) for name in self._list_output_ports()]
            output_dropdown.options = options
            output_dropdown.value = self._output_name

        if channel_slider is not None:
            channel_slider.value = self._channel

        if status_widget is not None:
            status_widget.value = self._status

    def display(self) -> MidiPlaybackPanelDisplayHandle:
        """Render interactive widget controls in notebook environments when available."""
        panel = self._build_widget_panel()
        if panel is None:
            return MidiPlaybackPanelDisplayHandle(mode="text", panel=self)

        ipy_display = importlib.import_module("IPython.display")

        display_fn = getattr(ipy_display, "display", None)
        if callable(display_fn):
            display_fn(panel)

        return MidiPlaybackPanelDisplayHandle(mode="notebook", panel=self, widget=panel)

    def _ipython_display_(self) -> None:
        """IPython hook to auto-render panel UI when object is cell output."""
        self.display()

    def _repr_mimebundle_(self, include=None, exclude=None):
        """Return rich MIME output for notebook frontends that prefer mimebundle."""
        del include, exclude
        panel = self._build_widget_panel()
        if panel is None:
            return {"text/plain": "MidiPlaybackPanel (ipywidgets/IPython not available)"}

        repr_mimebundle = getattr(panel, "_repr_mimebundle_", None)
        if callable(repr_mimebundle):
            return repr_mimebundle()

        return {"text/plain": repr(panel)}

    def _build_widget_panel(self):
        """Build and wire ipywidgets controls when notebook dependencies exist."""
        try:
            widgets = importlib.import_module("ipywidgets")
            importlib.import_module("IPython.display")
        except ModuleNotFoundError:
            self._update_status("ipywidgets/IPython not available")
            return None

        outputs = self.refresh_ports()
        output_options = [("Auto", None)] + [(name, name) for name in outputs]

        output_dropdown = widgets.Dropdown(
            options=output_options,
            value=self._output_name,
            description="Port",
        )
        channel_slider = widgets.IntSlider(
            value=self._channel,
            min=0,
            max=15,
            step=1,
            description="Channel",
            continuous_update=False,
        )
        refresh_button = widgets.Button(description="Refresh Ports")
        reconnect_button = widgets.Button(description="Reconnect")
        stop_button = widgets.Button(description="Stop")
        status = widgets.Label(value=self._status)

        def on_output_change(change: dict[str, Any]) -> None:
            if change.get("name") != "value":
                return
            self._run_ui_action(lambda: self.set_output_name(change.get("new")))

        def on_channel_change(change: dict[str, Any]) -> None:
            if change.get("name") != "value":
                return
            self._run_ui_action(lambda: self.set_channel(int(change.get("new"))))

        output_dropdown.observe(on_output_change, names="value")
        channel_slider.observe(on_channel_change, names="value")
        refresh_button.on_click(lambda _btn: self._run_ui_action(self.refresh_ports))
        reconnect_button.on_click(
            lambda _btn: self._run_ui_action(lambda: self.connect(output_name=self._output_name))
        )
        stop_button.on_click(lambda _btn: self._run_ui_action(self.stop))

        controls = widgets.HBox((refresh_button, reconnect_button, stop_button))
        panel = widgets.VBox((output_dropdown, channel_slider, controls, status))

        self._widgets = {
            "output_dropdown": output_dropdown,
            "channel_slider": channel_slider,
            "status": status,
            "panel": panel,
        }
        return panel

    @staticmethod
    def _list_output_ports() -> list[str]:
        info = get_midi_ports()
        return list(info.get("output", []))


__all__ = ["MidiPlaybackPanel", "MidiPlaybackPanelDisplayHandle"]