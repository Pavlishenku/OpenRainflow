# OpenRainflow

Python package for fatigue analysis using the rainflow counting method, Eurocode fatigue curves, and Miner's cumulative damage calculation.

## Installation

```bash
pip install openrainflow
```

For local development:

```bash
git clone https://github.com/Pavlishenku/OpenRainflow.git
cd OpenRainflow
pip install -e .
```

## Quick Example

```python
import numpy as np
from openrainflow import rainflow_count, calculate_damage
from openrainflow.eurocode import EurocodeCategory

# Stress history data
stress_history = np.random.randn(10000) * 100 + 200

# Rainflow counting
cycles = rainflow_count(stress_history)

# Define fatigue curve (Eurocode category 36)
fatigue_curve = EurocodeCategory.get_curve('36')

# Calculate cumulative damage
damage = calculate_damage(cycles, fatigue_curve)

print(f"Cumulative damage: {damage:.6f}")
print(f"Estimated life: {1/damage:.2f} repetitions" if damage > 0 else "Infinite")
```

## Features

- Optimized rainflow algorithm with Numba JIT compilation
- High performance for large datasets
- Multi-threading support for parallel processing
- Complete implementation of Eurocode EN 1993-1-9 fatigue curves
- Miner's rule for damage calculation
- Comprehensive test coverage

## Eurocode Fatigue Curves

Supported categories: 160, 125, 112, 100, 90, 80, 71, 63, 56, 50, 45, 40, 36

Based on EN 1993-1-9:2005 standard.

## Performance

Benchmarks on Intel Core i7:
- Rainflow counting: ~1M points/second (JIT mode)
- Damage calculation: ~100k cycles/second
- Memory optimized for large datasets (>10M points)

## Documentation

See QUICKSTART.md for detailed usage examples.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License - see LICENSE file for details.
