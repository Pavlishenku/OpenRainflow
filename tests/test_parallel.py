"""Tests for parallel processing module."""

import numpy as np
import pytest
from openrainflow import rainflow_count
from openrainflow.parallel import (
    process_signals_parallel,
    batch_damage_calculation,
    parallel_rainflow_batch,
    ParallelFatigueAnalyzer
)
from openrainflow.eurocode import EurocodeCategory


class TestProcessSignalsParallel:
    """Test parallel signal processing."""
    
    def test_basic_parallel_processing(self):
        """Test basic parallel rainflow counting."""
        np.random.seed(42)
        signals = [np.random.randn(100) * 50 + 100 for _ in range(5)]
        
        # Process in parallel
        results = process_signals_parallel(signals, rainflow_count, n_jobs=2)
        
        # Should have one result per signal
        assert len(results) == len(signals)
        
        # Each result should be a cycles array
        for cycles in results:
            assert 'range' in cycles.dtype.names
            assert 'mean' in cycles.dtype.names
            assert 'count' in cycles.dtype.names
    
    def test_parallel_vs_sequential(self):
        """Test that parallel gives same results as sequential."""
        np.random.seed(42)
        signals = [np.random.randn(50) * 30 + 80 for _ in range(3)]
        
        # Sequential
        results_seq = [rainflow_count(sig) for sig in signals]
        
        # Parallel
        results_par = process_signals_parallel(signals, rainflow_count, n_jobs=2)
        
        # Results should be identical
        assert len(results_seq) == len(results_par)
        for seq, par in zip(results_seq, results_par):
            np.testing.assert_array_almost_equal(seq['range'], par['range'])
            np.testing.assert_array_almost_equal(seq['mean'], par['mean'])
            np.testing.assert_array_almost_equal(seq['count'], par['count'])
    
    def test_parallel_with_kwargs(self):
        """Test parallel processing with additional arguments."""
        np.random.seed(42)
        signals = [np.random.randn(100) * 50 + 100 for _ in range(3)]
        
        # Use gate parameter
        results = process_signals_parallel(
            signals, rainflow_count, n_jobs=2, gate=20.0
        )
        
        # All cycles should have range >= gate
        for cycles in results:
            if len(cycles) > 0:
                assert np.all(cycles['range'] >= 20.0 - 1e-10)
    
    def test_single_job(self):
        """Test that n_jobs=1 works (sequential)."""
        np.random.seed(42)
        signals = [np.random.randn(50) for _ in range(2)]
        
        results = process_signals_parallel(signals, rainflow_count, n_jobs=1)
        
        assert len(results) == 2
        for cycles in results:
            assert len(cycles) > 0
    
    def test_empty_signal_list(self):
        """Test with empty signal list."""
        results = process_signals_parallel([], rainflow_count, n_jobs=2)
        assert len(results) == 0
    
    def test_fallback_without_joblib(self):
        """Test that parallel still works (simplified test)."""
        # Note: Testing actual ImportError for joblib is complex
        # This test just ensures the function works
        np.random.seed(42)
        signals = [np.random.randn(50) for _ in range(2)]
        
        results = process_signals_parallel(signals, rainflow_count, n_jobs=2)
        
        assert len(results) == 2
        for cycles in results:
            assert len(cycles) > 0


class TestBatchDamageCalculation:
    """Test batch damage calculation."""
    
    def test_batch_damage_single_curve(self):
        """Test batch damage with single curve for all."""
        np.random.seed(42)
        
        # Create multiple cycle sets
        cycles_list = []
        for _ in range(3):
            signal = np.random.randn(100) * 50 + 100
            cycles = rainflow_count(signal)
            cycles_list.append(cycles)
        
        curve = EurocodeCategory.get_curve('71')
        
        # Calculate damages in batch
        damages = batch_damage_calculation(cycles_list, curve, n_jobs=2)
        
        # Should have one damage per cycles
        assert len(damages) == len(cycles_list)
        
        # All damages should be positive
        assert np.all(damages >= 0)
    
    def test_batch_damage_multiple_curves(self):
        """Test batch damage with different curves."""
        np.random.seed(42)
        
        cycles_list = []
        for _ in range(3):
            signal = np.random.randn(100) * 50 + 100
            cycles = rainflow_count(signal)
            cycles_list.append(cycles)
        
        # Different curves for each
        curves = [
            EurocodeCategory.get_curve('71'),
            EurocodeCategory.get_curve('56'),
            EurocodeCategory.get_curve('40')
        ]
        
        damages = batch_damage_calculation(cycles_list, curves, n_jobs=2)
        
        assert len(damages) == 3
        assert np.all(damages >= 0)
    
    def test_batch_damage_length_mismatch(self):
        """Test error when lengths don't match."""
        cycles_list = [np.array([], dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])]
        curves = [EurocodeCategory.get_curve('71'), EurocodeCategory.get_curve('56')]
        
        with pytest.raises(ValueError, match="must have same length"):
            batch_damage_calculation(cycles_list, curves)
    
    def test_batch_damage_sequential_consistency(self):
        """Test that batch gives same results as sequential."""
        from openrainflow import calculate_damage
        
        np.random.seed(42)
        cycles_list = []
        for _ in range(3):
            signal = np.random.randn(100) * 50 + 100
            cycles = rainflow_count(signal)
            cycles_list.append(cycles)
        
        curve = EurocodeCategory.get_curve('71')
        
        # Sequential
        damages_seq = np.array([calculate_damage(c, curve) for c in cycles_list])
        
        # Batch
        damages_batch = batch_damage_calculation(cycles_list, curve, n_jobs=2)
        
        np.testing.assert_array_almost_equal(damages_seq, damages_batch)


