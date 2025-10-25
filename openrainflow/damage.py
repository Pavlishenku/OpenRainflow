"""
Fatigue damage calculation using Miner's linear damage accumulation rule.

Implements Palmgren-Miner cumulative damage theory:
    D = Σ(n_i / N_i)

where:
    D: Total damage
    n_i: Number of cycles at stress range i
    N_i: Number of cycles to failure at stress range i
"""

import numpy as np
from typing import Union, Optional, Tuple
from numba import njit
import warnings

from .eurocode import FatigueCurve


def calculate_damage(
    cycles: np.ndarray,
    fatigue_curve: FatigueCurve,
    use_cutoff: bool = True,
    partial_safety_factor: float = 1.0
) -> float:
    """
    Calculate cumulative fatigue damage using Miner's rule.
    
    Args:
        cycles: Structured array from rainflow_count with fields:
                'range', 'mean', 'count'
        fatigue_curve: FatigueCurve object defining S-N relationship
        use_cutoff: If True, stress ranges below CAFL cause no damage
        partial_safety_factor: Partial safety factor for fatigue (γ_Mf)
                              Applied to stress ranges: Δσ_Ed = γ_Mf * Δσ
                              
    Returns:
        D: Total cumulative damage (failure occurs at D ≈ 1.0)
        
    Example:
        >>> from openrainflow import rainflow_count, calculate_damage
        >>> from openrainflow.eurocode import EurocodeCategory
        >>> import numpy as np
        >>> signal = np.random.randn(1000) * 50 + 100
        >>> cycles = rainflow_count(signal)
        >>> curve = EurocodeCategory.get_curve('71')
        >>> damage = calculate_damage(cycles, curve)
        >>> print(f"Damage: {damage:.6f}")
    """
    if len(cycles) == 0:
        return 0.0
    
    # Extract stress ranges and cycle counts
    stress_ranges = cycles['range'] * partial_safety_factor
    cycle_counts = cycles['count']
    
    # Get number of cycles to failure for each stress range
    N_f = fatigue_curve.get_cycles_to_failure(stress_ranges, use_cutoff=use_cutoff)
    
    # Calculate damage contribution from each cycle
    # Handle infinite life (below CAFL)
    damage_increments = np.where(
        np.isinf(N_f),
        0.0,
        cycle_counts / N_f
    )
    
    # Sum total damage
    total_damage = np.sum(damage_increments)
    
    return total_damage


def calculate_life(
    cycles: np.ndarray,
    fatigue_curve: FatigueCurve,
    use_cutoff: bool = True,
    partial_safety_factor: float = 1.0,
    failure_damage: float = 1.0
) -> float:
    """
    Calculate fatigue life (number of repetitions until failure).
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        use_cutoff: If True, stress ranges below CAFL cause no damage
        partial_safety_factor: Partial safety factor for fatigue
        failure_damage: Damage threshold for failure (default: 1.0)
        
    Returns:
        life: Number of repetitions of the load history until failure
              Returns inf if damage per cycle is zero
              
    Example:
        >>> life = calculate_life(cycles, curve)
        >>> print(f"Expected life: {life:.2e} repetitions")
    """
    damage_per_cycle = calculate_damage(
        cycles, 
        fatigue_curve, 
        use_cutoff, 
        partial_safety_factor
    )
    
    if damage_per_cycle == 0:
        return np.inf
    
    return failure_damage / damage_per_cycle


@njit(cache=True)
def _damage_from_histogram(
    stress_ranges: np.ndarray,
    cycle_counts: np.ndarray,
    N_f: np.ndarray
) -> float:
    """
    JIT-compiled core function for damage calculation from histogram.
    
    Args:
        stress_ranges: Array of stress range bin centers
        cycle_counts: Array of cycle counts in each bin
        N_f: Array of cycles to failure for each stress range
        
    Returns:
        Total damage
    """
    total_damage = 0.0
    
    for i in range(len(stress_ranges)):
        if cycle_counts[i] > 0 and not np.isinf(N_f[i]):
            total_damage += cycle_counts[i] / N_f[i]
    
    return total_damage


