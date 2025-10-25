"""Tests for visualization module."""

import numpy as np
import pytest

# Check if matplotlib is available
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for testing
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from openrainflow import rainflow_count
from openrainflow.eurocode import EurocodeCategory

# Skip all tests if matplotlib not available
pytestmark = pytest.mark.skipif(
    not MATPLOTLIB_AVAILABLE,
    reason="Matplotlib not installed"
)


@pytest.fixture
def sample_signal():
    """Generate sample signal for testing."""
    np.random.seed(42)
    return np.random.randn(500) * 50 + 100


@pytest.fixture
def sample_cycles(sample_signal):
    """Generate sample cycles for testing."""
    return rainflow_count(sample_signal)


@pytest.fixture
def sample_curve():
    """Get sample fatigue curve."""
    return EurocodeCategory.get_curve('71')


class TestVisualizationImport:
    """Test visualization module import."""
    
    def test_import_visualization(self):
        """Test that visualization can be imported."""
        from openrainflow import visualization
        assert visualization is not None
    
    def test_import_functions(self):
        """Test that visualization functions can be imported."""
        from openrainflow.visualization import (
            plot_rainflow_cycles,
            plot_cycle_histogram,
            plot_damage_contribution,
            plot_sn_curve,
            plot_fatigue_assessment,
            plot_signal_with_cycles,
            plot_multiple_sn_curves
        )
        
        # All should be callable
        assert callable(plot_rainflow_cycles)
        assert callable(plot_cycle_histogram)
        assert callable(plot_damage_contribution)
        assert callable(plot_sn_curve)
        assert callable(plot_fatigue_assessment)
        assert callable(plot_signal_with_cycles)
        assert callable(plot_multiple_sn_curves)


class TestPlotRainflowCycles:
    """Test cycle distribution plotting."""
    
    def test_basic_plot(self, sample_cycles):
        """Test basic cycle distribution plot."""
        from openrainflow.visualization import plot_rainflow_cycles
        
        fig = plot_rainflow_cycles(sample_cycles)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        plt.close(fig)
    
    def test_plot_with_ax(self, sample_cycles):
        """Test plotting on provided axes."""
        from openrainflow.visualization import plot_rainflow_cycles
        
        fig, ax = plt.subplots()
        result_fig = plot_rainflow_cycles(sample_cycles, ax=ax)
        
        assert result_fig is fig
        
        plt.close(fig)
    
    def test_plot_without_half_cycles(self, sample_cycles):
        """Test plotting without showing half cycles separately."""
        from openrainflow.visualization import plot_rainflow_cycles
        
        fig = plot_rainflow_cycles(sample_cycles, show_half_cycles=False)
        
        assert fig is not None
        
        plt.close(fig)


class TestPlotCycleHistogram:
    """Test cycle histogram plotting."""
    
    def test_basic_histogram(self, sample_cycles):
        """Test basic histogram plot."""
        from openrainflow.visualization import plot_cycle_histogram
        
        fig = plot_cycle_histogram(sample_cycles, n_bins=20)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        plt.close(fig)
    
    def test_histogram_with_different_bins(self, sample_cycles):
        """Test histogram with different bin counts."""
        from openrainflow.visualization import plot_cycle_histogram
        
        for n_bins in [10, 15, 30]:
            fig = plot_cycle_histogram(sample_cycles, n_bins=n_bins)
            assert fig is not None
            plt.close(fig)


class TestPlotDamageContribution:
    """Test damage contribution plotting."""
    
    def test_basic_damage_plot(self, sample_cycles, sample_curve):
        """Test basic damage contribution plot."""
        from openrainflow.visualization import plot_damage_contribution
        
        fig = plot_damage_contribution(sample_cycles, sample_curve, n_bins=15)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        plt.close(fig)
    
    def test_damage_plot_with_ax(self, sample_cycles, sample_curve):
        """Test damage plot on provided axes."""
        from openrainflow.visualization import plot_damage_contribution
        
        fig, ax = plt.subplots()
        result_fig = plot_damage_contribution(sample_cycles, sample_curve, ax=ax)
        
        assert result_fig is fig
        
        plt.close(fig)


class TestPlotSNCurve:
    """Test S-N curve plotting."""
    
    def test_basic_sn_curve(self, sample_curve):
        """Test basic S-N curve plot."""
        from openrainflow.visualization import plot_sn_curve
        
        fig = plot_sn_curve(sample_curve)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        plt.close(fig)
    
    def test_sn_curve_with_data_points(self, sample_curve):
        """Test S-N curve with data points."""
        from openrainflow.visualization import plot_sn_curve
        
        data_points = np.array([80, 100, 120, 150])
        fig = plot_sn_curve(sample_curve, show_data_points=data_points)
        
        assert fig is not None
        
        plt.close(fig)
    
    def test_multiple_curves(self):
        """Test plotting multiple S-N curves."""
        from openrainflow.visualization import plot_multiple_sn_curves
        
        curve_names = ['71', '56', '40']
        fig = plot_multiple_sn_curves(curve_names)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        plt.close(fig)


