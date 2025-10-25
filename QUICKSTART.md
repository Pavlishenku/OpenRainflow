# Quick Start Guide

## Installation

```bash
cd OpenRainflow
pip install -e .
```

For parallel processing support:
```bash
pip install -e ".[parallel]"
```

## Basic Example

```python
import numpy as np
from openrainflow import rainflow_count, calculate_damage
from openrainflow.eurocode import EurocodeCategory

# 1. Your stress/strain history
stress_history = np.random.randn(10000) * 50 + 100

# 2. Count cycles using rainflow method
cycles = rainflow_count(stress_history)

# 3. Select fatigue curve (Eurocode category)
fatigue_curve = EurocodeCategory.get_curve('71')

# 4. Calculate damage
damage = calculate_damage(cycles, fatigue_curve)

# 5. Check result
print(f"Cumulative damage: {damage:.6e}")
print(f"Life: {1/damage:.2e} repetitions" if damage > 0 else "Infinite life")
```

## Eurocode Categories

Category | Strength @ 2M cycles | Typical Application
---------|---------------------|--------------------
160      | 160 MPa            | Parent material, rolled
125      | 125 MPa            | Parent material, flame cut
112      | 112 MPa            | High quality welded joints
100      | 100 MPa            | Good quality welded joints
90       | 90 MPa             | Welded attachments
80       | 80 MPa             | Transverse butt welds
71       | 71 MPa             | Common welded details
63       | 63 MPa             | Welded attachments
56       | 56 MPa             | Cruciform joints
50       | 50 MPa             | Load-carrying welds
45       | 45 MPa             | Complex welded joints
40       | 40 MPa             | Severe stress concentration
36       | 36 MPa             | Very severe stress concentration

## Running Examples

```bash
python examples/basic_usage.py
python examples/advanced_analysis.py
python examples/custom_fatigue_curve.py
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
pytest --cov=openrainflow --cov-report=html
```

## Common Use Cases

### Multiple Signals in Parallel

```python
from openrainflow.parallel import ParallelFatigueAnalyzer

analyzer = ParallelFatigueAnalyzer(n_jobs=4)
analyzer.add_signals([signal1, signal2, signal3])
analyzer.set_fatigue_curve('71')
results = analyzer.analyze(design_life=1000)

print(results['damages'])
```

### Custom Fatigue Curve

```python
from openrainflow.eurocode import create_custom_curve

curve = create_custom_curve(
    name='MyMaterial',
    delta_sigma_c=85.0,  # Strength at 2M cycles
    m1=3.5,              # Slope
)
```

### Detailed Safety Assessment

```python
from openrainflow.damage import print_damage_report

print_damage_report(
    cycles, 
    fatigue_curve, 
    design_life=50,
    partial_safety_factor=1.25
)
```

## Performance Tips

1. Use Numba cache: First run compiles JIT functions, subsequent runs are fast
2. Parallel processing: Use n_jobs=-1 for all CPU cores
3. Batch processing: For very large datasets, use ParallelFatigueAnalyzer
4. Memory: rainflow_count is memory-efficient, processes in-place where possible

## Getting Help

- Documentation: See README.md
- Examples: Check examples/ directory
- Tests: Look at tests/ for usage patterns
- Issues: Report bugs on GitHub