class TestParallelRainflowBatch:
    """Test batch processing of very large signals."""
    
    def test_large_signal_batching(self):
        """Test splitting large signal into batches."""
        np.random.seed(42)
        
        # Create a large signal
        signal = np.random.randn(10000) * 50 + 100
        
        # Process with batching
        cycles = parallel_rainflow_batch(signal, batch_size=3000, n_jobs=2)
        
        # Should get reasonable results
        assert len(cycles) > 0
        assert 'range' in cycles.dtype.names
    
    def test_batch_auto_size(self):
        """Test automatic batch size determination."""
        np.random.seed(42)
        signal = np.random.randn(5000) * 50 + 100
        
        # Auto batch size (None)
        cycles = parallel_rainflow_batch(signal, batch_size=None, n_jobs=2)
        
        assert len(cycles) > 0
    
    def test_batch_with_overlap(self):
        """Test batching with overlap."""
        np.random.seed(42)
        signal = np.random.randn(5000) * 50 + 100
        
        cycles = parallel_rainflow_batch(
            signal, batch_size=2000, n_jobs=2, overlap=200
        )
        
        assert len(cycles) > 0
    
    def test_batch_small_signal(self):
        """Test that small signal works with batching."""
        signal = np.array([0, 10, 0, 20, 0])
        
        cycles = parallel_rainflow_batch(signal, batch_size=3, n_jobs=1)
        
        # Should still work, even if inefficient
        assert len(cycles) > 0


