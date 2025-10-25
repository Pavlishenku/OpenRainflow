"""Tests for damage calculation."""

import numpy as np
import pytest
from openrainflow import rainflow_count, calculate_damage, calculate_life
from openrainflow.eurocode import EurocodeCategory, FatigueCurve
from openrainflow.damage import (
    calculate_damage_from_histogram,
    calculate_equivalent_stress,
    assess_fatigue_safety,
    damage_contribution_analysis
)


class TestCalculateDamage:
    """Test basic damage calculation."""
    
    def test_zero_damage(self):
        """Test that no cycles gives zero damage."""
        cycles = np.array([], dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
        curve = EurocodeCategory.get_curve('71')
        
        damage = calculate_damage(cycles, curve)
        assert damage == 0.0
    
    def test_single_cycle(self):
        """Test damage from single cycle."""
        cycles = np.array(
            [(100.0, 50.0, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        damage = calculate_damage(cycles, curve)
        
        # Should be 1/N_f for this stress range
        N_f = curve.get_cycles_to_failure(100.0)
        expected_damage = 1.0 / N_f
        
        assert damage == pytest.approx(expected_damage, rel=1e-6)
    
    def test_multiple_cycles(self):
        """Test damage accumulation from multiple cycles."""
        cycles = np.array(
            [(100.0, 50.0, 1.0), (80.0, 40.0, 2.0), (60.0, 30.0, 3.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        damage = calculate_damage(cycles, curve)
        
        # Calculate expected damage manually
        expected = 0.0
        for cyc in cycles:
            N_f = curve.get_cycles_to_failure(cyc['range'])
            expected += cyc['count'] / N_f
        
        assert damage == pytest.approx(expected, rel=1e-6)
    
    def test_damage_with_safety_factor(self):
        """Test partial safety factor application."""
        cycles = np.array(
            [(100.0, 50.0, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        damage_no_factor = calculate_damage(cycles, curve, partial_safety_factor=1.0)
        damage_with_factor = calculate_damage(cycles, curve, partial_safety_factor=1.25)
        
        # Higher safety factor should give more damage
        assert damage_with_factor > damage_no_factor
    
    def test_damage_below_cafl(self):
        """Test that stress below CAFL causes no damage."""
        curve = EurocodeCategory.get_curve('71')
        
        # Create cycles below CAFL
        low_stress = curve.delta_sigma_L * 0.5
        cycles = np.array(
            [(low_stress, low_stress/2, 1000.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        damage = calculate_damage(cycles, curve, use_cutoff=True)
        assert damage == 0.0


class TestCalculateLife:
    """Test fatigue life calculation."""
    
    def test_life_calculation(self):
        """Test basic life calculation."""
        cycles = np.array(
            [(100.0, 50.0, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        life = calculate_life(cycles, curve)
        damage = calculate_damage(cycles, curve)
        
        # Life should be 1/damage
        assert life == pytest.approx(1.0 / damage, rel=1e-6)
    
    def test_infinite_life(self):
        """Test infinite life for stress below CAFL."""
        curve = EurocodeCategory.get_curve('71')
        low_stress = curve.delta_sigma_L * 0.5
        
        cycles = np.array(
            [(low_stress, low_stress/2, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        life = calculate_life(cycles, curve, use_cutoff=True)
        assert np.isinf(life)
    
    def test_custom_failure_damage(self):
        """Test custom failure damage threshold."""
        cycles = np.array(
            [(100.0, 50.0, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        life_standard = calculate_life(cycles, curve, failure_damage=1.0)
        life_conservative = calculate_life(cycles, curve, failure_damage=0.5)
        
        # Lower failure threshold should give shorter life
        assert life_conservative < life_standard
        assert life_conservative == pytest.approx(life_standard * 0.5, rel=1e-6)


class TestDamageFromHistogram:
    """Test histogram-based damage calculation."""
    
    def test_histogram_vs_cycles(self):
        """Test that histogram method gives same result as cycle-based."""
        # Create cycles
        cycles = np.array(
            [(100.0, 50.0, 5.0), (80.0, 40.0, 10.0), (60.0, 30.0, 15.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        # Calculate from cycles
        damage_cycles = calculate_damage(cycles, curve)
        
        # Calculate from histogram
        stress_ranges = cycles['range']
        cycle_counts = cycles['count']
        damage_histogram = calculate_damage_from_histogram(
            stress_ranges, cycle_counts, curve
        )
        
        assert damage_histogram == pytest.approx(damage_cycles, rel=1e-6)
    
    def test_histogram_length_mismatch(self):
        """Test error for mismatched array lengths."""
        curve = EurocodeCategory.get_curve('71')
        
        with pytest.raises(ValueError):
            calculate_damage_from_histogram(
                np.array([100, 80]),
                np.array([10, 20, 30]),  # Wrong length
                curve
            )


class TestEquivalentStress:
    """Test equivalent stress calculation."""
    
    def test_single_cycle_equivalent(self):
        """Test equivalent stress for single cycle type."""
        stress_range = 100.0
        n_cycles = 10.0
        cycles = np.array(
            [(stress_range, 50.0, n_cycles)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        # For single stress level, equivalent stress at N_eq cycles
        # should match original when N_eq = n_cycles
        equiv_stress = calculate_equivalent_stress(cycles, curve, N_eq=n_cycles)
        
        # For single stress level with matching N_eq, should equal that stress
        assert equiv_stress == pytest.approx(stress_range, rel=1e-6)
        
        # Test with default N_eq (2E6)
        equiv_stress_default = calculate_equivalent_stress(cycles, curve)
        # With fewer cycles than N_eq, equivalent stress will be lower
        assert equiv_stress_default < stress_range
    
    def test_equivalent_stress_properties(self):
        """Test equivalent stress properties."""
        cycles = np.array(
            [(100.0, 50.0, 5.0), (80.0, 40.0, 10.0), (60.0, 30.0, 15.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        # Use N_eq equal to total cycle count for meaningful comparison
        total_cycles = np.sum(cycles['count'])
        equiv_stress = calculate_equivalent_stress(cycles, curve, N_eq=total_cycles)
        
        # Equivalent stress should be a weighted average
        # For same number of cycles, should be between min and max
        assert equiv_stress > 0, "Equivalent stress should be positive"
        assert equiv_stress >= np.min(cycles['range']), \
            f"Equivalent stress {equiv_stress} < min range {np.min(cycles['range'])}"
        assert equiv_stress <= np.max(cycles['range']), \
            f"Equivalent stress {equiv_stress} > max range {np.max(cycles['range'])}"
        
        # Test with default N_eq
        equiv_stress_default = calculate_equivalent_stress(cycles, curve)
        assert equiv_stress_default > 0


class TestFatigueSafetyAssessment:
    """Test fatigue safety assessment."""
    
    def test_safe_assessment(self):
        """Test assessment for safe case."""
        # Low stress cycles
        curve = EurocodeCategory.get_curve('71')
        cycles = np.array(
            [(50.0, 25.0, 10.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        util, status, details = assess_fatigue_safety(
            cycles, curve, design_life=100
        )
        
        assert util < 1.0
        assert status in ['PASS', 'WARNING']
        assert 'damage_per_cycle' in details
        assert 'actual_life' in details
    
    def test_failure_assessment(self):
        """Test assessment for failure case."""
        # High stress cycles
        curve = EurocodeCategory.get_curve('71')
        cycles = np.array(
            [(150.0, 75.0, 100.0)],  # High count of high stress
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        util, status, details = assess_fatigue_safety(
            cycles, curve, design_life=1e6  # Very long design life
        )
        
        # Should likely fail with such high stress and long life
        assert util > 0  # Some utilization
    
    def test_reserve_factor(self):
        """Test reserve factor calculation."""
        cycles = np.array(
            [(100.0, 50.0, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        util, status, details = assess_fatigue_safety(cycles, curve, design_life=1.0)
        
        # Reserve factor should be 1/utilization
        if util > 0:
            assert details['reserve_factor'] == pytest.approx(1.0 / util, rel=1e-6)


class TestDamageContribution:
    """Test damage contribution analysis."""
    
    def test_damage_contribution(self):
        """Test damage contribution analysis."""
        cycles = np.array(
            [(100.0, 50.0, 5.0), (80.0, 40.0, 10.0), (60.0, 30.0, 15.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        curve = EurocodeCategory.get_curve('71')
        
        bins, counts, damage_fractions = damage_contribution_analysis(
            cycles, curve, n_bins=5
        )
        
        assert len(bins) == 5
        assert len(damage_fractions) == 5
        
        # Damage fractions should sum to ~1.0
        assert np.sum(damage_fractions) == pytest.approx(1.0, rel=1e-6)
        
        # All fractions should be non-negative
        assert np.all(damage_fractions >= 0)
    
    def test_empty_cycles_contribution(self):
        """Test empty cycles for contribution analysis."""
        cycles = np.array([], dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')])
        curve = EurocodeCategory.get_curve('71')
        
        bins, counts, damage_fractions = damage_contribution_analysis(cycles, curve)
        
        assert len(bins) == 0


class TestIntegration:
    """Integration tests with realistic scenarios."""
    
    def test_realistic_scenario(self):
        """Test with realistic stress history."""
        np.random.seed(42)
        
        # Generate realistic stress history
        signal = np.random.randn(1000) * 30 + 100
        
        # Rainflow count
        cycles = rainflow_count(signal)
        
        # Select fatigue curve
        curve = EurocodeCategory.get_curve('71')
        
        # Calculate damage
        damage = calculate_damage(cycles, curve)
        
        # Calculate life
        life = calculate_life(cycles, curve)
        
        # Should have some damage
        assert damage > 0
        assert np.isfinite(damage)
        
        # Life should be positive
        assert life > 0
        
        # Damage * life should equal 1
        if np.isfinite(life):
            assert damage * life == pytest.approx(1.0, rel=1e-6)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