class TestPlotFatigueAssessment:
    """Test complete assessment plotting."""
    
    def test_basic_assessment(self, sample_cycles, sample_curve):
        """Test basic fatigue assessment dashboard."""
        from openrainflow.visualization import plot_fatigue_assessment
        
        fig = plot_fatigue_assessment(sample_cycles, sample_curve, design_life=1000)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        # Check that it has 4 subplots (2x2)
        axes = fig.get_axes()
        assert len(axes) == 4
        
        plt.close(fig)


class TestPlotSignalWithCycles:
    """Test signal plotting with cycles."""
    
    def test_basic_signal_plot(self, sample_signal, sample_cycles):
        """Test basic signal plot."""
        from openrainflow.visualization import plot_signal_with_cycles
        
        fig = plot_signal_with_cycles(sample_signal, sample_cycles)
        
        assert fig is not None
        assert isinstance(fig, plt.Figure)
        
        plt.close(fig)
    
    def test_signal_plot_with_max_cycles(self, sample_signal, sample_cycles):
        """Test signal plot with limited cycle display."""
        from openrainflow.visualization import plot_signal_with_cycles
        
        fig = plot_signal_with_cycles(
            sample_signal, sample_cycles, max_cycles_to_show=5
        )
        
        assert fig is not None
        
        plt.close(fig)


class TestPlotIntegration:
    """Integration tests for plotting."""
    
    def test_complete_workflow(self):
        """Test complete visualization workflow."""
        from openrainflow.visualization import (
            plot_rainflow_cycles,
            plot_cycle_histogram,
            plot_damage_contribution,
            plot_fatigue_assessment
        )
        
        # Generate signal
        np.random.seed(42)
        signal = np.random.randn(1000) * 50 + 100
        
        # Count cycles
        cycles = rainflow_count(signal)
        
        # Get curve
        curve = EurocodeCategory.get_curve('71')
        
        # Create all plots
        figs = []
        figs.append(plot_rainflow_cycles(cycles))
        figs.append(plot_cycle_histogram(cycles))
        figs.append(plot_damage_contribution(cycles, curve))
        figs.append(plot_fatigue_assessment(cycles, curve))
        
        # All should be valid
        for fig in figs:
            assert fig is not None
            assert isinstance(fig, plt.Figure)
            plt.close(fig)
    
    def test_save_figure(self, sample_cycles, tmp_path):
        """Test saving figure to file."""
        from openrainflow.visualization import plot_cycle_histogram
        
        fig = plot_cycle_histogram(sample_cycles)
        
        # Save to temporary file
        output_file = tmp_path / "test_figure.png"
        fig.savefig(output_file, dpi=100, bbox_inches='tight')
        
        # Check file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        plt.close(fig)


class TestEdgeCases:
    """Test edge cases in visualization."""
    
    def test_empty_cycles(self):
        """Test plotting with empty cycles."""
        from openrainflow.visualization import plot_rainflow_cycles
        
        empty_cycles = np.array(
            [],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        # Should handle gracefully (may show empty plot)
        fig = plot_rainflow_cycles(empty_cycles)
        assert fig is not None
        plt.close(fig)
    
    def test_single_cycle(self):
        """Test plotting with single cycle."""
        from openrainflow.visualization import plot_cycle_histogram
        
        single_cycle = np.array(
            [(100.0, 50.0, 1.0)],
            dtype=[('range', 'f8'), ('mean', 'f8'), ('count', 'f8')]
        )
        
        fig = plot_cycle_histogram(single_cycle)
        assert fig is not None
        plt.close(fig)
    
    def test_very_large_signal(self):
        """Test plotting with large signal."""
        from openrainflow.visualization import plot_signal_with_cycles
        
        # Large signal
        large_signal = np.random.randn(10000) * 50 + 100
        cycles = rainflow_count(large_signal)
        
        # Should still work (though may be slow)
        fig = plot_signal_with_cycles(large_signal, cycles)
        assert fig is not None
        plt.close(fig)


class TestCustomization:
    """Test plot customization options."""
    
    def test_custom_figsize(self, sample_cycles):
        """Test custom figure size."""
        from openrainflow.visualization import plot_rainflow_cycles
        
        fig = plot_rainflow_cycles(sample_cycles, figsize=(12, 8))
        
        # Check size
        size = fig.get_size_inches()
        assert size[0] == pytest.approx(12)
        assert size[1] == pytest.approx(8)
        
        plt.close(fig)
    
    def test_custom_bins(self, sample_cycles):
        """Test custom bin counts."""
        from openrainflow.visualization import plot_cycle_histogram
        
        for n_bins in [5, 10, 20, 50]:
            fig = plot_cycle_histogram(sample_cycles, n_bins=n_bins)
            assert fig is not None
            plt.close(fig)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

