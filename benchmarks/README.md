# Field discovery benchmark

Run from the repository root with no extra dependencies:

```bash
python benchmarks/benchmark_field_names.py --profile --records 100000 --fields 32 --repeat 3
```

The script generates 100,000 distinct records with the same 32 integer fields.
Generation is excluded from timings. The baseline copies `field_names` from
commit `f4bb7d0`; both versions operate on the same in-memory data. Runs alternate
baseline/optimized order, collect garbage before timing, and compare the complete
returned `Report` objects for equality. Profiling is separate from timed runs.

On Python 3.12.10 / Windows 11, field discovery was called three times in one
`check_records` call and consumed 1.384 seconds of the 23.666-second profiled run.
The change replaces repeated linear list membership with a set while retaining
the ordered output list. Extra memory grows with the number of distinct fields,
not the number of records. It does not change the checks, issue ordering, or
messages. These are measurements for this dataset and machine, not timing tests.

Recorded output:

```text
Python 3.12.10 on Windows-11-10.0.26300-SP0
100000 distinct records x 32 integer fields; 3 alternating repetitions; generation excluded
Baseline check_records cumulative profile:
         91101409 function calls (91101404 primitive calls) in 23.666 seconds

   Ordered by: cumulative time
   List reduced from 140 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000   23.666   23.666 __init__.py:49(check_records)
        1    0.043    0.043   18.794   18.794 analyzer.py:219(analyze)
        1    0.105    0.105   12.768   12.768 analyzer.py:160(check_duplicates)
   100000    5.725    0.000   12.557    0.000 analyzer.py:111(_record_key)
        2    2.407    1.203    9.585    4.792 analyzer.py:62(profile_fields)
  6400000    2.423    0.000    4.939    0.000 analyzer.py:21(infer_type)
        1    0.000    0.000    4.713    4.713 analyzer.py:189(check_type_consistency)
 38600007    3.282    0.000    3.282    0.000 {built-in method builtins.isinstance}
   100000    0.579    0.000    2.720    0.000 {built-in method builtins.sorted}
  3200000    1.432    0.000    2.141    0.000 analyzer.py:133(<lambda>)
  9600000    1.330    0.000    2.068    0.000 analyzer.py:12(is_missing)
        3    1.384    0.461    1.384    0.461 benchmark_field_names.py:25(baseline_field_names)
  6500006    1.353    0.000    1.353    0.000 {method 'get' of 'dict' objects}
        1    0.354    0.354    1.270    1.270 analyzer.py:82(check_missing_values)
  6400000    0.851    0.000    0.851    0.000 {built-in method builtins.repr}

field_names:
baseline: samples=0.585353,0.548794,0.490337 median=0.548794s
optimized: samples=0.060775,0.066915,0.067444 median=0.066915s
median reduction: 87.8%
check_records (complete Report equality verified):
baseline: samples=6.570621,6.533645,6.567959 median=6.567959s
optimized: samples=5.205777,5.165633,5.149156 median=5.165633s
median reduction: 21.4%
```