def calculate_damage_from_histogram(
    stress_ranges: np.ndarray,
    cycle_counts: np.ndarray,
    fatigue_curve: FatigueCurve,
    use_cutoff: bool = True,
    partial_safety_factor: float = 1.0
) -> float:
    """
    Calculate damage from a stress range histogram (binned data).
    
    This is useful when you have pre-binned cycle counting data.
    
    Args:
        stress_ranges: Array of stress range values (bin centers)
        cycle_counts: Array of cycle counts for each stress range
        fatigue_curve: FatigueCurve object
        use_cutoff: If True, stress ranges below CAFL cause no damage
        partial_safety_factor: Partial safety factor for fatigue
        
    Returns:
        Total cumulative damage
        
    Example:
        >>> stress_ranges = np.array([50, 75, 100, 125, 150])
        >>> cycle_counts = np.array([1000, 500, 200, 50, 10])
        >>> damage = calculate_damage_from_histogram(
        ...     stress_ranges, cycle_counts, curve
        ... )
    """
    if len(stress_ranges) != len(cycle_counts):
        raise ValueError("stress_ranges and cycle_counts must have same length")
    
    # Apply safety factor
    stress_ranges_factored = stress_ranges * partial_safety_factor
    
    # Get cycles to failure
    N_f = fatigue_curve.get_cycles_to_failure(
        stress_ranges_factored, 
        use_cutoff=use_cutoff
    )
    
    # Calculate damage
    return _damage_from_histogram(stress_ranges_factored, cycle_counts, N_f)


def calculate_equivalent_stress(
    cycles: np.ndarray,
    fatigue_curve: FatigueCurve,
    N_eq: float = 2e6
) -> float:
    """
    Calculate equivalent constant amplitude stress range.
    
    The equivalent stress is a single stress range that would cause
    the same damage in N_eq cycles as the actual variable amplitude
    loading.
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        N_eq: Equivalent number of cycles (default: 2E6)
        
    Returns:
        delta_sigma_eq: Equivalent stress range [MPa]
        
    Note:
        For slope m, the equivalent stress is calculated as:
        Δσ_eq = (Σ n_i * Δσ_i^m / N_eq)^(1/m)
    """
    if len(cycles) == 0:
        return 0.0
    
    stress_ranges = cycles['range']
    cycle_counts = cycles['count']
    
    # Use appropriate slope based on stress level
    # For simplicity, use m1 (can be refined for mixed ranges)
    m = fatigue_curve.m1
    
    # Calculate equivalent stress
    sum_damage_term = np.sum(cycle_counts * (stress_ranges ** m))
    delta_sigma_eq = (sum_damage_term / N_eq) ** (1.0 / m)
    
    return delta_sigma_eq


def assess_fatigue_safety(
    cycles: np.ndarray,
    fatigue_curve: FatigueCurve,
    design_life: float = 1.0,
    partial_safety_factor: float = 1.0,
    use_cutoff: bool = True
) -> Tuple[float, str, dict]:
    """
    Assess fatigue safety and provide detailed evaluation.
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        design_life: Required number of repetitions of load history
        partial_safety_factor: Partial safety factor for fatigue
        use_cutoff: If True, stress ranges below CAFL cause no damage
        
    Returns:
        utilization: Fatigue utilization ratio (should be < 1.0)
        assessment: Text assessment ("PASS", "FAIL", or "WARNING")
        details: Dictionary with detailed results
        
    Example:
        >>> util, status, details = assess_fatigue_safety(
        ...     cycles, curve, design_life=50
        ... )
        >>> print(f"Status: {status}, Utilization: {util:.2%}")
    """
    # Calculate damage for design life
    damage_per_cycle = calculate_damage(
        cycles, 
        fatigue_curve, 
        use_cutoff, 
        partial_safety_factor
    )
    
    total_damage = damage_per_cycle * design_life
    
    # Calculate actual life
    if damage_per_cycle > 0:
        actual_life = 1.0 / damage_per_cycle
    else:
        actual_life = np.inf
    
    # Utilization ratio
    if actual_life == np.inf:
        utilization = 0.0
    else:
        utilization = design_life / actual_life
    
    # Assessment
    if utilization < 0.8:
        assessment = "PASS"
    elif utilization < 1.0:
        assessment = "WARNING"
    else:
        assessment = "FAIL"
    
    # Equivalent stress
    delta_sigma_eq = calculate_equivalent_stress(cycles, fatigue_curve)
    
    # Detailed results
    details = {
        'damage_per_cycle': damage_per_cycle,
        'total_damage': total_damage,
        'actual_life': actual_life,
        'design_life': design_life,
        'reserve_factor': 1.0 / utilization if utilization > 0 else np.inf,
        'equivalent_stress': delta_sigma_eq,
        'total_cycles': np.sum(cycles['count']),
        'max_stress_range': np.max(cycles['range']) if len(cycles) > 0 else 0.0,
        'partial_safety_factor': partial_safety_factor,
        'fatigue_curve': fatigue_curve.name,
    }
    
    return utilization, assessment, details


