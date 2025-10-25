"""
Eurocode fatigue curves (EN 1993-1-9:2005).

Implementation of S-N fatigue curves for structural steel according to
Eurocode 3 Part 1-9.
"""

import numpy as np
from typing import Optional, Dict, Union
from dataclasses import dataclass


# Eurocode detail categories with characteristic fatigue strength at 2 million cycles
# Values in MPa (N/mm²)
EUROCODE_CATEGORIES = {
    '160': 160.0,
    '140': 140.0,
    '125': 125.0,
    '112': 112.0,
    '100': 100.0,
    '90': 90.0,
    '80': 80.0,
    '71': 71.0,
    '63': 63.0,
    '56': 56.0,
    '50': 50.0,
    '45': 45.0,
    '40': 40.0,
    '36': 36.0,
}


@dataclass
class FatigueCurve:
    """
    S-N fatigue curve representation.
    
    The curve follows the equation:
        N = C / (Δσ^m)
    
    where:
        N: Number of cycles to failure
        Δσ: Stress range
        C: Fatigue strength coefficient
        m: Slope of S-N curve (typically 3 for steel in normal range, 5 for high cycle)
    
    Attributes:
        name: Curve identifier (e.g., '36', '71', '160')
        delta_sigma_c: Characteristic fatigue strength at 2E6 cycles [MPa]
        m1: Slope for normal range (default: 3)
        m2: Slope for high-cycle range (default: 5)
        N_knee: Transition point between slopes (default: 5E6 cycles)
        delta_sigma_L: Constant amplitude fatigue limit (CAFL) [MPa]
        N_cutoff: Cut-off limit (default: 1E8 cycles)
    """
    name: str
    delta_sigma_c: float
    m1: float = 3.0
    m2: float = 5.0
    N_knee: float = 5e6
    N_cutoff: float = 1e8
    delta_sigma_L: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived parameters."""
        # Reference point: 2 million cycles
        self.N_ref = 2e6
        
        # Calculate fatigue strength coefficient for normal range
        self.C1 = self.N_ref * (self.delta_sigma_c ** self.m1)
        
        # Calculate stress range at knee point
        self.delta_sigma_knee = (self.C1 / self.N_knee) ** (1 / self.m1)
        
        # Calculate fatigue strength coefficient for high-cycle range
        self.C2 = self.N_knee * (self.delta_sigma_knee ** self.m2)
        
        # Calculate constant amplitude fatigue limit if not provided
        if self.delta_sigma_L is None:
            self.delta_sigma_L = (self.C2 / self.N_cutoff) ** (1 / self.m2)
    
    def get_cycles_to_failure(
        self,
        delta_sigma: Union[float, np.ndarray],
        use_cutoff: bool = True
    ) -> Union[float, np.ndarray]:
        """
        Calculate number of cycles to failure for given stress range(s).
        
        Args:
            delta_sigma: Stress range [MPa] (scalar or array)
            use_cutoff: If True, cycles below CAFL return infinite life
            
        Returns:
            N: Number of cycles to failure
        """
        is_scalar = np.isscalar(delta_sigma)
        delta_sigma = np.atleast_1d(delta_sigma)
        
        N = np.zeros_like(delta_sigma, dtype=np.float64)
        
        # Apply cutoff (infinite life)
        if use_cutoff:
            below_cafl = delta_sigma < self.delta_sigma_L
            N[below_cafl] = np.inf
            above_cafl = ~below_cafl
        else:
            above_cafl = np.ones_like(delta_sigma, dtype=bool)
        
        # Region 1: High stress, slope m1
        in_region1 = above_cafl & (delta_sigma >= self.delta_sigma_knee)
        N[in_region1] = self.C1 / (delta_sigma[in_region1] ** self.m1)
        
        # Region 2: Low stress, slope m2
        in_region2 = above_cafl & (delta_sigma < self.delta_sigma_knee) & \
                     (delta_sigma >= self.delta_sigma_L)
        N[in_region2] = self.C2 / (delta_sigma[in_region2] ** self.m2)
        
        return N[0] if is_scalar else N
    
    def get_stress_range(self, N: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Calculate stress range for given number of cycles (inverse S-N curve).
        
        Args:
            N: Number of cycles
            
        Returns:
            delta_sigma: Stress range [MPa]
        """
        is_scalar = np.isscalar(N)
        N = np.atleast_1d(N)
        
        delta_sigma = np.zeros_like(N, dtype=np.float64)
        
        # Region 1: N < N_knee
        in_region1 = N < self.N_knee
        delta_sigma[in_region1] = (self.C1 / N[in_region1]) ** (1 / self.m1)
        
        # Region 2: N_knee <= N <= N_cutoff
        in_region2 = (N >= self.N_knee) & (N <= self.N_cutoff)
        delta_sigma[in_region2] = (self.C2 / N[in_region2]) ** (1 / self.m2)
        
        # Region 3: N > N_cutoff (below CAFL)
        beyond_cutoff = N > self.N_cutoff
        delta_sigma[beyond_cutoff] = self.delta_sigma_L
        
        return delta_sigma[0] if is_scalar else delta_sigma
    
    def get_damage_per_cycle(
        self,
        delta_sigma: Union[float, np.ndarray],
        use_cutoff: bool = True
    ) -> Union[float, np.ndarray]:
        """
        Calculate damage per cycle for given stress range(s).
        
        Damage per cycle = 1 / N
        
        Args:
            delta_sigma: Stress range [MPa]
            use_cutoff: If True, stress below CAFL causes no damage
            
        Returns:
            damage: Damage per cycle (0 to 1)
        """
        N = self.get_cycles_to_failure(delta_sigma, use_cutoff=use_cutoff)
        
        # Handle infinite life
        damage = np.where(np.isinf(N), 0.0, 1.0 / N)
        
        return damage
    
    def __repr__(self) -> str:
        return (
            f"FatigueCurve(name='{self.name}', "
            f"Δσ_c={self.delta_sigma_c:.1f} MPa, "
            f"m1={self.m1}, m2={self.m2}, "
            f"CAFL={self.delta_sigma_L:.2f} MPa)"
        )