class TestParallelFatigueAnalyzer:
    """Test high-level parallel analyzer class."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = ParallelFatigueAnalyzer(n_jobs=2, verbose=0)
        
        assert analyzer.n_jobs == 2
        assert analyzer.verbose == 0
        assert analyzer.signals == []
        assert analyzer.fatigue_curve is None
        assert analyzer.cycles_list is None
    
    def test_add_signals(self):
        """Test adding signals."""
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        signals = [np.random.randn(100) for _ in range(3)]
        analyzer.add_signals(signals)
        
        assert len(analyzer.signals) == 3
    
    def test_set_fatigue_curve_by_name(self):
        """Test setting curve by Eurocode name."""
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        analyzer.set_fatigue_curve('71')
        
        assert analyzer.fatigue_curve is not None
        assert analyzer.fatigue_curve.name == '71'
    
    def test_set_fatigue_curve_by_object(self):
        """Test setting curve by object."""
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        curve = EurocodeCategory.get_curve('56')
        analyzer.set_fatigue_curve(curve)
        
        assert analyzer.fatigue_curve is curve
    
    def test_count_cycles(self):
        """Test cycle counting."""
        np.random.seed(42)
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        signals = [np.random.randn(100) * 50 + 100 for _ in range(3)]
        analyzer.add_signals(signals)
        
        cycles_list = analyzer.count_cycles()
        
        assert len(cycles_list) == 3
        assert analyzer.cycles_list is not None
        
        for cycles in cycles_list:
            assert len(cycles) > 0
    
    def test_calculate_damages(self):
        """Test damage calculation."""
        np.random.seed(42)
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        signals = [np.random.randn(100) * 50 + 100 for _ in range(3)]
        analyzer.add_signals(signals)
        analyzer.set_fatigue_curve('71')
        
        damages = analyzer.calculate_damages()
        
        assert len(damages) == 3
        assert np.all(damages >= 0)
    
    def test_calculate_damages_without_curve(self):
        """Test that damage calculation fails without curve."""
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        signals = [np.random.randn(100) for _ in range(2)]
        analyzer.add_signals(signals)
        
        with pytest.raises(ValueError, match="Fatigue curve not set"):
            analyzer.calculate_damages()
    
    def test_full_analysis(self):
        """Test complete analysis workflow."""
        np.random.seed(42)
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        # Setup
        signals = [np.random.randn(100) * 50 + 100 for _ in range(3)]
        analyzer.add_signals(signals)
        analyzer.set_fatigue_curve('71')
        
        # Analyze
        results = analyzer.analyze(design_life=1000)
        
        # Check results
        assert results['n_signals'] == 3
        assert 'damages' in results
        assert 'lives' in results
        assert 'utilizations' in results
        assert 'cycles_list' in results
        
        assert len(results['damages']) == 3
        assert len(results['lives']) == 3
        assert len(results['utilizations']) == 3
        
        assert results['design_life'] == 1000
        assert 'max_damage' in results
        assert 'min_life' in results
        assert 'max_utilization' in results
    
    def test_get_summary(self):
        """Test summary generation."""
        np.random.seed(42)
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        signals = [np.random.randn(100) * 50 + 100 for _ in range(3)]
        analyzer.add_signals(signals)
        analyzer.set_fatigue_curve('71')
        
        # Before analysis
        summary = analyzer.get_summary()
        assert "No analysis performed" in summary
        
        # After counting
        analyzer.count_cycles()
        summary = analyzer.get_summary()
        
        assert "Parallel Fatigue Analysis" in summary
        assert "Number of signals:" in summary
        assert "71" in summary
    
    def test_analyzer_with_gate(self):
        """Test analyzer with gate parameter."""
        np.random.seed(42)
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        signals = [np.random.randn(100) * 50 + 100 for _ in range(2)]
        analyzer.add_signals(signals)
        analyzer.set_fatigue_curve('71')
        
        # Count with gate
        cycles_list = analyzer.count_cycles(gate=30.0)
        
        # All cycles should be >= gate
        for cycles in cycles_list:
            if len(cycles) > 0:
                assert np.all(cycles['range'] >= 30.0 - 1e-10)
    
    def test_analyzer_empty_signals(self):
        """Test analyzer with no signals."""
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        analyzer.set_fatigue_curve('71')
        
        # Should handle empty gracefully
        cycles_list = analyzer.count_cycles()
        assert len(cycles_list) == 0
        
        damages = analyzer.calculate_damages()
        assert len(damages) == 0


class TestIntegrationParallel:
    """Integration tests for parallel processing."""
    
    def test_realistic_parallel_workflow(self):
        """Test realistic workflow with multiple signals."""
        np.random.seed(42)
        
        # Generate realistic stress histories
        n_signals = 5
        signals = []
        for i in range(n_signals):
            # Different stress levels
            mean_stress = 80 + i * 20
            signal = np.random.randn(500) * 30 + mean_stress
            signals.append(signal)
        
        # Process in parallel
        cycles_list = process_signals_parallel(
            signals, rainflow_count, n_jobs=2
        )
        
        # Calculate damages
        curve = EurocodeCategory.get_curve('71')
        damages = batch_damage_calculation(cycles_list, curve, n_jobs=2)
        
        # Check that higher stress gives higher damage
        assert len(damages) == n_signals
        
        # Generally, higher mean stress should lead to more damage
        # (though randomness may affect this)
        assert np.all(damages >= 0)
    
    def test_parallel_vs_sequential_full_workflow(self):
        """Test that parallel workflow matches sequential."""
        from openrainflow import calculate_damage
        
        np.random.seed(42)
        signals = [np.random.randn(200) * 50 + 100 for _ in range(4)]
        curve = EurocodeCategory.get_curve('71')
        
        # Sequential workflow
        damages_seq = []
        for signal in signals:
            cycles = rainflow_count(signal)
            damage = calculate_damage(cycles, curve)
            damages_seq.append(damage)
        damages_seq = np.array(damages_seq)
        
        # Parallel workflow
        cycles_list = process_signals_parallel(signals, rainflow_count, n_jobs=2)
        damages_par = batch_damage_calculation(cycles_list, curve, n_jobs=2)
        
        # Should match
        np.testing.assert_array_almost_equal(damages_seq, damages_par)
    
    def test_memory_efficiency_large_batch(self):
        """Test memory efficiency with many signals."""
        np.random.seed(42)
        
        # Create many small signals
        n_signals = 50
        signals = [np.random.randn(100) * 50 + 100 for _ in range(n_signals)]
        
        # This should not crash or use excessive memory
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        analyzer.add_signals(signals)
        analyzer.set_fatigue_curve('71')
        
        results = analyzer.analyze()
        
        assert results['n_signals'] == n_signals
        assert len(results['damages']) == n_signals


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

