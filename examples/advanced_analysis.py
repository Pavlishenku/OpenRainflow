"""
Advanced analysis example with multiple signals and parallel processing.

This example demonstrates:
1. Parallel rainflow counting on multiple signals
2. Batch damage calculation
3. Damage contribution analysis
4. Comparison of different fatigue curves
"""

import numpy as np
import matplotlib.pyplot as plt
from openrainflow import rainflow_count_parallel
from openrainflow.eurocode import EurocodeCategory
from openrainflow.damage import (
    calculate_damage, 
    damage_contribution_analysis,
    assess_fatigue_safety
)
from openrainflow.parallel import ParallelFatigueAnalyzer

# Set random seed
np.random.seed(42)

print("=" * 70)
print("OPENRAINFLOW - ADVANCED ANALYSIS EXAMPLE")
print("=" * 70)

# 1. Generate multiple stress histories (e.g., from different load cases)
print("\n1. Generating multiple stress histories...")
n_signals = 20
n_points = 5000

signals = []
for i in range(n_signals):
    # Vary the stress characteristics for each signal
    mean_stress = 80 + np.random.rand() * 40
    amplitude = 30 + np.random.rand() * 30
    signal = np.random.randn(n_points) * amplitude + mean_stress
    signals.append(signal)

print(f"   Generated {n_signals} signals with {n_points} points each")

# 2. Parallel rainflow counting
print("\n2. Performing parallel rainflow counting...")
cycles_list = rainflow_count_parallel(signals, n_jobs=4)

total_cycles = sum(len(c) for c in cycles_list)
print(f"   Total cycles across all signals: {total_cycles}")
print(f"   Average cycles per signal: {total_cycles/n_signals:.1f}")

# 3. Parallel fatigue analysis using ParallelFatigueAnalyzer
print("\n3. Setting up parallel fatigue analyzer...")
analyzer = ParallelFatigueAnalyzer(n_jobs=4, verbose=0)
analyzer.add_signals(signals)
analyzer.set_fatigue_curve('71')

print("\n4. Running complete analysis...")
results = analyzer.analyze(design_life=1000)

print(f"\n   Analysis Results:")
print(f"   - Number of signals: {results['n_signals']}")
print(f"   - Maximum damage: {results['max_damage']:.6e}")
print(f"   - Minimum life: {results['min_life']:.2e} repetitions")
print(f"   - Maximum utilization: {results['max_utilization']:.2%}")

# 5. Compare different fatigue curves
print("\n5. Comparing different Eurocode categories...")
categories = ['36', '50', '71', '100']
comparison_results = {}

for category in categories:
    curve = EurocodeCategory.get_curve(category)
    damages = []
    
    for cycles in cycles_list:
        damage = calculate_damage(cycles, curve)
        damages.append(damage)
    
    comparison_results[category] = {
        'mean_damage': np.mean(damages),
        'max_damage': np.max(damages),
        'min_life': np.min([1/d if d > 0 else np.inf for d in damages])
    }

print("\n   Category | Mean Damage | Max Damage  | Min Life")
print("   " + "-" * 50)
for cat in categories:
    res = comparison_results[cat]
    print(f"   {cat:8s} | {res['mean_damage']:11.4e} | "
          f"{res['max_damage']:11.4e} | {res['min_life']:8.2e}")

# 6. Damage contribution analysis for first signal
print("\n6. Analyzing damage contribution for first signal...")
cycles = cycles_list[0]
curve = EurocodeCategory.get_curve('71')

bins, counts, damage_fractions = damage_contribution_analysis(
    cycles, curve, n_bins=20
)

# Find the bin with maximum damage contribution
max_damage_bin = np.argmax(damage_fractions)
print(f"   Most damaging stress range: {bins[max_damage_bin]:.2f} MPa")
print(f"   Contributes {damage_fractions[max_damage_bin]*100:.1f}% of total damage")

# Top 3 contributors
top_indices = np.argsort(damage_fractions)[-3:][::-1]
print(f"\n   Top 3 damage contributors:")
for i, idx in enumerate(top_indices, 1):
    print(f"   {i}. Range {bins[idx]:.2f} MPa: "
          f"{damage_fractions[idx]*100:.1f}% ({counts[idx]:.1f} cycles)")

# 7. Safety assessment for critical case
print("\n7. Safety assessment for most critical signal...")
critical_idx = np.argmax(results['damages'])
critical_cycles = cycles_list[critical_idx]

utilization, status, details = assess_fatigue_safety(
    critical_cycles, 
    curve, 
    design_life=1000,
    partial_safety_factor=1.25
)

print(f"\n   Most critical signal: #{critical_idx}")
print(f"   Status: {status}")
print(f"   Utilization: {utilization:.2%}")
print(f"   Reserve factor: {details['reserve_factor']:.2f}")
print(f"   Equivalent stress (2M): {details['equivalent_stress']:.2f} MPa")

# 8. Create visualization
print("\n8. Creating visualization...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Damage distribution across signals
ax = axes[0, 0]
ax.bar(range(len(results['damages'])), results['damages'])
ax.set_xlabel('Signal Number')
ax.set_ylabel('Damage')
ax.set_title('Damage Distribution Across Signals')
ax.grid(True, alpha=0.3)

# Plot 2: Life distribution
ax = axes[0, 1]
lives_finite = [l for l in results['lives'] if np.isfinite(l)]
if lives_finite:
    ax.hist(np.log10(lives_finite), bins=15, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Log₁₀(Life [repetitions])')
    ax.set_ylabel('Frequency')
    ax.set_title('Fatigue Life Distribution')
    ax.grid(True, alpha=0.3)

# Plot 3: Damage contribution for critical signal
ax = axes[1, 0]
ax.bar(bins, damage_fractions * 100, width=np.diff(bins)[0] * 0.8)
ax.set_xlabel('Stress Range [MPa]')
ax.set_ylabel('Damage Contribution [%]')
ax.set_title(f'Damage Contribution (Signal #{critical_idx})')
ax.grid(True, alpha=0.3)

# Plot 4: Comparison of fatigue curves
ax = axes[1, 1]
for category in categories:
    curve = EurocodeCategory.get_curve(category)
    N_range = np.logspace(4, 8, 100)
    stress_range = curve.get_stress_range(N_range)
    ax.loglog(N_range, stress_range, linewidth=2, label=f'Cat. {category}')

ax.set_xlabel('Number of Cycles, N')
ax.set_ylabel('Stress Range, Δσ [MPa]')
ax.set_title('Eurocode S-N Curves Comparison')
ax.legend()
ax.grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig('examples/advanced_analysis_results.png', dpi=150)
print("   Visualization saved to 'examples/advanced_analysis_results.png'")

# 9. Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(analyzer.get_summary())

print("Advanced analysis completed successfully!")
print("=" * 70)