class EurocodeCategory:
    """
    Factory class for Eurocode fatigue curves.
    
    Provides easy access to standard Eurocode detail categories.
    """
    
    _curves_cache: Dict[str, FatigueCurve] = {}
    
    @classmethod
    def get_curve(
        cls,
        category: str,
        m1: float = 3.0,
        m2: float = 5.0,
        N_knee: float = 5e6,
        N_cutoff: float = 1e8
    ) -> FatigueCurve:
        """
        Get a fatigue curve for a given Eurocode category.
        
        Args:
            category: Eurocode detail category ('160', '125', ..., '36')
            m1: Slope for normal range (default: 3)
            m2: Slope for high-cycle range (default: 5)
            N_knee: Transition point between slopes (default: 5E6)
            N_cutoff: Cut-off limit (default: 1E8)
            
        Returns:
            FatigueCurve object
            
        Raises:
            ValueError: If category is not valid
            
        Example:
            >>> curve = EurocodeCategory.get_curve('71')
            >>> N = curve.get_cycles_to_failure(100.0)
        """
        if category not in EUROCODE_CATEGORIES:
            valid = ', '.join(EUROCODE_CATEGORIES.keys())
            raise ValueError(
                f"Invalid Eurocode category '{category}'. "
                f"Valid categories: {valid}"
            )
        
        cache_key = f"{category}_{m1}_{m2}_{N_knee}_{N_cutoff}"
        
        if cache_key not in cls._curves_cache:
            delta_sigma_c = EUROCODE_CATEGORIES[category]
            curve = FatigueCurve(
                name=category,
                delta_sigma_c=delta_sigma_c,
                m1=m1,
                m2=m2,
                N_knee=N_knee,
                N_cutoff=N_cutoff
            )
            cls._curves_cache[cache_key] = curve
        
        return cls._curves_cache[cache_key]
    
    @classmethod
    def list_categories(cls) -> list:
        """
        List all available Eurocode categories.
        
        Returns:
            List of category names
        """
        return sorted(EUROCODE_CATEGORIES.keys(), 
                     key=lambda x: EUROCODE_CATEGORIES[x], 
                     reverse=True)
    
    @classmethod
    def get_category_strength(cls, category: str) -> float:
        """
        Get the characteristic fatigue strength for a category.
        
        Args:
            category: Eurocode detail category
            
        Returns:
            Characteristic fatigue strength at 2E6 cycles [MPa]
        """
        if category not in EUROCODE_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        return EUROCODE_CATEGORIES[category]


