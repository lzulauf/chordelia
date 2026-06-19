"""Pytest configuration for the chordelia test suite.

Provides a small helper to skip tests marked with ``@pytest.mark.slow`` by
default. To run slow tests explicitly, pass ``--runslow`` to pytest.

This keeps CI and quick local runs fast while still allowing the full suite
to run when desired.
"""

import pytest
import importlib.util


def pytest_addoption(parser):
	"""Add command line option to enable slow tests.

	Usage:
		pytest --runslow
	"""
	parser.addoption(
		"--runslow",
		action="store_true",
		default=False,
		help="run tests marked with @pytest.mark.slow",
	)


def pytest_collection_modifyitems(config, items):
	"""Modify collected tests: skip those marked `slow` unless `--runslow` is set.

	This is a common pattern to keep slow tests out of default runs.
	"""
	runslow = config.getoption("runslow")
	missing_audio_dependencies = [
		module_name
		for module_name in ("numpy", "sounddevice")
		if importlib.util.find_spec(module_name) is None
	]

	skip_marker = pytest.mark.skip(reason="skipped slow test (use --runslow to run)")
	for item in items:
		if "slow" in item.keywords and not runslow:
			item.add_marker(skip_marker)

		if "optional_audio" in item.keywords and missing_audio_dependencies:
			item.add_marker(
				pytest.mark.skip(
					reason=(
						"missing optional dependencies for 'optional_audio': "
						+ ", ".join(missing_audio_dependencies)
					)
				)
			)


@pytest.fixture
def reset_chordelia_context_state():
	"""Reset full Chordelia runtime context for test isolation."""
	from chordelia.scale_context import get_chordelia_context, reset_chordelia_context, set_chordelia_context

	previous_context = get_chordelia_context()
	reset_chordelia_context()
	try:
		yield
	finally:
		set_chordelia_context(previous_context)


@pytest.fixture
def reset_global_scale_context_state():
	"""Reset only the scale context while restoring full context afterward."""
	from chordelia.scale_context import get_chordelia_context, reset_global_scale_context, set_chordelia_context

	previous_context = get_chordelia_context()
	reset_global_scale_context()
	try:
		yield
	finally:
		set_chordelia_context(previous_context)


@pytest.fixture
def reset_global_random_state():
	"""Reset the Random global singleton for test isolation."""
	import chordelia.randomization as randomization_module
	from chordelia import reset_global_random

	previous_global_random = randomization_module._GLOBAL_RANDOM
	reset_global_random()
	try:
		yield
	finally:
		randomization_module._GLOBAL_RANDOM = previous_global_random


@pytest.fixture
def restore_sheetmusic_runtime_rendering_config_state():
	"""Reset and restore sheetmusic runtime rendering configuration and hooks."""
	import chordelia.sheetmusic_runtime as runtime

	previous_config = runtime.get_sheetmusic_rendering_config()
	runtime.uninstall_sequenceable_sheetmusic_display_hooks()
	runtime.reset_sheetmusic_rendering_config()
	try:
		yield
	finally:
		runtime.uninstall_sequenceable_sheetmusic_display_hooks()
		runtime._RENDERING_CONFIG.set(previous_config)  # type: ignore[attr-defined]


@pytest.fixture
def restore_sheetmusic_backend_adapters_state():
	"""Restore registered sheetmusic backend adapters after the test."""
	from chordelia.sheet_music import SheetMusic

	previous_adapters = dict(SheetMusic._RENDER_BACKEND_ADAPTERS)
	try:
		yield
	finally:
		SheetMusic._RENDER_BACKEND_ADAPTERS.clear()
		SheetMusic._RENDER_BACKEND_ADAPTERS.update(previous_adapters)
