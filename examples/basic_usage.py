"""
Basic usage example for OpenRainflow package.

This example demonstrates:
1. Rainflow cycle counting
2. Fatigue curve selection
3. Damage calculation using Miner's rule
"""

import numpy as np
from openrainflow import rainflow_count, calculate_damage, calculate_life
from openrainflow.eurocode import EurocodeCategory
from openrainflow.damage import print_damage_report

# Set random seed for reproducibility
np.random.seed(42)

print("=" * 70)
print("OPENRAINFLOW - BASIC USAGE EXAMPLE")
print("=" * 70)

# 1. Generate a sample stress history
# In practice, this would be your measured or simulated stress data
print("\n1. Generating sample stress history...")
n_points = 10000
mean_stress = 100  # MPa
stress_amplitude = 50  # MPa
stress_history = np.random.randn(n_points) * stress_amplitude + mean_stress

print(f"   Generated {n_points} stress values")
print(f"   Mean: {np.mean(stress_history):.2f} MPa")
print(f"   Std: {np.std(stress_history):.2f} MPa")
print(f"   Range: [{np.min(stress_history):.2f}, {np.max(stress_history):.2f}] MPa")

# 2. Perform rainflow cycle counting
print("\n2. Performing rainflow cycle counting...")
cycles = rainflow_count(stress_history)

print(f"   Total cycles identified: {len(cycles)}")
print(f"   Full cycles: {np.sum(cycles['count'] == 1.0):.0f}")
print(f"   Half cycles: {np.sum(cycles['count'] == 0.5):.0f}")
print(f"   Total equivalent full cycles: {np.sum(cycles['count']):.1f}")

# Show some statistics
print(f"\n   Cycle range statistics:")
print(f"   - Min: {np.min(cycles['range']):.2f} MPa")
print(f"   - Max: {np.max(cycles['range']):.2f} MPa")
print(f"   - Mean: {np.mean(cycles['range']):.2f} MPa")

# 3. Select an Eurocode fatigue curve
print("\n3. Selecting Eurocode fatigue curve...")
category = '71'  # Detail category 71 (common for welded joints)
fatigue_curve = EurocodeCategory.get_curve(category)

print(f"   Selected category: {fatigue_curve.name}")
print(f"   Characteristic strength (2M cycles): {fatigue_curve.delta_sigma_c:.1f} MPa")
print(f"   Constant amplitude fatigue limit: {fatigue_curve.delta_sigma_L:.2f} MPa")
print(f"   Slopes: m1={fatigue_curve.m1}, m2={fatigue_curve.m2}")

# 4. Calculate cumulative damage
print("\n4. Calculating cumulative damage (Miner's rule)...")
damage = calculate_damage(cycles, fatigue_curve)

print(f"   Damage per load cycle: {damage:.6e}")
print(f"   This represents {damage*100:.4f}% of total damage capacity")

# 5. Calculate fatigue life
print("\n5. Calculating fatigue life...")
life = calculate_life(cycles, fatigue_curve)

if np.isfinite(life):
    print(f"   Expected life: {life:.2e} repetitions of this load history")
    print(f"   If this history represents 1 day of loading:")
    print(f"   - Life in days: {life:.1f}")
    print(f"   - Life in years: {life/365:.1f}")
else:
    print(f"   Expected life: INFINITE (all stress ranges below fatigue limit)")

# 6. Generate detailed damage report
print("\n6. Detailed damage assessment report:")
print_damage_report(cycles, fatigue_curve, design_life=1000)

# 7. Example with different safety factors
print("\n7. Effect of partial safety factor...")
safety_factors = [1.0, 1.15, 1.25, 1.35]

for gamma_mf in safety_factors:
    damage_factored = calculate_damage(
        cycles, 
        fatigue_curve, 
        partial_safety_factor=gamma_mf
    )
    life_factored = calculate_life(
        cycles, 
        fatigue_curve, 
        partial_safety_factor=gamma_mf
    )
    
    print(f"   γ_Mf = {gamma_mf:.2f}: Damage = {damage_factored:.6e}, "
          f"Life = {life_factored:.2e}")

print("\n" + "=" * 70)
print("Example completed successfully!")
print("=" * 70)

