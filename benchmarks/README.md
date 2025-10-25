# Benchmarks OpenRainflow

This directory contains comparative benchmarks of OpenRainflow with other Python rainflow counting packages.

## Compared Packages

1. OpenRainflow (this package)
   - Optimized with Numba JIT
   - Integrated Eurocode support
   - Miner's damage calculation
   
2. fatpack
   - Mature fatigue analysis package
   - https://github.com/Gunnstein/fatpack
   - Install: pip install fatpack
   
3. rainflow
   - Lightweight rainflow counting package
   - https://github.com/iamlikeme/rainflow
   - Install: pip install rainflow

## Installation of Comparison Packages

```bash
pip install fatpack rainflow
```

## Benchmark Scripts

### 1. benchmark_speed.py
Compares execution speed on different signal sizes.

```bash
python benchmarks/benchmark_speed.py
```

### 2. benchmark_accuracy.py
Compares result accuracy between packages.

```bash
python benchmarks/benchmark_accuracy.py
```

### 3. benchmark_memory.py
Measures memory usage for large signals.

```bash
python benchmarks/benchmark_memory.py
```

### 4. benchmark_features.py
Compares available features.

```bash
python benchmarks/benchmark_features.py
```

## Run All Benchmarks

```bash
python benchmarks/run_all_benchmarks.py
```

## Expected Results

Results are saved in:
- benchmarks/results/ - CSV files with raw data
- benchmarks/plots/ - Comparison charts

## Compared Metrics

1. Execution Speed
   - Rainflow counting time
   - JIT compilation impact (Numba)
   - Scalability with signal size

2. Accuracy
   - Number of identified cycles
   - Cycle range values
   - Result consistency

3. Memory Usage
   - Peak memory
   - Large signal handling (>1M points)

4. Features
   - S-N curve support
   - Damage calculation
   - Parallelization
   - Visualization

## Benchmark Results

### Real Results (Windows, Python 3.13)

Size     | OpenRainflow | fatpack  | rainflow | Speedup
---------|--------------|----------|----------|--------
100 pts  | 0.04 ms     | 0.36 ms  | 0.09 ms  | 9x
1k pts   | 0.04 ms     | 0.99 ms  | 1.28 ms  | 26x
10k pts  | 0.16 ms     | 9.36 ms  | 7.09 ms  | 59x
50k pts  | 1.25 ms     | 49.09 ms | 44.28 ms | 39x
100k pts | 2.01 ms     | 78.83 ms | 101.45 ms| 39x

Average speedup: 34-35x faster

Note: OpenRainflow includes ~500ms Numba compilation on first call

### Feature Score

Package      | Score | Percentage
-------------|-------|------------
OpenRainflow | 15/15 | 100%
fatpack      | 9/15  | 60%
rainflow     | 3/15  | 20%

## OpenRainflow Advantages

- Performance: ~3-4x faster after JIT compilation
- Features: Eurocode, Miner, complete analysis
- Parallelization: Native multi-signal support
- Documentation: Complete guide and examples
- Integration: Complete workflow (rainflow -> S-N -> damage)
