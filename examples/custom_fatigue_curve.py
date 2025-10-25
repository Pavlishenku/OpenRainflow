"""
Example demonstrating custom fatigue curve creation.

Shows how to:
1. Create custom S-N curves
2. Compare with Eurocode standards
3. Use custom curves in damage calculations
"""

import numpy as np
import matplotlib.pyplot as plt
from openrainflow import rainflow_count, calculate_damage
from openrainflow.eurocode import EurocodeCategory, create_custom_curve, plot_sn_curve

print("=" * 70)
print("CUSTOM FATIGUE CURVE EXAMPLE")
print("=" * 70)

# 1. Create a custom fatigue curve
print("\n1. Creating custom fatigue curves...")

# Example 1: Custom curve with different slope
custom_curve_1 = create_custom_curve(
    name='Custom-1',
    delta_sigma_c=90.0,  # Strength at 2M cycles
    m1=3.5,  # Steeper slope in normal range
    m2=5.0
)

# Example 2: Custom curve for aluminum (different slopes)
custom_curve_2 = create_custom_curve(
    name='Aluminum',
    delta_sigma_c=65.0,
    m1=4.0,  # Aluminum typically has higher slope
    m2=6.0,
    N_cutoff=5e8  # Different cutoff
)

# Example 3: Custom CAFL
custom_curve_3 = create_custom_curve(
    name='Custom-CAFL',
    delta_sigma_c=80.0,
    delta_sigma_L=25.0  # Explicit fatigue limit
)

print(f"   Created 3 custom curves:")
print(f"   - {custom_curve_1}")
print(f"   - {custom_curve_2}")
print(f"   - {custom_curve_3}")

# 2. Compare with Eurocode standard
print("\n2. Comparing with Eurocode standard...")

eurocode_71 = EurocodeCategory.get_curve('71')
eurocode_50 = EurocodeCategory.get_curve('50')

# Test stress range
test_stress = 100.0

curves_to_compare = [
    ('Eurocode 71', eurocode_71),
    ('Eurocode 50', eurocode_50),
    ('Custom-1', custom_curve_1),
    ('Aluminum', custom_curve_2),
    ('Custom-CAFL', custom_curve_3),
]

print(f"\n   Cycles to failure at Δσ = {test_stress:.1f} MPa:")
for name, curve in curves_to_compare:
    N_f = curve.get_cycles_to_failure(test_stress)
    print(f"   {name:15s}: {N_f:.3e} cycles")

# 3. Visualize S-N curves
print("\n3. Plotting S-N curves...")

fig, ax = plt.subplots(figsize=(12, 8))

N_range = np.logspace(3, 9, 500)

for name, curve in curves_to_compare:
    stress_range = curve.get_stress_range(N_range)
    ax.loglog(N_range, stress_range, linewidth=2.5, label=name)
    
    # Mark the knee point
    ax.plot(curve.N_knee, curve.delta_sigma_knee, 'o', markersize=6)
    
    # Mark the CAFL
    ax.axhline(curve.delta_sigma_L, linestyle='--', alpha=0.4)

ax.set_xlabel('Number of Cycles, N', fontsize=13)
ax.set_ylabel('Stress Range, Δσ [MPa]', fontsize=13)
ax.set_title('Comparison of Custom and Eurocode Fatigue Curves', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=11, loc='upper right')
ax.grid(True, which='both', alpha=0.3)
ax.set_xlim(1e3, 1e9)
ax.set_ylim(10, 300)

plt.tight_layout()
plt.savefig('examples/custom_curves_comparison.png', dpi=150)
print("   S-N curves saved to 'examples/custom_curves_comparison.png'")

# 4. Damage calculation with custom curves
print("\n4. Damage calculation comparison...")

# Generate a stress history
np.random.seed(42)
stress_history = np.random.randn(5000) * 40 + 120

# Rainflow count
cycles = rainflow_count(stress_history)

print(f"\n   Stress history: {len(stress_history)} points")
print(f"   Rainflow cycles: {len(cycles)}")
print(f"   Mean stress range: {np.mean(cycles['range']):.2f} MPa")

# Calculate damage with each curve
print(f"\n   Damage comparison:")
for name, curve in curves_to_compare:
    damage = calculate_damage(cycles, curve)
    life = 1.0 / damage if damage > 0 else np.inf
    
    print(f"   {name:15s}: Damage = {damage:.6e}, Life = {life:.3e}")

# 5. Sensitivity analysis
print("\n5. Sensitivity to slope parameter m...")

slopes = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
damages_vs_slope = []

for m in slopes:
    curve = create_custom_curve(
        name=f'm={m}',
        delta_sigma_c=71.0,
        m1=m,
        m2=m+2
    )
    damage = calculate_damage(cycles, curve)
    damages_vs_slope.append(damage)

print(f"\n   Slope (m) | Damage")
print("   " + "-" * 25)
for m, damage in zip(slopes, damages_vs_slope):
    print(f"   {m:7.1f}   | {damage:.6e}")

# Plot sensitivity
fig, ax = plt.subplots(figsize=(10, 6))
ax.semilogy(slopes, damages_vs_slope, 'o-', linewidth=2, markersize=8)
ax.set_xlabel('Slope Parameter, m', fontsize=12)
ax.set_ylabel('Cumulative Damage', fontsize=12)
ax.set_title('Sensitivity of Damage to S-N Curve Slope', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('examples/slope_sensitivity.png', dpi=150)
print("\n   Sensitivity plot saved to 'examples/slope_sensitivity.png'")

# 6. Design curve with safety margin
print("\n6. Creating design curve with built-in safety margin...")

# Original curve
base_curve = EurocodeCategory.get_curve('71')

# Design curve: reduce strength by 20% (equivalent to safety factor)
design_strength = base_curve.delta_sigma_c * 0.8
design_curve = create_custom_curve(
    name='Design (with margin)',
    delta_sigma_c=design_strength,
    m1=base_curve.m1,
    m2=base_curve.m2
)

damage_base = calculate_damage(cycles, base_curve)
damage_design = calculate_damage(cycles, design_curve)

print(f"\n   Base curve (Cat 71):")
print(f"   - Strength at 2M: {base_curve.delta_sigma_c:.1f} MPa")
print(f"   - Damage: {damage_base:.6e}")

print(f"\n   Design curve (20% margin):")
print(f"   - Strength at 2M: {design_curve.delta_sigma_c:.1f} MPa")
print(f"   - Damage: {damage_design:.6e}")
print(f"   - Damage ratio: {damage_design/damage_base:.2f}x")

print("\n" + "=" * 70)
print("Custom curve example completed!")
print("=" * 70)

