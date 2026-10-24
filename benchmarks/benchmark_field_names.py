"""Compare field discovery before/after #16 on the same generated records.

Run from the repository root: python benchmarks/benchmark_field_names.py --profile
The baseline reproduces field_names from commit f4bb7d0. Timings exclude data
generation, compare alternating runs, and report every sample plus the median.
This is a manual benchmark, not a timing assertion in the test suite.
"""

import argparse
import cProfile
import gc
import platform
import pstats
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tabulint import check_records
from tabulint import analyzer


def baseline_field_names(records):
    names = []
    for record in records:
        for name in record:
            if name not in names:
                names.append(name)
    return names


def measure(records, repetitions, full_report):
    optimized = analyzer.field_names
    samples = {"baseline": [], "optimized": []}
    results = {}
    try:
        for repeat in range(repetitions):
            order = ("baseline", "optimized") if repeat % 2 == 0 else ("optimized", "baseline")
            for name in order:
                analyzer.field_names = baseline_field_names if name == "baseline" else optimized
                gc.collect()
                start = time.perf_counter()
                result = check_records(records) if full_report else analyzer.field_names(records)
                samples[name].append(time.perf_counter() - start)
                results[name] = result
        assert results["baseline"] == results["optimized"], "behavior changed"
    finally:
        analyzer.field_names = optimized
    for name, values in samples.items():
        print(f"{name}: samples={','.join(f'{value:.6f}' for value in values)} "
              f"median={statistics.median(values):.6f}s")
    before = statistics.median(samples["baseline"])
    after = statistics.median(samples["optimized"])
    print(f"median reduction: {100 * (before - after) / before:.1f}%")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=100_000)
    parser.add_argument("--fields", type=int, default=32)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    if min(args.records, args.fields, args.repeat) < 1:
        parser.error("records, fields, and repeat must be positive")
    names = [f"column_{index:02d}" for index in range(args.fields)]
    records = [dict.fromkeys(names, row) for row in range(args.records)]
    print(f"Python {platform.python_version()} on {platform.platform()}")
    print(f"{args.records} distinct records x {args.fields} integer fields; "
          f"{args.repeat} alternating repetitions; generation excluded")
    if args.profile:
        optimized = analyzer.field_names
        try:
            analyzer.field_names = baseline_field_names
            profiler = cProfile.Profile()
            profiler.runcall(check_records, records)
            print("Baseline check_records cumulative profile:")
            pstats.Stats(profiler).strip_dirs().sort_stats("cumulative").print_stats(15)
        finally:
            analyzer.field_names = optimized
    print("field_names:")
    measure(records, args.repeat, full_report=False)
    print("check_records (complete Report equality verified):")
    measure(records, args.repeat, full_report=True)


if __name__ == "__main__":
    main()
