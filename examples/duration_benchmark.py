"""Simple performance benchmarks for Duration operations.

This script measures common Duration arithmetic and conversion paths,
including a scheduling-style conversion loop similar to playback setup.

Usage:
    python examples/duration_benchmark.py
    python examples/duration_benchmark.py --iterations 300000 --events 80000
"""

from __future__ import annotations

import argparse
import platform
import statistics
import time
from typing import Callable

from chordelia.rhythm import Duration, TimeSignature


def _ops_per_second(label: str, iterations: int, fn: Callable[[], None], repeats: int = 3) -> None:
    """Run a small repeated benchmark and print median throughput."""
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - start
        samples.append(elapsed)

    median = statistics.median(samples)
    ops = iterations / median
    print(f"{label:<32} {ops:>12.0f} ops/s   ({(median / iterations) * 1e6:>8.2f} us/op)")


def benchmark_duration_operations(iterations: int) -> None:
    """Benchmark core Duration arithmetic and conversion paths."""
    print("Duration operation microbenchmarks")
    print("-" * 72)

    time_sig = TimeSignature(4, 4)

    note_a = Duration("quarter")
    note_b = Duration("eighth")

    beat_a = Duration.from_beats(1)
    beat_b = Duration.from_beats(1, 2)

    sec_a = Duration.from_seconds("1.0")
    sec_b = Duration.from_seconds("0.5")

    _ops_per_second(
        "note_fraction add",
        iterations,
        lambda: [note_a + note_b for _ in range(iterations)],
    )

    _ops_per_second(
        "beats add",
        iterations,
        lambda: [beat_a + beat_b for _ in range(iterations)],
    )

    _ops_per_second(
        "seconds add",
        iterations,
        lambda: [sec_a + sec_b for _ in range(iterations)],
    )

    _ops_per_second(
        "beats to_milliseconds",
        iterations,
        lambda: [beat_a.to_milliseconds(120, time_sig) for _ in range(iterations)],
    )

    _ops_per_second(
        "seconds to_milliseconds",
        iterations,
        lambda: [sec_a.to_milliseconds(120, time_sig) for _ in range(iterations)],
    )

    print()


def benchmark_scheduling_conversions(event_count: int) -> None:
    """Benchmark conversion throughput for event scheduling-style loops."""
    print("Scheduling-style conversion benchmark")
    print("-" * 72)

    time_sig = TimeSignature(4, 4)

    starts = [Duration.from_beats(i % 8, None) for i in range(event_count)]
    durations = [
        Duration.from_beats(1, 2) if i % 2 else Duration.from_beats(1, None)
        for i in range(event_count)
    ]

    start = time.perf_counter()
    for start_offset, duration in zip(starts, durations):
        _ = start_offset.to_milliseconds(120, time_sig)
        _ = duration.to_milliseconds(120, time_sig)
    elapsed = time.perf_counter() - start

    conversions = 2 * event_count
    print(
        f"Converted {conversions} timing values in {elapsed:.4f}s "
        f"({(conversions / elapsed):.0f} conv/s, {(elapsed / conversions) * 1e6:.2f} us/conv)"
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Duration operations.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=200_000,
        help="Iterations for microbenchmarks (default: 200000)",
    )
    parser.add_argument(
        "--events",
        type=int,
        default=50_000,
        help="Number of events for scheduling benchmark (default: 50000)",
    )
    args = parser.parse_args()

    print("Duration benchmark (informational, not a strict profiler)")
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Iterations: {args.iterations}")
    print(f"Events: {args.events}")
    print()

    benchmark_duration_operations(args.iterations)
    benchmark_scheduling_conversions(args.events)


if __name__ == "__main__":
    main()
