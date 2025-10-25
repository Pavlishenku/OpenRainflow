"""
Parallel processing utilities for large-scale fatigue analysis.
"""

import numpy as np
from typing import List, Callable, Optional, Any
import warnings


def process_signals_parallel(
    signals: List[np.ndarray],
    processing_func: Callable,
    n_jobs: int = -1,
    verbose: int = 0,
    **kwargs
) -> List[Any]:
    """
    Process multiple signals in parallel using joblib.
    
    Args:
        signals: List of signal arrays
        processing_func: Function to apply to each signal
        n_jobs: Number of parallel jobs (-1 for all CPUs)
        verbose: Verbosity level (0=silent, 1=basic, 2=detailed)
        **kwargs: Additional arguments passed to processing_func
        
    Returns:
        List of results, one per signal
        
    Example:
        >>> from openrainflow import rainflow_count
        >>> from openrainflow.parallel import process_signals_parallel
        >>> signals = [np.random.randn(10000) for _ in range(100)]
        >>> results = process_signals_parallel(
        ...     signals, rainflow_count, n_jobs=4
        ... )
    """
    try:
        from joblib import Parallel, delayed
    except ImportError:
        warnings.warn(
            "joblib not installed. Falling back to sequential processing. "
            "Install with: pip install joblib"
        )
        return [processing_func(sig, **kwargs) for sig in signals]
    
    results = Parallel(n_jobs=n_jobs, verbose=verbose)(
        delayed(processing_func)(sig, **kwargs) for sig in signals
    )
    
    return results


def batch_damage_calculation(
    cycles_list: List[np.ndarray],
    fatigue_curves: List,
    n_jobs: int = -1,
    **kwargs
) -> np.ndarray:
    """
    Calculate damage for multiple cycle sets in parallel.
    
    Args:
        cycles_list: List of cycle arrays
        fatigue_curves: List of FatigueCurve objects (one per cycles array)
                       or single FatigueCurve for all
        n_jobs: Number of parallel jobs
        **kwargs: Additional arguments for calculate_damage
        
    Returns:
        Array of damage values
    """
    from .damage import calculate_damage
    
    # Handle single curve for all
    if not isinstance(fatigue_curves, list):
        fatigue_curves = [fatigue_curves] * len(cycles_list)
    
    if len(cycles_list) != len(fatigue_curves):
        raise ValueError("cycles_list and fatigue_curves must have same length")
    
    try:
        from joblib import Parallel, delayed
    except ImportError:
        warnings.warn("joblib not installed. Using sequential processing.")
        return np.array([
            calculate_damage(cycles, curve, **kwargs)
            for cycles, curve in zip(cycles_list, fatigue_curves)
        ])
    
    damages = Parallel(n_jobs=n_jobs)(
        delayed(calculate_damage)(cycles, curve, **kwargs)
        for cycles, curve in zip(cycles_list, fatigue_curves)
    )
    
    return np.array(damages)


