"""
Integration tests for complete fatigue analysis workflows.

These tests validate the entire process from signal to fatigue life prediction.
"""

import numpy as np
import pytest
from openrainflow import (
    rainflow_count, 
    rainflow_count_parallel,
    calculate_damage,
    calculate_life
)
from openrainflow.eurocode import EurocodeCategory, FatigueCurve
from openrainflow.damage import (
    calculate_damage_from_histogram,
    calculate_equivalent_stress,
    assess_fatigue_safety,
    damage_contribution_analysis
)
from openrainflow.parallel import ParallelFatigueAnalyzer


class TestBasicWorkflow:
    """Test basic fatigue analysis workflow."""
    
    def test_simple_workflow(self):
        """Test simple signal → cycles → damage → life."""
        # Generate signal
        np.random.seed(42)
        signal = np.random.randn(1000) * 50 + 100
        
        # Step 1: Rainflow counting
        cycles = rainflow_count(signal)
        assert len(cycles) > 0
        
        # Step 2: Get fatigue curve
        curve = EurocodeCategory.get_curve('71')
        
        # Step 3: Calculate damage
        damage = calculate_damage(cycles, curve)
        assert damage > 0
        assert np.isfinite(damage)
        
        # Step 4: Calculate life
        life = calculate_life(cycles, curve)
        assert life > 0
        assert np.isfinite(life)
        
        # Verify relationship: damage * life = 1
        assert damage * life == pytest.approx(1.0, rel=1e-6)
    
    def test_workflow_with_safety_factors(self):
        """Test workflow with partial safety factors."""
        np.random.seed(42)
        signal = np.random.randn(1000) * 50 + 100
        
        cycles = rainflow_count(signal)
        curve = EurocodeCategory.get_curve('71')
        
        # Without safety factor
        damage_no_sf = calculate_damage(cycles, curve, partial_safety_factor=1.0)
        life_no_sf = calculate_life(cycles, curve, partial_safety_factor=1.0)
        
        # With safety factor
        damage_with_sf = calculate_damage(cycles, curve, partial_safety_factor=1.25)
        life_with_sf = calculate_life(cycles, curve, partial_safety_factor=1.25)
        
        # Safety factor should increase damage and decrease life
        assert damage_with_sf > damage_no_sf
        assert life_with_sf < life_no_sf
    
    def test_workflow_with_cutoff(self):
        """Test workflow with CAFL cutoff."""
        # Signal with low and high stress
        signal = np.array([0, 10, 0, 100, 0, 10, 0, 100, 0])
        
        cycles = rainflow_count(signal)
        curve = EurocodeCategory.get_curve('71')
        
        # With cutoff
        damage_cutoff = calculate_damage(cycles, curve, use_cutoff=True)
        life_cutoff = calculate_life(cycles, curve, use_cutoff=True)
        
        # Without cutoff
        damage_no_cutoff = calculate_damage(cycles, curve, use_cutoff=False)
        life_no_cutoff = calculate_life(cycles, curve, use_cutoff=False)
        
        # Cutoff should reduce damage (ignoring low stress cycles)
        assert damage_cutoff <= damage_no_cutoff
        assert life_cutoff >= life_no_cutoff
    
    def test_workflow_different_curves(self):
        """Test workflow with different fatigue curves."""
        np.random.seed(42)
        signal = np.random.randn(1000) * 50 + 100
        
        cycles = rainflow_count(signal)
        
        # Test several Eurocode curves
        curves = ['71', '56', '40', '36']
        damages = []
        
        for curve_name in curves:
            curve = EurocodeCategory.get_curve(curve_name)
            damage = calculate_damage(cycles, curve)
            damages.append(damage)
        
        # Higher strength category should give less damage
        # 71 > 56 > 40 > 36 (strength)
        # So damage should increase
        for i in range(len(damages) - 1):
            assert damages[i] <= damages[i + 1]


