"""Pytest configuration for the chordelia test suite.

Provides a small helper to skip tests marked with ``@pytest.mark.slow`` by
default. To run slow tests explicitly, pass ``--runslow`` to pytest.

This keeps CI and quick local runs fast while still allowing the full suite
to run when desired.
"""

import pytest


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
	if config.getoption("runslow"):
		# User explicitly asked to run slow tests; do nothing.
		return

	skip_marker = pytest.mark.skip(reason="skipped slow test (use --runslow to run)")
	for item in items:
		if "slow" in item.keywords:
			item.add_marker(skip_marker)