def create_custom_curve(
    name: str,
    delta_sigma_c: float,
    m1: float = 3.0,
    m2: float = 5.0,
    N_ref: float = 2e6,
    N_knee: float = 5e6,
    N_cutoff: float = 1e8,
    delta_sigma_L: Optional[float] = None
) -> FatigueCurve:
    """
    Create a custom fatigue curve with specified parameters.
    
    Args:
        name: Curve identifier
        delta_sigma_c: Characteristic fatigue strength at N_ref cycles [MPa]
        m1: Slope for normal range
        m2: Slope for high-cycle range
        N_ref: Reference number of cycles (default: 2E6)
        N_knee: Transition point between slopes
        N_cutoff: Cut-off limit
        delta_sigma_L: Constant amplitude fatigue limit [MPa]
        
    Returns:
        FatigueCurve object
        
    Example:
        >>> curve = create_custom_curve('Custom', delta_sigma_c=85.0, m1=3.5)
    """
    # Adjust delta_sigma_c if N_ref is not 2E6
    if N_ref != 2e6:
        # Convert to equivalent value at 2E6 cycles
        delta_sigma_c_2M = delta_sigma_c * (N_ref / 2e6) ** (1 / m1)
    else:
        delta_sigma_c_2M = delta_sigma_c
    
    return FatigueCurve(
        name=name,
        delta_sigma_c=delta_sigma_c_2M,
        m1=m1,
        m2=m2,
        N_knee=N_knee,
        N_cutoff=N_cutoff,
        delta_sigma_L=delta_sigma_L
    )


def plot_sn_curve(
    curves: Union[FatigueCurve, list],
    N_range: tuple = (1e3, 1e9),
    show_knee: bool = True,
    show_cafl: bool = True
):
    """
    Plot S-N curve(s) for visualization.
    
    Note: Requires matplotlib (not a required dependency).
    
    Args:
        curves: Single FatigueCurve or list of curves
        N_range: Tuple of (min_N, max_N) for plot range
        show_knee: If True, mark the knee point
        show_cafl: If True, mark the CAFL
        
    Example:
        >>> import matplotlib.pyplot as plt
        >>> curve = EurocodeCategory.get_curve('71')
        >>> plot_sn_curve(curve)
        >>> plt.show()
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for plotting. "
            "Install with: pip install matplotlib"
        )
    
    if isinstance(curves, FatigueCurve):
        curves = [curves]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    N_plot = np.logspace(np.log10(N_range[0]), np.log10(N_range[1]), 1000)
    
    for curve in curves:
        delta_sigma_plot = curve.get_stress_range(N_plot)
        ax.loglog(N_plot, delta_sigma_plot, label=f'Category {curve.name}', linewidth=2)
        
        if show_knee:
            ax.plot(curve.N_knee, curve.delta_sigma_knee, 'o', 
                   markersize=6, label=f'Knee ({curve.name})')
        
        if show_cafl:
            ax.axhline(curve.delta_sigma_L, linestyle='--', alpha=0.5,
                      label=f'CAFL {curve.name} ({curve.delta_sigma_L:.1f} MPa)')
    
    ax.set_xlabel('Number of Cycles, N', fontsize=12)
    ax.set_ylabel('Stress Range, Δσ [MPa]', fontsize=12)
    ax.set_title('Eurocode S-N Fatigue Curves', fontsize=14, fontweight='bold')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(fontsize=10)
    
    return fig, ax