def parallel_rainflow_batch(
    signal: np.ndarray,
    batch_size: Optional[int] = None,
    n_jobs: int = -1,
    overlap: int = 100
) -> np.ndarray:
    """
    Process very large signal by splitting into batches.
    
    Note: This is an approximation as batch boundaries may affect results.
    For exact results, use regular rainflow_count.
    
    Args:
        signal: Very large signal array
        batch_size: Size of each batch (None for auto)
        n_jobs: Number of parallel jobs
        overlap: Overlap between batches to reduce edge effects
        
    Returns:
        Combined cycles from all batches
    """
    from .rainflow import rainflow_count, combine_cycles
    
    if batch_size is None:
        # Auto-determine batch size (aim for ~1M points per batch)
        batch_size = max(1000000, len(signal) // (n_jobs * 4))
    
    # Create overlapping batches
    batches = []
    start = 0
    while start < len(signal):
        end = min(start + batch_size, len(signal))
        
        # Add overlap except for first batch
        if start > 0:
            start_with_overlap = max(0, start - overlap)
        else:
            start_with_overlap = start
        
        batches.append(signal[start_with_overlap:end])
        start = end
    
    # Process batches in parallel
    cycles_list = process_signals_parallel(
        batches,
        rainflow_count,
        n_jobs=n_jobs
    )
    
    # Combine results
    return combine_cycles(cycles_list)


class ParallelFatigueAnalyzer:
    """
    High-level class for parallel fatigue analysis of multiple signals.
    
    Example:
        >>> analyzer = ParallelFatigueAnalyzer(n_jobs=4)
        >>> analyzer.add_signals(signals)
        >>> analyzer.set_fatigue_curve('71')
        >>> results = analyzer.analyze()
        >>> print(results['damages'])
    """
    
    def __init__(self, n_jobs: int = -1, verbose: int = 0):
        """
        Initialize analyzer.
        
        Args:
            n_jobs: Number of parallel jobs
            verbose: Verbosity level
        """
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.signals = []
        self.fatigue_curve = None
        self.cycles_list = None
        
    def add_signals(self, signals: List[np.ndarray]):
        """Add signals to analyze."""
        self.signals.extend(signals)
        
    def set_fatigue_curve(self, curve):
        """
        Set fatigue curve for analysis.
        
        Args:
            curve: FatigueCurve object or Eurocode category name (str)
        """
        if isinstance(curve, str):
            from .eurocode import EurocodeCategory
            self.fatigue_curve = EurocodeCategory.get_curve(curve)
        else:
            self.fatigue_curve = curve
    
    def count_cycles(self, **kwargs) -> List[np.ndarray]:
        """
        Perform rainflow counting on all signals in parallel.
        
        Args:
            **kwargs: Arguments passed to rainflow_count
            
        Returns:
            List of cycle arrays
        """
        from .rainflow import rainflow_count
        
        self.cycles_list = process_signals_parallel(
            self.signals,
            rainflow_count,
            n_jobs=self.n_jobs,
            verbose=self.verbose,
            **kwargs
        )
        
        return self.cycles_list
    
    def calculate_damages(self, **kwargs) -> np.ndarray:
        """
        Calculate damage for all signals.
        
        Args:
            **kwargs: Arguments passed to calculate_damage
            
        Returns:
            Array of damage values
        """
        if self.cycles_list is None:
            self.count_cycles()
        
        if self.fatigue_curve is None:
            raise ValueError("Fatigue curve not set. Use set_fatigue_curve()")
        
        return batch_damage_calculation(
            self.cycles_list,
            self.fatigue_curve,
            n_jobs=self.n_jobs,
            **kwargs
        )
    
    def analyze(
        self,
        design_life: float = 1.0,
        **kwargs
    ) -> dict:
        """
        Perform complete fatigue analysis.
        
        Args:
            design_life: Design life for assessment
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with results
        """
        from .damage import calculate_life
        
        # Count cycles
        if self.cycles_list is None:
            self.count_cycles()
        
        # Calculate damages
        damages = self.calculate_damages(**kwargs)
        
        # Calculate lives
        lives = np.array([
            calculate_life(cycles, self.fatigue_curve, **kwargs)
            for cycles in self.cycles_list
        ])
        
        # Utilization
        utilizations = design_life / lives
        
        results = {
            'n_signals': len(self.signals),
            'cycles_list': self.cycles_list,
            'damages': damages,
            'lives': lives,
            'utilizations': utilizations,
            'design_life': design_life,
            'max_damage': np.max(damages),
            'min_life': np.min(lives),
            'max_utilization': np.max(utilizations),
        }
        
        return results
    
    def get_summary(self) -> str:
        """Get summary statistics as formatted string."""
        if self.cycles_list is None:
            return "No analysis performed yet."
        
        results = self.analyze()
        
        summary = f"""
Parallel Fatigue Analysis Summary
{'=' * 50}
Number of signals:     {results['n_signals']}
Fatigue curve:         {self.fatigue_curve.name}

Damage Statistics:
  Maximum:             {results['max_damage']:.6e}
  Mean:                {np.mean(results['damages']):.6e}
  Std:                 {np.std(results['damages']):.6e}

Life Statistics:
  Minimum:             {results['min_life']:.2e} repetitions
  Median:              {np.median(results['lives']):.2e} repetitions

Utilization (for design life = {results['design_life']}):
  Maximum:             {results['max_utilization']:.2%}
  Mean:                {np.mean(results['utilizations']):.2%}
{'=' * 50}
"""
        return summary

