"""
Rainflow cycle counting algorithm.

Implementation based on ASTM E1049-85 standard with optimizations using Numba JIT.
"""

import numpy as np
from numba import njit
from typing import Tuple, Optional
import warnings


@njit(cache=True)
def _find_reversals(signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Identify turning points (peaks and valleys) in a signal.
    
    Args:
        signal: Input time series data
        
    Returns:
        reversals: Array of reversal values
        indices: Array of indices where reversals occur
    """
    n = len(signal)
    if n < 3:
        return signal.copy(), np.arange(n)
    
    # Preallocate maximum possible size
    reversals = np.empty(n, dtype=signal.dtype)
    indices = np.empty(n, dtype=np.int64)
    
    # First point is always a reversal
    reversals[0] = signal[0]
    indices[0] = 0
    count = 1
    
    i = 1
    while i < n - 1:
        # Check if this is a peak or valley
        if (signal[i] >= signal[i-1] and signal[i] > signal[i+1]) or \
           (signal[i] <= signal[i-1] and signal[i] < signal[i+1]):
            reversals[count] = signal[i]
            indices[count] = i
            count += 1
        i += 1
    
    # Last point is always a reversal
    reversals[count] = signal[-1]
    indices[count] = n - 1
    count += 1
    
    return reversals[:count], indices[:count]


@njit(cache=True)
def _rainflow_core(reversals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Core rainflow counting algorithm using the three-point method.
    
    This is the optimized JIT-compiled core function.
    
    Args:
        reversals: Array of reversal points (peaks and valleys)
        
    Returns:
        ranges: Array of cycle ranges (stress range)
        means: Array of cycle means (mean stress)
        counts: Array of cycle counts (0.5 for half-cycles, 1.0 for full cycles)
    """
    n = len(reversals)
    if n < 2:
        return np.empty(0), np.empty(0), np.empty(0)
    
    # Stack for processing
    stack = np.empty(n, dtype=reversals.dtype)
    stack_ptr = 0
    
    # Results storage (maximum possible size is n//2 full cycles + n//2 half cycles)
    max_cycles = n
    ranges = np.empty(max_cycles, dtype=reversals.dtype)
    means = np.empty(max_cycles, dtype=reversals.dtype)
    counts = np.empty(max_cycles, dtype=np.float64)
    cycle_count = 0
    
    for reversal in reversals:
        stack[stack_ptr] = reversal
        stack_ptr += 1
        
        # Try to extract cycles
        while stack_ptr >= 3:
            # Get last three points
            Y = stack[stack_ptr - 1]
            X = stack[stack_ptr - 2]
            W = stack[stack_ptr - 3]
            
            # Calculate ranges
            range_XY = abs(Y - X)
            
            if stack_ptr >= 4:
                V = stack[stack_ptr - 4]
                range_WX = abs(X - W)
                range_VW = abs(W - V)
                
                # Check if X-Y can be extracted as a full cycle
                if range_XY <= range_VW and range_WX <= range_VW:
                    # Extract full cycle X-Y
                    cycle_range = range_XY
                    cycle_mean = (X + Y) / 2.0
                    
                    ranges[cycle_count] = cycle_range
                    means[cycle_count] = cycle_mean
                    counts[cycle_count] = 1.0  # Full cycle
                    cycle_count += 1
                    
                    # Remove X and Y from stack
                    stack[stack_ptr - 2] = stack[stack_ptr - 1]
                    stack_ptr -= 2
                    continue
            
            # Check if we have at least 3 points and X-Y >= W-X
            if stack_ptr >= 3:
                range_WX = abs(X - W)
                if range_XY >= range_WX:
                    # Extract full cycle W-X
                    cycle_range = range_WX
                    cycle_mean = (W + X) / 2.0
                    
                    ranges[cycle_count] = cycle_range
                    means[cycle_count] = cycle_mean
                    counts[cycle_count] = 1.0  # Full cycle
                    cycle_count += 1
                    
                    # Remove W and X from stack
                    stack[stack_ptr - 3] = stack[stack_ptr - 1]
                    stack_ptr -= 2
                    continue
            
            break
    
    # Extract remaining half-cycles from stack
    for i in range(stack_ptr - 1):
        cycle_range = abs(stack[i + 1] - stack[i])
        cycle_mean = (stack[i] + stack[i + 1]) / 2.0
        
        ranges[cycle_count] = cycle_range
        means[cycle_count] = cycle_mean
        counts[cycle_count] = 0.5  # Half cycle
        cycle_count += 1
    
    return ranges[:cycle_count], means[:cycle_count], counts[:cycle_count]


def rainflow_count(
    signal: np.ndarray,
    remove_zeros: bool = True,
    gate: Optional[float] = None
) -> np.ndarray:
    """
    Perform rainflow cycle counting on a time series signal.
    
    This function implements the ASTM E1049-85 rainflow counting algorithm
    with Numba JIT compilation for high performance.
    
    Args:
        signal: Input time series data (stress/strain history)
        remove_zeros: If True, remove zero-range cycles from results
        gate: Optional minimum range threshold. Cycles below this are ignored.
        
    Returns:
        cycles: Structured numpy array with fields:
            - 'range': Cycle range (peak-to-valley)
            - 'mean': Cycle mean value
            - 'count': Cycle count (0.5 for half-cycles, 1.0 for full cycles)
            
    Example:
        >>> import numpy as np
        >>> from openrainflow import rainflow_count
        >>> signal = np.array([0, 1, 0, 2, 0, 3, 0])
        >>> cycles = rainflow_count(signal)
        >>> print(cycles)
    """
    if not isinstance(signal, np.ndarray):
        signal = np.asarray(signal, dtype=np.float64)
    elif signal.dtype not in (np.float32, np.float64):
        signal = signal.astype(np.float64)
    
    if len(signal) < 2:
        warnings.warn("Signal too short for rainflow counting (need at least 2 points)")
        return np.empty(0, dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
    
    # Find reversal points
    reversals, _ = _find_reversals(signal)
    
    # Apply rainflow algorithm
    ranges, means, counts = _rainflow_core(reversals)
    
    # Apply gating if specified
    if gate is not None and gate > 0:
        mask = ranges >= gate
        ranges = ranges[mask]
        means = means[mask]
        counts = counts[mask]
    
    # Remove zero-range cycles if requested
    if remove_zeros:
        mask = ranges > 0
        ranges = ranges[mask]
        means = means[mask]
        counts = counts[mask]
    
    # Create structured array
    cycles = np.empty(len(ranges), dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
    cycles['range'] = ranges
    cycles['mean'] = means
    cycles['count'] = counts
    
    return cycles


def rainflow_count_parallel(
    signals: list,
    remove_zeros: bool = True,
    gate: Optional[float] = None,
    n_jobs: int = -1
) -> list:
    """
    Perform rainflow counting on multiple signals in parallel.
    
    Args:
        signals: List of time series arrays
        remove_zeros: If True, remove zero-range cycles from results
        gate: Optional minimum range threshold
        n_jobs: Number of parallel jobs (-1 for all CPUs)
        
    Returns:
        cycles_list: List of cycle arrays, one per input signal
        
    Example:
        >>> signals = [np.random.randn(1000) for _ in range(10)]
        >>> cycles_list = rainflow_count_parallel(signals, n_jobs=4)
    """
    try:
        from joblib import Parallel, delayed
    except ImportError:
        warnings.warn(
            "joblib not installed. Falling back to sequential processing. "
            "Install with: pip install joblib"
        )
        return [rainflow_count(sig, remove_zeros, gate) for sig in signals]
    
    results = Parallel(n_jobs=n_jobs)(
        delayed(rainflow_count)(sig, remove_zeros, gate) 
        for sig in signals
    )
    
    return results


def combine_cycles(cycles_list: list) -> np.ndarray:
    """
    Combine multiple cycle arrays into a single array.
    
    Args:
        cycles_list: List of cycle arrays from rainflow_count
        
    Returns:
        combined: Single combined cycle array
    """
    if not cycles_list:
        return np.empty(0, dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
    
    return np.concatenate(cycles_list)


def bin_cycles(
    cycles: np.ndarray,
    range_bins: int = 50,
    mean_bins: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bin cycles into a histogram for visualization or further analysis.
    
    Args:
        cycles: Cycle array from rainflow_count
        range_bins: Number of bins for cycle ranges
        mean_bins: Number of bins for cycle means (None for 1D histogram)
        
    Returns:
        If mean_bins is None:
            bin_centers: Center values of range bins
            counts: Cycle counts in each bin
            None
        If mean_bins is specified:
            range_centers: Center values of range bins
            mean_centers: Center values of mean bins
            counts_2d: 2D histogram of cycles
    """
    if len(cycles) == 0:
        if mean_bins is None:
            return np.array([]), np.array([]), None
        else:
            return np.array([]), np.array([]), np.array([])
    
    if mean_bins is None:
        # 1D histogram by range only
        range_edges = np.linspace(cycles['range'].min(), cycles['range'].max(), range_bins + 1)
        bin_indices = np.digitize(cycles['range'], range_edges) - 1
        bin_indices = np.clip(bin_indices, 0, range_bins - 1)
        
        counts = np.zeros(range_bins)
        for i, count in enumerate(cycles['count']):
            counts[bin_indices[i]] += count
        
        bin_centers = (range_edges[:-1] + range_edges[1:]) / 2
        return bin_centers, counts, None
    else:
        # 2D histogram by range and mean
        range_edges = np.linspace(cycles['range'].min(), cycles['range'].max(), range_bins + 1)
        mean_edges = np.linspace(cycles['mean'].min(), cycles['mean'].max(), mean_bins + 1)
        
        counts_2d = np.zeros((range_bins, mean_bins))
        
        for cycle in cycles:
            r_idx = np.digitize(cycle['range'], range_edges) - 1
            m_idx = np.digitize(cycle['mean'], mean_edges) - 1
            r_idx = np.clip(r_idx, 0, range_bins - 1)
            m_idx = np.clip(m_idx, 0, mean_bins - 1)
            counts_2d[r_idx, m_idx] += cycle['count']
        
        range_centers = (range_edges[:-1] + range_edges[1:]) / 2
        mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2
        
        return range_centers, mean_centers, counts_2d

