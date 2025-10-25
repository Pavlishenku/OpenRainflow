"""Tests for rainflow counting algorithm."""

import numpy as np
import pytest
from openrainflow import rainflow_count, rainflow_count_parallel
from openrainflow.rainflow import _find_reversals, combine_cycles, bin_cycles


class TestFindReversals:
    """Test reversal finding."""
    
    def test_simple_signal(self):
        """Test reversal detection on simple signal."""
        signal = np.array([0, 1, 0, 2, 0, 3, 0])
        reversals, indices = _find_reversals(signal)
        
        # Should identify peaks and valleys
        assert len(reversals) > 0
        assert reversals[0] == signal[0]
        assert reversals[-1] == signal[-1]
    
    def test_monotonic_signal(self):
        """Test monotonic signal (no internal reversals)."""
        signal = np.array([0, 1, 2, 3, 4, 5])
        reversals, indices = _find_reversals(signal)
        
        # Only first and last points
        assert len(reversals) == 2
        assert reversals[0] == 0
        assert reversals[1] == 5
    
    def test_constant_signal(self):
        """Test constant signal."""
        signal = np.array([5, 5, 5, 5])
        reversals, indices = _find_reversals(signal)
        
        # Only endpoints
        assert len(reversals) == 2


class TestRainflowCount:
    """Test rainflow counting."""
    
    def test_simple_cycles(self):
        """Test basic cycle counting."""
        # Simple signal with clear cycles
        signal = np.array([0, 1, 0, 2, 0, 1, 0])
        cycles = rainflow_count(signal)
        
        assert len(cycles) > 0
        assert 'range' in cycles.dtype.names
        assert 'mean' in cycles.dtype.names
        assert 'count' in cycles.dtype.names
    
    def test_single_cycle(self):
        """Test signal with one full cycle."""
        signal = np.array([0, 10, 0])
        cycles = rainflow_count(signal)
        
        assert len(cycles) >= 1
        # Should have a cycle with range ~10
        max_range = np.max(cycles['range'])
        assert max_range == pytest.approx(10.0, rel=1e-6)
    
    def test_empty_signal(self):
        """Test empty or very short signal."""
        signal = np.array([])
        cycles = rainflow_count(signal)
        assert len(cycles) == 0
        
        signal = np.array([5])
        cycles = rainflow_count(signal)
        assert len(cycles) == 0
    
    def test_zero_removal(self):
        """Test removal of zero-range cycles."""
        signal = np.array([0, 0, 1, 1, 2, 2])
        
        cycles_with_zeros = rainflow_count(signal, remove_zeros=False)
        cycles_no_zeros = rainflow_count(signal, remove_zeros=True)
        
        # Should have fewer cycles when zeros removed
        assert len(cycles_no_zeros) <= len(cycles_with_zeros)
    
    def test_gate_threshold(self):
        """Test gating (minimum range threshold)."""
        signal = np.array([0, 10, 0, 100, 0])
        
        cycles_no_gate = rainflow_count(signal, gate=None)
        cycles_with_gate = rainflow_count(signal, gate=50)
        
        # Gate should filter out small cycles
        assert len(cycles_with_gate) <= len(cycles_no_gate)
        
        # All remaining cycles should be >= gate
        if len(cycles_with_gate) > 0:
            assert np.all(cycles_with_gate['range'] >= 50)
    
    def test_count_values(self):
        """Test that cycle counts are valid (0.5 or 1.0)."""
        signal = np.random.randn(1000) * 50 + 100
        cycles = rainflow_count(signal)
        
        # All counts should be 0.5 or 1.0
        unique_counts = np.unique(cycles['count'])
        assert all(c in [0.5, 1.0] for c in unique_counts)
    
    def test_reproducibility(self):
        """Test that results are reproducible."""
        signal = np.random.randn(100)
        
        cycles1 = rainflow_count(signal)
        cycles2 = rainflow_count(signal)
        
        np.testing.assert_array_equal(cycles1['range'], cycles2['range'])
        np.testing.assert_array_equal(cycles1['mean'], cycles2['mean'])
        np.testing.assert_array_equal(cycles1['count'], cycles2['count'])


class TestRainflowParallel:
    """Test parallel rainflow counting."""
    
    def test_parallel_vs_serial(self):
        """Test parallel processing gives same results."""
        np.random.seed(42)
        signals = [np.random.randn(100) for _ in range(5)]
        
        # Serial
        cycles_serial = [rainflow_count(sig) for sig in signals]
        
        # Parallel (using n_jobs=2 to test parallelization)
        cycles_parallel = rainflow_count_parallel(signals, n_jobs=2)
        
        assert len(cycles_serial) == len(cycles_parallel)
        
        for cs, cp in zip(cycles_serial, cycles_parallel):
            np.testing.assert_array_almost_equal(cs['range'], cp['range'])
    
    def test_combine_cycles(self):
        """Test combining multiple cycle arrays."""
        cycles1 = np.array([(10, 5, 1.0), (20, 10, 0.5)],
                          dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
        cycles2 = np.array([(15, 7, 1.0)],
                          dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
        
        combined = combine_cycles([cycles1, cycles2])
        
        assert len(combined) == 3
        assert combined.dtype == cycles1.dtype


class TestBinCycles:
    """Test cycle binning."""
    
    def test_1d_binning(self):
        """Test 1D histogram by range."""
        cycles = np.array(
            [(10, 5, 1.0), (20, 10, 1.0), (30, 15, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        bin_centers, counts, _ = bin_cycles(cycles, range_bins=5, mean_bins=None)
        
        assert len(bin_centers) == 5
        assert len(counts) == 5
        assert np.sum(counts) == pytest.approx(3.0)  # Total cycles
    
    def test_2d_binning(self):
        """Test 2D histogram by range and mean."""
        cycles = np.array(
            [(10, 5, 1.0), (20, 10, 1.0), (30, 15, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        range_centers, mean_centers, counts_2d = bin_cycles(
            cycles, range_bins=5, mean_bins=5
        )
        
        assert len(range_centers) == 5
        assert len(mean_centers) == 5
        assert counts_2d.shape == (5, 5)
        assert np.sum(counts_2d) == pytest.approx(3.0)
    
    def test_empty_cycles(self):
        """Test binning empty cycles."""
        cycles = np.array([], dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
        
        bin_centers, counts, _ = bin_cycles(cycles, range_bins=10)
        
        assert len(bin_centers) == 0
        assert len(counts) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