def damage_contribution_analysis(
    cycles: np.ndarray,
    fatigue_curve: FatigueCurve,
    n_bins: int = 10,
    partial_safety_factor: float = 1.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Analyze damage contribution from different stress range bins.
    
    Useful for identifying which stress ranges contribute most to damage.
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        n_bins: Number of bins for stress ranges
        partial_safety_factor: Partial safety factor
        
    Returns:
        bin_centers: Center values of stress range bins
        cycle_counts: Number of cycles in each bin
        damage_fractions: Fraction of total damage from each bin
        
    Example:
        >>> bins, counts, damage_frac = damage_contribution_analysis(
        ...     cycles, curve, n_bins=20
        ... )
        >>> # Plot damage distribution
        >>> import matplotlib.pyplot as plt
        >>> plt.bar(bins, damage_frac)
        >>> plt.xlabel('Stress Range [MPa]')
        >>> plt.ylabel('Damage Fraction')
    """
    if len(cycles) == 0:
        return np.array([]), np.array([]), np.array([])
    
    stress_ranges = cycles['range']
    cycle_counts = cycles['count']
    
    # Create bins
    range_min = stress_ranges.min()
    range_max = stress_ranges.max()
    bin_edges = np.linspace(range_min, range_max, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Assign cycles to bins
    bin_indices = np.digitize(stress_ranges, bin_edges) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    # Accumulate cycles and damage in each bin
    binned_counts = np.zeros(n_bins)
    binned_damage = np.zeros(n_bins)
    
    for i, (stress, count) in enumerate(zip(stress_ranges, cycle_counts)):
        bin_idx = bin_indices[i]
        binned_counts[bin_idx] += count
        
        # Calculate damage for this cycle
        N_f = fatigue_curve.get_cycles_to_failure(
            stress * partial_safety_factor
        )
        if not np.isinf(N_f):
            binned_damage[bin_idx] += count / N_f
    
    # Calculate damage fractions
    total_damage = np.sum(binned_damage)
    if total_damage > 0:
        damage_fractions = binned_damage / total_damage
    else:
        damage_fractions = np.zeros(n_bins)
    
    return bin_centers, binned_counts, damage_fractions


def print_damage_report(
    cycles: np.ndarray,
    fatigue_curve: FatigueCurve,
    design_life: float = 1.0,
    partial_safety_factor: float = 1.0
):
    """
    Print a formatted fatigue damage assessment report.
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        design_life: Required number of repetitions
        partial_safety_factor: Partial safety factor
    """
    util, status, details = assess_fatigue_safety(
        cycles, fatigue_curve, design_life, partial_safety_factor
    )
    
    print("=" * 70)
    print("FATIGUE DAMAGE ASSESSMENT REPORT")
    print("=" * 70)
    print(f"\nFatigue Curve: {fatigue_curve.name}")
    print(f"  Δσ_c at 2E6:  {fatigue_curve.delta_sigma_c:.1f} MPa")
    print(f"  Slopes:       m1={fatigue_curve.m1}, m2={fatigue_curve.m2}")
    print(f"  CAFL:         {fatigue_curve.delta_sigma_L:.2f} MPa")
    
    print(f"\nLoad History:")
    print(f"  Total cycles:       {details['total_cycles']:.1f}")
    print(f"  Max stress range:   {details['max_stress_range']:.2f} MPa")
    print(f"  Equiv. stress (2M): {details['equivalent_stress']:.2f} MPa")
    
    print(f"\nDamage Analysis:")
    print(f"  Design life:        {design_life:.2e} repetitions")
    print(f"  Damage per cycle:   {details['damage_per_cycle']:.6e}")
    print(f"  Total damage:       {details['total_damage']:.6f}")
    print(f"  Actual life:        {details['actual_life']:.2e} repetitions")
    
    print(f"\nSafety Assessment:")
    print(f"  Utilization:        {util:.2%}")
    print(f"  Reserve factor:     {details['reserve_factor']:.2f}")
    print(f"  Safety factor:      {partial_safety_factor:.2f}")
    print(f"  Status:             {status}")
    
    if status == "FAIL":
        print("\n⚠ WARNING: FATIGUE FAILURE EXPECTED!")
    elif status == "WARNING":
        print("\n⚠ WARNING: High utilization - consider increasing safety margin")
    else:
        print("\n✓ Fatigue assessment PASSED")
    
    print("=" * 70)

