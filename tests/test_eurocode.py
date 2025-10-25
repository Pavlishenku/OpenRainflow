"""Tests for Eurocode fatigue curves."""

import numpy as np
import pytest
from openrainflow.eurocode import (
    EurocodeCategory, FatigueCurve, create_custom_curve, EUROCODE_CATEGORIES
)


class TestFatigueCurve:
    """Test FatigueCurve class."""
    
    def test_initialization(self):
        """Test basic initialization."""
        curve = FatigueCurve(name='Test', delta_sigma_c=71.0)
        
        assert curve.name == 'Test'
        assert curve.delta_sigma_c == 71.0
        assert curve.m1 == 3.0  # Default
        assert curve.m2 == 5.0  # Default
    
    def test_cycles_at_reference(self):
        """Test that stress at reference point is correct."""
        delta_sigma_c = 71.0
        curve = FatigueCurve(name='71', delta_sigma_c=delta_sigma_c)
        
        # At 2 million cycles, should get characteristic strength
        N = curve.get_cycles_to_failure(delta_sigma_c)
        assert N == pytest.approx(2e6, rel=1e-6)
    
    def test_inverse_sn_curve(self):
        """Test that stress-to-N and N-to-stress are inverse."""
        curve = FatigueCurve(name='Test', delta_sigma_c=100.0)
        
        # Test several points
        test_N = np.array([1e4, 1e5, 1e6, 1e7])
        
        for N in test_N:
            stress = curve.get_stress_range(N)
            N_recovered = curve.get_cycles_to_failure(stress)
            assert N_recovered == pytest.approx(N, rel=1e-6)
    
    def test_cutoff_limit(self):
        """Test constant amplitude fatigue limit."""
        curve = FatigueCurve(name='Test', delta_sigma_c=71.0)
        
        # Very low stress should give infinite life
        very_low_stress = curve.delta_sigma_L * 0.5
        N = curve.get_cycles_to_failure(very_low_stress, use_cutoff=True)
        assert np.isinf(N)
        
        # Without cutoff, should still get finite value
        N_no_cutoff = curve.get_cycles_to_failure(very_low_stress, use_cutoff=False)
        assert np.isfinite(N_no_cutoff)
    
    def test_damage_per_cycle(self):
        """Test damage calculation."""
        curve = FatigueCurve(name='Test', delta_sigma_c=100.0)
        
        # At characteristic strength
        damage = curve.get_damage_per_cycle(100.0)
        assert damage == pytest.approx(1.0 / 2e6, rel=1e-6)
        
        # Below CAFL
        damage_low = curve.get_damage_per_cycle(curve.delta_sigma_L * 0.5, use_cutoff=True)
        assert damage_low == 0.0
    
    def test_array_input(self):
        """Test that array inputs work."""
        curve = FatigueCurve(name='Test', delta_sigma_c=100.0)
        
        stress_ranges = np.array([50, 75, 100, 125, 150])
        N_values = curve.get_cycles_to_failure(stress_ranges)
        
        assert len(N_values) == len(stress_ranges)
        assert all(np.isfinite(N_values) | np.isinf(N_values))


class TestEurocodeCategory:
    """Test Eurocode category factory."""
    
    def test_valid_categories(self):
        """Test that all standard categories can be created."""
        for category in EUROCODE_CATEGORIES.keys():
            curve = EurocodeCategory.get_curve(category)
            assert curve.name == category
            assert curve.delta_sigma_c == EUROCODE_CATEGORIES[category]
    
    def test_invalid_category(self):
        """Test that invalid category raises error."""
        with pytest.raises(ValueError):
            EurocodeCategory.get_curve('999')
    
    def test_list_categories(self):
        """Test listing available categories."""
        categories = EurocodeCategory.list_categories()
        
        assert len(categories) == len(EUROCODE_CATEGORIES)
        assert '71' in categories
        assert '36' in categories
    
    def test_get_category_strength(self):
        """Test getting strength value."""
        strength = EurocodeCategory.get_category_strength('71')
        assert strength == 71.0
    
    def test_caching(self):
        """Test that curves are cached."""
        curve1 = EurocodeCategory.get_curve('71')
        curve2 = EurocodeCategory.get_curve('71')
        
        # Should be same object (cached)
        assert curve1 is curve2
    
    def test_custom_parameters(self):
        """Test creating curve with custom parameters."""
        curve = EurocodeCategory.get_curve('71', m1=3.5, m2=5.5)
        
        assert curve.m1 == 3.5
        assert curve.m2 == 5.5


class TestCustomCurve:
    """Test custom curve creation."""
    
    def test_basic_custom_curve(self):
        """Test creating a custom curve."""
        curve = create_custom_curve(
            name='Custom',
            delta_sigma_c=85.0,
            m1=3.0
        )
        
        assert curve.name == 'Custom'
        assert curve.delta_sigma_c == 85.0
    
    def test_custom_reference_cycles(self):
        """Test custom curve with different reference cycles."""
        # Specify strength at 1 million cycles instead of 2 million
        curve = create_custom_curve(
            name='Custom',
            delta_sigma_c=100.0,
            N_ref=1e6
        )
        
        # Should adjust internally to 2M reference
        assert curve.N_ref == 2e6
    
    def test_custom_cafl(self):
        """Test custom CAFL."""
        custom_cafl = 30.0
        curve = create_custom_curve(
            name='Custom',
            delta_sigma_c=100.0,
            delta_sigma_L=custom_cafl
        )
        
        assert curve.delta_sigma_L == custom_cafl


class TestSNCurveProperties:
    """Test S-N curve mathematical properties."""
    
    def test_decreasing_stress(self):
        """Test that stress decreases with increasing cycles."""
        curve = EurocodeCategory.get_curve('71')
        
        N_values = np.logspace(3, 8, 100)
        stress_values = curve.get_stress_range(N_values)
        
        # Stress should decrease monotonically (or stay constant after cutoff)
        differences = np.diff(stress_values)
        assert np.all(differences <= 1e-10)  # Allow small numerical errors
    
    def test_knee_point(self):
        """Test knee point transition."""
        curve = EurocodeCategory.get_curve('71')
        
        # Just before knee
        N_before = curve.N_knee * 0.99
        stress_before = curve.get_stress_range(N_before)
        
        # Just after knee
        N_after = curve.N_knee * 1.01
        stress_after = curve.get_stress_range(N_after)
        
        # Stress should be continuous at knee
        assert stress_before > stress_after
        # And close in value (continuous)
        assert abs(stress_before - stress_after) / stress_before < 0.1
    
    def test_high_stress_region(self):
        """Test high stress region (slope m1)."""
        curve = EurocodeCategory.get_curve('71')
        
        # In region 1 (N < N_knee), should follow: N * Δσ^m1 = constant
        N1 = 1e5
        N2 = 2e5
        
        stress1 = curve.get_stress_range(N1)
        stress2 = curve.get_stress_range(N2)
        
        # Check that N * Δσ^m ≈ constant
        C1 = N1 * (stress1 ** curve.m1)
        C2 = N2 * (stress2 ** curve.m1)
        
        assert C1 == pytest.approx(C2, rel=1e-6)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

