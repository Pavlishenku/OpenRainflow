"""
Visualization tools for rainflow counting and fatigue analysis.

Provides plotting functions for:
- Cycle histograms
- Damage contribution plots
- S-N curves
- Fatigue assessment visualizations
"""

import numpy as np
from typing import Optional, Tuple
import warnings

try:
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn(
        "Matplotlib not installed. Visualization functions will not work. "
        "Install with: pip install matplotlib"
    )


def _check_matplotlib():
    """Check if matplotlib is available."""
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "Matplotlib is required for visualization. "
            "Install with: pip install matplotlib"
        )


def plot_rainflow_cycles(
    cycles: np.ndarray,
    ax: Optional[plt.Axes] = None,
    show_half_cycles: bool = True,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Plot rainflow cycle distribution (range vs mean stress).
    
    Args:
        cycles: Structured array from rainflow_count
        ax: Matplotlib axes (None to create new figure)
        show_half_cycles: If True, show half-cycles differently
        figsize: Figure size if creating new figure
        
    Returns:
        Matplotlib figure object
        
    Example:
        >>> cycles = rainflow_count(signal)
        >>> fig = plot_rainflow_cycles(cycles)
        >>> plt.show()
    """
    _check_matplotlib()
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Separate full and half cycles
    if show_half_cycles:
        full_cycles = cycles[cycles['count'] == 1.0]
        half_cycles = cycles[cycles['count'] == 0.5]
        
        if len(full_cycles) > 0:
            ax.scatter(
                full_cycles['mean'], full_cycles['range'],
                s=50, alpha=0.6, label='Full cycles', marker='o'
            )
        
        if len(half_cycles) > 0:
            ax.scatter(
                half_cycles['mean'], half_cycles['range'],
                s=30, alpha=0.4, label='Half cycles', marker='x'
            )
    else:
        ax.scatter(cycles['mean'], cycles['range'], s=50, alpha=0.6)
    
    ax.set_xlabel('Mean Stress [MPa]', fontsize=12)
    ax.set_ylabel('Stress Range [MPa]', fontsize=12)
    ax.set_title('Rainflow Cycle Distribution', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    if show_half_cycles:
        ax.legend()
    
    fig.tight_layout()
    return fig


def plot_cycle_histogram(
    cycles: np.ndarray,
    n_bins: int = 20,
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Plot histogram of cycle ranges.
    
    Args:
        cycles: Structured array from rainflow_count
        n_bins: Number of histogram bins
        ax: Matplotlib axes (None to create new figure)
        figsize: Figure size if creating new figure
        
    Returns:
        Matplotlib figure object
    """
    _check_matplotlib()
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Weight by cycle count
    weights = cycles['count']
    
    ax.hist(
        cycles['range'], bins=n_bins, weights=weights,
        alpha=0.7, edgecolor='black', linewidth=1.2
    )
    
    ax.set_xlabel('Stress Range [MPa]', fontsize=12)
    ax.set_ylabel('Cycle Count', fontsize=12)
    ax.set_title('Cycle Range Histogram', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add statistics text
    total_cycles = np.sum(cycles['count'])
    mean_range = np.average(cycles['range'], weights=cycles['count'])
    max_range = np.max(cycles['range'])
    
    stats_text = f'Total cycles: {total_cycles:.0f}\n'
    stats_text += f'Mean range: {mean_range:.1f} MPa\n'
    stats_text += f'Max range: {max_range:.1f} MPa'
    
    ax.text(
        0.98, 0.98, stats_text,
        transform=ax.transAxes,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
        fontsize=10
    )
    
    fig.tight_layout()
    return fig


def plot_damage_contribution(
    cycles: np.ndarray,
    fatigue_curve,
    n_bins: int = 15,
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Plot damage contribution by stress range bins.
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        n_bins: Number of bins for analysis
        ax: Matplotlib axes (None to create new figure)
        figsize: Figure size if creating new figure
        
    Returns:
        Matplotlib figure object
    """
    _check_matplotlib()
    from .damage import damage_contribution_analysis
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Calculate damage contribution
    bins, counts, damage_fractions = damage_contribution_analysis(
        cycles, fatigue_curve, n_bins=n_bins
    )
    
    # Create bar plot
    ax.bar(
        bins, damage_fractions * 100,
        width=bins[1] - bins[0] if len(bins) > 1 else 1,
        alpha=0.7, edgecolor='black', linewidth=1.2,
        color='coral'
    )
    
    ax.set_xlabel('Stress Range [MPa]', fontsize=12)
    ax.set_ylabel('Damage Contribution [%]', fontsize=12)
    ax.set_title(
        f'Damage Contribution by Stress Range\n(Fatigue Curve: {fatigue_curve.name})',
        fontsize=14, fontweight='bold'
    )
    ax.grid(True, alpha=0.3, axis='y')
    
    # Highlight bins contributing > 10%
    for i, (b, df) in enumerate(zip(bins, damage_fractions)):
        if df > 0.1:
            ax.text(
                b, df * 100 + 1,
                f'{df*100:.1f}%',
                ha='center', fontsize=9, fontweight='bold'
            )
    
    fig.tight_layout()
    return fig


def plot_sn_curve(
    fatigue_curve,
    ax: Optional[plt.Axes] = None,
    show_data_points: Optional[np.ndarray] = None,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Plot S-N curve (Wöhler curve).
    
    Args:
        fatigue_curve: FatigueCurve object
        ax: Matplotlib axes (None to create new figure)
        show_data_points: Optional array of stress ranges to highlight
        figsize: Figure size if creating new figure
        
    Returns:
        Matplotlib figure object
    """
    _check_matplotlib()
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    # Generate S-N curve
    N_values = np.logspace(3, 8, 500)
    stress_values = fatigue_curve.get_stress_range(N_values)
    
    # Plot curve
    ax.loglog(N_values, stress_values, 'b-', linewidth=2, label=f'Curve {fatigue_curve.name}')
    
    # Mark reference point
    ax.plot(
        fatigue_curve.N_ref, fatigue_curve.delta_sigma_c,
        'ro', markersize=10, label=f'Reference: Δσ_c = {fatigue_curve.delta_sigma_c} MPa'
    )
    
    # Mark knee point
    if hasattr(fatigue_curve, 'N_knee'):
        stress_at_knee = fatigue_curve.get_stress_range(fatigue_curve.N_knee)
        ax.plot(
            fatigue_curve.N_knee, stress_at_knee,
            'go', markersize=8, label='Knee point'
        )
    
    # Mark CAFL
    if hasattr(fatigue_curve, 'delta_sigma_L'):
        ax.axhline(
            y=fatigue_curve.delta_sigma_L,
            color='r', linestyle='--', linewidth=1.5,
            label=f'CAFL: {fatigue_curve.delta_sigma_L:.1f} MPa'
        )
    
    # Show data points if provided
    if show_data_points is not None:
        N_data = fatigue_curve.get_cycles_to_failure(show_data_points, use_cutoff=False)
        ax.plot(
            N_data, show_data_points,
            'kx', markersize=8, markeredgewidth=2,
            label='Measured cycles'
        )
    
    ax.set_xlabel('Number of Cycles, N', fontsize=12)
    ax.set_ylabel('Stress Range, Δσ [MPa]', fontsize=12)
    ax.set_title(
        f'S-N Curve (Wöhler Curve) - {fatigue_curve.name}',
        fontsize=14, fontweight='bold'
    )
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='upper right')
    
    # Add slope annotation
    slope_text = f'm₁ = {fatigue_curve.m1:.1f}'
    if hasattr(fatigue_curve, 'm2'):
        slope_text += f', m₂ = {fatigue_curve.m2:.1f}'
    ax.text(
        0.02, 0.02, slope_text,
        transform=ax.transAxes,
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3)
    )
    
    fig.tight_layout()
    return fig


def plot_fatigue_assessment(
    cycles: np.ndarray,
    fatigue_curve,
    design_life: float = 1.0,
    figsize: Tuple[float, float] = (14, 10)
) -> plt.Figure:
    """
    Create comprehensive fatigue assessment dashboard.
    
    Creates a 2x2 subplot figure with:
    - Cycle distribution
    - Cycle histogram
    - Damage contribution
    - S-N curve
    
    Args:
        cycles: Structured array from rainflow_count
        fatigue_curve: FatigueCurve object
        design_life: Design life for assessment
        figsize: Figure size
        
    Returns:
        Matplotlib figure object
    """
    _check_matplotlib()
    from .damage import calculate_damage, calculate_life, assess_fatigue_safety
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
    
    # 1. Cycle distribution
    plot_rainflow_cycles(cycles, ax=ax1)
    
    # 2. Cycle histogram
    plot_cycle_histogram(cycles, ax=ax2)
    
    # 3. Damage contribution
    plot_damage_contribution(cycles, fatigue_curve, ax=ax3)
    
    # 4. S-N curve with measured cycles
    plot_sn_curve(fatigue_curve, ax=ax4, show_data_points=cycles['range'])
    
    # Add overall assessment as suptitle
    utilization, status, details = assess_fatigue_safety(
        cycles, fatigue_curve, design_life=design_life
    )
    
    damage = calculate_damage(cycles, fatigue_curve)
    life = calculate_life(cycles, fatigue_curve)
    
    # Color code based on status
    status_color = {'PASS': 'green', 'WARNING': 'orange', 'FAIL': 'red'}
    color = status_color.get(status, 'black')
    
    suptitle = f'Fatigue Assessment - Curve {fatigue_curve.name}\n'
    suptitle += f'Damage: {damage:.6e} | Life: {life:.2e} repetitions | '
    suptitle += f'Utilization: {utilization:.2%} | Status: {status}'
    
    fig.suptitle(suptitle, fontsize=14, fontweight='bold', color=color)
    
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


def plot_signal_with_cycles(
    signal: np.ndarray,
    cycles: np.ndarray,
    max_cycles_to_show: int = 10,
    figsize: Tuple[float, float] = (12, 6)
) -> plt.Figure:
    """
    Plot signal time history with identified cycles highlighted.
    
    Args:
        signal: Original signal array
        cycles: Structured array from rainflow_count
        max_cycles_to_show: Maximum number of cycles to highlight
        figsize: Figure size
        
    Returns:
        Matplotlib figure object
        
    Note:
        This is a simplified visualization showing the largest cycles.
    """
    _check_matplotlib()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot signal
    ax.plot(signal, 'b-', linewidth=1, alpha=0.7, label='Signal')
    
    ax.set_xlabel('Time Index', fontsize=12)
    ax.set_ylabel('Stress [MPa]', fontsize=12)
    ax.set_title('Signal with Rainflow Cycles', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add statistics
    total_cycles = np.sum(cycles['count'])
    stats_text = f'Total cycles: {total_cycles:.0f}\n'
    stats_text += f'Signal length: {len(signal)}\n'
    stats_text += f'Max range: {np.max(cycles["range"]):.1f} MPa'
    
    ax.text(
        0.02, 0.98, stats_text,
        transform=ax.transAxes,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5),
        fontsize=10
    )
    
    fig.tight_layout()
    return fig


def plot_multiple_sn_curves(
    curve_names: list,
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[float, float] = (10, 6)
) -> plt.Figure:
    """
    Plot multiple S-N curves for comparison.
    
    Args:
        curve_names: List of Eurocode category names
        ax: Matplotlib axes (None to create new figure)
        figsize: Figure size if creating new figure
        
    Returns:
        Matplotlib figure object
    """
    _check_matplotlib()
    from .eurocode import EurocodeCategory
    
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()
    
    N_values = np.logspace(3, 8, 300)
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(curve_names)))
    
    for curve_name, color in zip(curve_names, colors):
        curve = EurocodeCategory.get_curve(curve_name)
        stress_values = curve.get_stress_range(N_values)
        
        ax.loglog(
            N_values, stress_values,
            linewidth=2, label=f'Category {curve_name}',
            color=color
        )
        
        # Mark reference point
        ax.plot(
            curve.N_ref, curve.delta_sigma_c,
            'o', markersize=7, color=color
        )
    
    ax.set_xlabel('Number of Cycles, N', fontsize=12)
    ax.set_ylabel('Stress Range, Δσ [MPa]', fontsize=12)
    ax.set_title('Eurocode S-N Curves Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)
    
    fig.tight_layout()
    return fig


# Export main functions
__all__ = [
    'plot_rainflow_cycles',
    'plot_cycle_histogram',
    'plot_damage_contribution',
    'plot_sn_curve',
    'plot_fatigue_assessment',
    'plot_signal_with_cycles',
    'plot_multiple_sn_curves'
]

