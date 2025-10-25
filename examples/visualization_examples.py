"""
Examples of visualization capabilities in OpenRainflow.

This module demonstrates various plotting functions for:
- Cycle distributions
- Damage analysis
- S-N curves
- Complete fatigue assessments
"""

import numpy as np
import matplotlib.pyplot as plt

# Import OpenRainflow
from openrainflow import rainflow_count
from openrainflow.eurocode import EurocodeCategory
from openrainflow.visualization import (
    plot_rainflow_cycles,
    plot_cycle_histogram,
    plot_damage_contribution,
    plot_sn_curve,
    plot_fatigue_assessment,
    plot_signal_with_cycles,
    plot_multiple_sn_curves
)


def example_1_basic_cycle_plot():
    """Example 1: Basic rainflow cycle distribution plot."""
    print("=" * 70)
    print("Example 1: Rainflow Cycle Distribution")
    print("=" * 70)
    
    # Generate random stress history
    np.random.seed(42)
    signal = np.random.randn(1000) * 50 + 100
    
    # Rainflow counting
    cycles = rainflow_count(signal)
    
    # Plot cycle distribution
    fig = plot_rainflow_cycles(cycles, show_half_cycles=True)
    fig.savefig('temp/example1_cycle_distribution.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example1_cycle_distribution.png")
    print(f"  Total cycles detected: {np.sum(cycles['count']):.0f}")
    print(f"  Range: [{np.min(cycles['range']):.1f}, {np.max(cycles['range']):.1f}] MPa")
    plt.close(fig)


def example_2_cycle_histogram():
    """Example 2: Cycle range histogram."""
    print("\n" + "=" * 70)
    print("Example 2: Cycle Range Histogram")
    print("=" * 70)
    
    # Generate signal with multiple load levels
    np.random.seed(42)
    signal = []
    for _ in range(20):
        # Low amplitude cycles
        signal.extend(np.random.randn(50) * 20 + 80)
        # High amplitude cycle
        signal.extend([80, 150, 80])
    signal = np.array(signal)
    
    cycles = rainflow_count(signal)
    
    # Plot histogram
    fig = plot_cycle_histogram(cycles, n_bins=25)
    fig.savefig('temp/example2_cycle_histogram.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example2_cycle_histogram.png")
    print(f"  Total cycles: {np.sum(cycles['count']):.0f}")
    print(f"  Mean range: {np.average(cycles['range'], weights=cycles['count']):.1f} MPa")
    plt.close(fig)


def example_3_damage_contribution():
    """Example 3: Damage contribution analysis."""
    print("\n" + "=" * 70)
    print("Example 3: Damage Contribution Analysis")
    print("=" * 70)
    
    # Generate realistic stress history
    np.random.seed(42)
    base = 100
    variable = np.random.randn(2000) * 30
    periodic = 40 * np.sin(np.linspace(0, 10*np.pi, 2000))
    signal = base + variable + periodic
    
    cycles = rainflow_count(signal)
    curve = EurocodeCategory.get_curve('71')
    
    # Plot damage contribution
    fig = plot_damage_contribution(cycles, curve, n_bins=20)
    fig.savefig('temp/example3_damage_contribution.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example3_damage_contribution.png")
    print(f"  Fatigue curve: {curve.name}")
    print(f"  Total cycles: {np.sum(cycles['count']):.0f}")
    plt.close(fig)


def example_4_sn_curve():
    """Example 4: S-N curve with data points."""
    print("\n" + "=" * 70)
    print("Example 4: S-N Curve (Wöhler Curve)")
    print("=" * 70)
    
    # Get fatigue curve
    curve = EurocodeCategory.get_curve('71')
    
    # Sample stress ranges from measurements
    measured_stresses = np.array([80, 100, 120, 150, 180])
    
    # Plot S-N curve
    fig = plot_sn_curve(curve, show_data_points=measured_stresses)
    fig.savefig('temp/example4_sn_curve.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example4_sn_curve.png")
    print(f"  Curve: {curve.name}")
    print(f"  Reference: Δσ_c = {curve.delta_sigma_c} MPa at N = {curve.N_ref:.0e}")
    print(f"  CAFL: {curve.delta_sigma_L:.1f} MPa")
    plt.close(fig)


def example_5_complete_assessment():
    """Example 5: Complete fatigue assessment dashboard."""
    print("\n" + "=" * 70)
    print("Example 5: Complete Fatigue Assessment Dashboard")
    print("=" * 70)
    
    # Generate stress history
    np.random.seed(42)
    signal = np.random.randn(1500) * 45 + 110
    
    cycles = rainflow_count(signal)
    curve = EurocodeCategory.get_curve('56')
    design_life = 1000
    
    # Create comprehensive assessment
    fig = plot_fatigue_assessment(cycles, curve, design_life=design_life)
    fig.savefig('temp/example5_complete_assessment.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example5_complete_assessment.png")
    print(f"  Design life: {design_life} repetitions")
    print(f"  Curve: {curve.name}")
    plt.close(fig)


def example_6_signal_with_cycles():
    """Example 6: Signal time history with cycles."""
    print("\n" + "=" * 70)
    print("Example 6: Signal with Identified Cycles")
    print("=" * 70)
    
    # Simple periodic signal
    t = np.linspace(0, 4*np.pi, 200)
    signal = 100 + 50 * np.sin(t) + 20 * np.sin(3*t)
    
    cycles = rainflow_count(signal)
    
    # Plot signal
    fig = plot_signal_with_cycles(signal, cycles)
    fig.savefig('temp/example6_signal_cycles.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example6_signal_cycles.png")
    print(f"  Signal length: {len(signal)} points")
    print(f"  Cycles detected: {np.sum(cycles['count']):.0f}")
    plt.close(fig)


def example_7_multiple_curves():
    """Example 7: Compare multiple S-N curves."""
    print("\n" + "=" * 70)
    print("Example 7: Multiple S-N Curves Comparison")
    print("=" * 70)
    
    # Compare several Eurocode categories
    curves_to_compare = ['71', '56', '40', '36']
    
    # Plot comparison
    fig = plot_multiple_sn_curves(curves_to_compare)
    fig.savefig('temp/example7_multiple_curves.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example7_multiple_curves.png")
    print(f"  Curves compared: {', '.join(curves_to_compare)}")
    plt.close(fig)


def example_8_custom_style():
    """Example 8: Custom styling example."""
    print("\n" + "=" * 70)
    print("Example 8: Custom Styling")
    print("=" * 70)
    
    # Set custom style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    np.random.seed(42)
    signal = np.random.randn(800) * 40 + 90
    cycles = rainflow_count(signal)
    
    # Create custom figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    plot_rainflow_cycles(cycles, ax=ax1, show_half_cycles=True)
    ax1.set_facecolor('#f0f0f0')
    
    plot_cycle_histogram(cycles, n_bins=20, ax=ax2)
    ax2.set_facecolor('#f0f0f0')
    
    fig.suptitle('Custom Styled Fatigue Analysis', fontsize=16, fontweight='bold')
    fig.savefig('temp/example8_custom_style.png', dpi=150, bbox_inches='tight')
    print("✓ Figure saved: temp/example8_custom_style.png")
    
    # Reset to default style
    plt.style.use('default')
    plt.close(fig)


def run_all_examples():
    """Run all visualization examples."""
    import os
    os.makedirs('temp', exist_ok=True)
    
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║      OpenRainflow Visualization Examples                         ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    example_1_basic_cycle_plot()
    example_2_cycle_histogram()
    example_3_damage_contribution()
    example_4_sn_curve()
    example_5_complete_assessment()
    example_6_signal_with_cycles()
    example_7_multiple_curves()
    example_8_custom_style()
    
    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)
    print(f"\n📁 Figures saved in: temp/")
    print("\n💡 Tip: Open the PNG files to view the visualizations")


if __name__ == '__main__':
    run_all_examples()