class TestCompleteAnalysis:
    """Test complete analysis with all features."""
    
    def test_comprehensive_analysis(self):
        """Test comprehensive fatigue analysis."""
        # Generate realistic stress history
        np.random.seed(42)
        base_stress = 100
        variable_amplitude = np.random.randn(2000) * 30
        periodic_load = 50 * np.sin(np.linspace(0, 10*np.pi, 2000))
        signal = base_stress + variable_amplitude + periodic_load
        
        # Rainflow counting
        cycles = rainflow_count(signal)
        
        # Select curve
        curve = EurocodeCategory.get_curve('71')
        
        # Damage analysis
        damage = calculate_damage(cycles, curve)
        life = calculate_life(cycles, curve)
        equiv_stress = calculate_equivalent_stress(cycles, curve)
        
        # Safety assessment
        design_life = 1000
        utilization, status, details = assess_fatigue_safety(
            cycles, curve, design_life=design_life
        )
        
        # Verify results make sense
        assert damage > 0
        assert life > 0
        assert equiv_stress > 0
        assert utilization >= 0
        assert status in ['PASS', 'WARNING', 'FAIL']
        
        # Check details
        assert 'damage_per_cycle' in details
        assert 'actual_life' in details
        assert 'reserve_factor' in details
        
        # Utilization should match damage * design_life
        expected_utilization = damage * design_life
        assert utilization == pytest.approx(expected_utilization, rel=1e-6)
    
    def test_damage_contribution_analysis(self):
        """Test damage contribution by stress range."""
        np.random.seed(42)
        signal = np.random.randn(1000) * 50 + 100
        
        cycles = rainflow_count(signal)
        curve = EurocodeCategory.get_curve('71')
        
        # Analyze damage contribution
        bins, counts, damage_fractions = damage_contribution_analysis(
            cycles, curve, n_bins=10
        )
        
        # Verify results
        assert len(bins) == 10
        assert len(damage_fractions) == 10
        
        # Damage fractions should sum to 1
        assert np.sum(damage_fractions) == pytest.approx(1.0, rel=1e-6)
        
        # All fractions should be non-negative
        assert np.all(damage_fractions >= 0)
        
        # Higher stress ranges typically contribute more to damage
        # (though not always due to count differences)
    
    def test_histogram_based_analysis(self):
        """Test analysis from pre-binned histogram data."""
        # Simulated histogram data
        stress_ranges = np.array([50, 75, 100, 125, 150])
        cycle_counts = np.array([1000, 500, 200, 50, 10])
        
        curve = EurocodeCategory.get_curve('71')
        
        # Calculate damage from histogram
        damage = calculate_damage_from_histogram(
            stress_ranges, cycle_counts, curve
        )
        
        assert damage > 0
        assert np.isfinite(damage)
        
        # Should match cycles-based approach
        cycles = np.array([
            (stress_ranges[i], stress_ranges[i]/2, cycle_counts[i])
            for i in range(len(stress_ranges))
        ], dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
        
        damage_from_cycles = calculate_damage(cycles, curve)
        
        # Should be approximately equal
        assert damage == pytest.approx(damage_from_cycles, rel=1e-10)


class TestParallelWorkflow:
    """Test parallel processing workflows."""
    
    def test_parallel_multiple_signals(self):
        """Test parallel analysis of multiple signals."""
        np.random.seed(42)
        
        # Generate multiple signals
        signals = [np.random.randn(500) * 50 + 100 for _ in range(5)]
        
        # Parallel counting
        cycles_list = rainflow_count_parallel(signals, n_jobs=2)
        
        assert len(cycles_list) == 5
        
        # Analyze each
        curve = EurocodeCategory.get_curve('71')
        damages = [calculate_damage(cycles, curve) for cycles in cycles_list]
        
        # All should be positive
        assert all(d > 0 for d in damages)
    
    def test_parallel_analyzer_full_workflow(self):
        """Test ParallelFatigueAnalyzer complete workflow."""
        np.random.seed(42)
        
        # Create analyzer
        analyzer = ParallelFatigueAnalyzer(n_jobs=2)
        
        # Add signals
        signals = [np.random.randn(500) * 50 + 100 for _ in range(5)]
        analyzer.add_signals(signals)
        
        # Set fatigue curve
        analyzer.set_fatigue_curve('71')
        
        # Run analysis
        results = analyzer.analyze(design_life=1000)
        
        # Verify results
        assert results['n_signals'] == 5
        assert len(results['damages']) == 5
        assert len(results['lives']) == 5
        assert len(results['utilizations']) == 5
        
        # All positive
        assert np.all(results['damages'] > 0)
        assert np.all(results['lives'] > 0)
        
        # Get summary
        summary = analyzer.get_summary()
        assert "Number of signals:" in summary
        assert "5" in summary


class TestEdgeCasesIntegration:
    """Test edge cases in complete workflows."""
    
    def test_very_low_stress_signal(self):
        """Test signal with very low stress (below CAFL)."""
        # Low stress signal
        signal = np.random.randn(1000) * 5 + 10
        
        cycles = rainflow_count(signal)
        curve = EurocodeCategory.get_curve('71')
        
        # With cutoff, should have zero or very low damage
        damage = calculate_damage(cycles, curve, use_cutoff=True)
        life = calculate_life(cycles, curve, use_cutoff=True)
        
        # Life should be very long or infinite
        assert damage >= 0
        assert life > 0
        
        # May be infinite if all cycles below CAFL
        if np.isinf(life):
            assert damage == 0.0
    
    def test_very_high_stress_signal(self):
        """Test signal with very high stress."""
        # High stress signal
        signal = np.random.randn(1000) * 50 + 300
        
        cycles = rainflow_count(signal)
        curve = EurocodeCategory.get_curve('71')
        
        damage = calculate_damage(cycles, curve)
        life = calculate_life(cycles, curve)
        
        # Should have significant damage and short life
        assert damage > 0
        assert life > 0
        assert np.isfinite(damage)
        assert np.isfinite(life)
    
    def test_constant_amplitude_loading(self):
        """Test constant amplitude loading."""
        # Perfect constant amplitude
        stress_range = 100
        n_cycles = 100
        signal = np.tile([0, stress_range, 0], n_cycles)[:-1]
        
        cycles = rainflow_count(signal)
        curve = EurocodeCategory.get_curve('71')
        
        # Should detect approximately n_cycles of the same amplitude
        total_cycles = np.sum(cycles['count'])
        assert total_cycles == pytest.approx(n_cycles, rel=0.1)
        
        # All ranges should be similar
        ranges = cycles['range']
        assert np.std(ranges) / np.mean(ranges) < 0.01  # Low variation
    
    def test_empty_signal_handling(self):
        """Test handling of empty or very short signals."""
        # Empty signal
        signal = np.array([])
        cycles = rainflow_count(signal)
        assert len(cycles) == 0
        
        curve = EurocodeCategory.get_curve('71')
        damage = calculate_damage(cycles, curve)
        assert damage == 0.0
        
        life = calculate_life(cycles, curve)
        assert np.isinf(life)


class TestConsistency:
    """Test consistency across different approaches."""
    
    def test_serial_vs_parallel_consistency(self):
        """Test that serial and parallel give identical results."""
        np.random.seed(42)
        signals = [np.random.randn(200) * 50 + 100 for _ in range(5)]
        
        # Serial
        cycles_serial = [rainflow_count(sig) for sig in signals]
        
        # Parallel
        cycles_parallel = rainflow_count_parallel(signals, n_jobs=2)
        
        # Should be identical
        for cs, cp in zip(cycles_serial, cycles_parallel):
            np.testing.assert_array_almost_equal(cs['range'], cp['range'])
            np.testing.assert_array_almost_equal(cs['mean'], cp['mean'])
            np.testing.assert_array_almost_equal(cs['count'], cp['count'])
    
    def test_gate_consistency(self):
        """Test that gate parameter works consistently."""
        np.random.seed(42)
        signal = np.random.randn(1000) * 50 + 100
        
        gate_values = [None, 20.0, 40.0, 60.0]
        cycle_counts = []
        
        for gate in gate_values:
            cycles = rainflow_count(signal, gate=gate)
            cycle_counts.append(len(cycles))
            
            # Verify gate is enforced
            if gate is not None and len(cycles) > 0:
                assert np.all(cycles['range'] >= gate - 1e-10)
        
        # Higher gate should give fewer or equal cycles
        for i in range(1, len(cycle_counts)):
            if gate_values[i] is not None:
                assert cycle_counts[i] <= cycle_counts[i-1]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

