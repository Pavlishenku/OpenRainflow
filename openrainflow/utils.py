"""
Utility functions for signal processing and data manipulation.
"""

import numpy as np
from typing import Optional, Tuple
from numba import njit


@njit(cache=True)
def remove_mean(signal: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Remove mean value from signal.
    
    Args:
        signal: Input signal
        
    Returns:
        signal_zeromean: Signal with zero mean
        mean_value: Original mean value
    """
    mean_value = np.mean(signal)
    return signal - mean_value, mean_value


def resample_signal(
    signal: np.ndarray,
    target_length: int,
    method: str = 'linear'
) -> np.ndarray:
    """
    Resample signal to different length.
    
    Args:
        signal: Input signal
        target_length: Desired length
        method: Interpolation method ('linear', 'nearest', 'cubic')
        
    Returns:
        Resampled signal
    """
    from scipy import interpolate
    
    x_old = np.arange(len(signal))
    x_new = np.linspace(0, len(signal) - 1, target_length)
    
    if method == 'linear':
        f = interpolate.interp1d(x_old, signal, kind='linear')
    elif method == 'nearest':
        f = interpolate.interp1d(x_old, signal, kind='nearest')
    elif method == 'cubic':
        f = interpolate.interp1d(x_old, signal, kind='cubic')
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return f(x_new)


def filter_signal(
    signal: np.ndarray,
    cutoff_freq: float,
    sampling_freq: float,
    filter_type: str = 'lowpass',
    order: int = 4
) -> np.ndarray:
    """
    Apply Butterworth filter to signal.
    
    Args:
        signal: Input signal
        cutoff_freq: Cutoff frequency [Hz]
        sampling_freq: Sampling frequency [Hz]
        filter_type: 'lowpass', 'highpass', 'bandpass', or 'bandstop'
        order: Filter order
        
    Returns:
        Filtered signal
    """
    from scipy import signal as sp_signal
    
    nyquist = sampling_freq / 2
    normalized_cutoff = cutoff_freq / nyquist
    
    b, a = sp_signal.butter(order, normalized_cutoff, btype=filter_type)
    filtered = sp_signal.filtfilt(b, a, signal)
    
    return filtered


def generate_random_signal(
    n_points: int,
    mean: float = 0.0,
    std: float = 1.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate random Gaussian signal.
    
    Args:
        n_points: Number of points
        mean: Mean value
        std: Standard deviation
        seed: Random seed for reproducibility
        
    Returns:
        Random signal
    """
    if seed is not None:
        np.random.seed(seed)
    
    return np.random.randn(n_points) * std + mean


def generate_sine_signal(
    n_points: int,
    amplitude: float,
    frequency: float,
    phase: float = 0.0,
    offset: float = 0.0,
    sampling_freq: float = 1.0
) -> np.ndarray:
    """
    Generate sinusoidal signal.
    
    Args:
        n_points: Number of points
        amplitude: Amplitude
        frequency: Frequency [Hz]
        phase: Phase offset [rad]
        offset: DC offset
        sampling_freq: Sampling frequency [Hz]
        
    Returns:
        Sinusoidal signal
    """
    t = np.arange(n_points) / sampling_freq
    return amplitude * np.sin(2 * np.pi * frequency * t + phase) + offset


def load_signal_from_file(
    filepath: str,
    column: int = 0,
    skip_rows: int = 0,
    delimiter: Optional[str] = None
) -> np.ndarray:
    """
    Load signal from text file.
    
    Args:
        filepath: Path to file
        column: Column index to read
        skip_rows: Number of header rows to skip
        delimiter: Column delimiter (None for whitespace)
        
    Returns:
        Signal array
    """
    data = np.loadtxt(filepath, skiprows=skip_rows, delimiter=delimiter)
    
    if data.ndim == 1:
        return data
    else:
        return data[:, column]


def save_cycles_to_file(
    cycles: np.ndarray,
    filepath: str,
    header: bool = True
):
    """
    Save rainflow cycles to text file.
    
    Args:
        cycles: Structured array from rainflow_count
        filepath: Output file path
        header: Include header row
    """
    header_str = "Range,Mean,Count" if header else ""
    
    np.savetxt(
        filepath,
        np.column_stack([cycles['range'], cycles['mean'], cycles['count']]),
        delimiter=',',
        header=header_str,
        comments=''
    )


def calculate_statistics(signal: np.ndarray) -> dict:
    """
    Calculate basic statistics of a signal.
    
    Args:
        signal: Input signal
        
    Returns:
        Dictionary with statistics
    """
    return {
        'mean': np.mean(signal),
        'std': np.std(signal),
        'min': np.min(signal),
        'max': np.max(signal),
        'range': np.max(signal) - np.min(signal),
        'rms': np.sqrt(np.mean(signal**2)),
        'median': np.median(signal),
        'q25': np.percentile(signal, 25),
        'q75': np.percentile(signal, 75),
    }


@njit(cache=True)
def range_pair_count(signal: np.ndarray) -> int:
    """
    Estimate number of reversals in signal (fast check).
    
    Args:
        signal: Input signal
        
    Returns:
        Approximate number of reversals
    """
    if len(signal) < 3:
        return len(signal)
    
    count = 1  # First point
    
    for i in range(1, len(signal) - 1):
        if (signal[i] >= signal[i-1] and signal[i] > signal[i+1]) or \
           (signal[i] <= signal[i-1] and signal[i] < signal[i+1]):
            count += 1
    
    count += 1  # Last point
    return count

