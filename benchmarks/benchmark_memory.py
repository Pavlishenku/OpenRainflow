"""
Benchmark mémoire : mesure de l'utilisation mémoire
"""

import numpy as np
import sys
import warnings
from pathlib import Path
import tracemalloc

warnings.filterwarnings('ignore')

print("""
╔═══════════════════════════════════════════════════════════════════╗
║          BENCHMARK MÉMOIRE - Rainflow Counting                    ║
╚═══════════════════════════════════════════════════════════════════╝
""")

# Vérifier disponibilité
packages_available = {}

try:
    from openrainflow import rainflow_count
    packages_available['openrainflow'] = True
    print("✓ OpenRainflow importé")
except ImportError:
    packages_available['openrainflow'] = False
    print("✗ OpenRainflow non disponible")

try:
    import fatpack
    packages_available['fatpack'] = True
    print("✓ fatpack importé")
except ImportError:
    packages_available['fatpack'] = False
    print("✗ fatpack non disponible")

try:
    import rainflow as rf_package
    packages_available['rainflow'] = True
    print("✓ rainflow importé")
except ImportError:
    packages_available['rainflow'] = False
    print("✗ rainflow non disponible")

print("\n" + "="*70)
print("Configuration")
print("="*70)

signal_sizes = [10_000, 100_000, 500_000, 1_000_000, 5_000_000]
print(f"Tailles testées : {[f'{s:,}' for s in signal_sizes]}")

print("\n" + "="*70)
print("Mesures mémoire")
print("="*70)

results = {}

def measure_memory(func, signal, name):
    """Mesure l'utilisation mémoire d'une fonction."""
    tracemalloc.start()
    
    # Mesure de base
    baseline = tracemalloc.get_traced_memory()[0]
    
    try:
        # Exécuter la fonction
        result = func(signal)
        
        # Mesure après exécution
        current, peak = tracemalloc.get_traced_memory()
        
        tracemalloc.stop()
        
        return {
            'current_mb': (current - baseline) / 1024 / 1024,
            'peak_mb': (peak - baseline) / 1024 / 1024,
            'signal_mb': signal.nbytes / 1024 / 1024
        }
    except Exception as e:
        tracemalloc.stop()
        print(f"  ✗ Erreur: {e}")
        return None

np.random.seed(42)

# OpenRainflow
if packages_available['openrainflow']:
    print("\n📊 OpenRainflow")
    print("-" * 70)
    results['openrainflow'] = {}
    
    for size in signal_sizes:
        signal = np.random.randn(size) * 50 + 100
        print(f"  Signal: {size:>10,} points ({signal.nbytes/1024/1024:.2f} MB)...", end=' ')
        
        mem = measure_memory(rainflow_count, signal, 'openrainflow')
        if mem:
            results['openrainflow'][size] = mem
            ratio = mem['peak_mb'] / mem['signal_mb']
            print(f"Pic: {mem['peak_mb']:.2f} MB (ratio: {ratio:.2f}x)")
        
        del signal  # Libérer mémoire

# fatpack
if packages_available['fatpack']:
    print("\n📊 fatpack")
    print("-" * 70)
    results['fatpack'] = {}
    
    def fatpack_count(signal):
        return fatpack.find_rainflow_ranges(signal)
    
    for size in signal_sizes:
        signal = np.random.randn(size) * 50 + 100
        print(f"  Signal: {size:>10,} points ({signal.nbytes/1024/1024:.2f} MB)...", end=' ')
        
        mem = measure_memory(fatpack_count, signal, 'fatpack')
        if mem:
            results['fatpack'][size] = mem
            ratio = mem['peak_mb'] / mem['signal_mb']
            print(f"Pic: {mem['peak_mb']:.2f} MB (ratio: {ratio:.2f}x)")
        
        del signal

# rainflow
if packages_available['rainflow']:
    print("\n📊 rainflow")
    print("-" * 70)
    results['rainflow'] = {}
    
    def rainflow_count_pkg(signal):
        return list(rf_package.extract_cycles(signal))
    
    for size in signal_sizes:
        signal = np.random.randn(size) * 50 + 100
        print(f"  Signal: {size:>10,} points ({signal.nbytes/1024/1024:.2f} MB)...", end=' ')
        
        mem = measure_memory(rainflow_count_pkg, signal, 'rainflow')
        if mem:
            results['rainflow'][size] = mem
            ratio = mem['peak_mb'] / mem['signal_mb']
            print(f"Pic: {mem['peak_mb']:.2f} MB (ratio: {ratio:.2f}x)")
        
        del signal

# Résumé
print("\n" + "="*70)
print("RÉSUMÉ - Utilisation mémoire pic (MB)")
print("="*70)

header = f"{'Taille':<12}{'Signal':<12}"
if packages_available['openrainflow']:
    header += f"{'OpenRF':<12}"
if packages_available['fatpack']:
    header += f"{'fatpack':<12}"
if packages_available['rainflow']:
    header += f"{'rainflow':<12}"
header += f"{'Meilleur':<12}"
print(header)
print("-" * 70)

for size in signal_sizes:
    signal_mb = (size * 8) / 1024 / 1024  # float64 = 8 bytes
    line = f"{size:<12,}{signal_mb:<12.2f}"
    
    memories = {}
    
    if packages_available['openrainflow'] and size in results['openrainflow']:
        m = results['openrainflow'][size]['peak_mb']
        line += f"{m:<12.2f}"
        memories['openrainflow'] = m
    else:
        line += f"{'N/A':<12}"
    
    if packages_available['fatpack'] and size in results['fatpack']:
        m = results['fatpack'][size]['peak_mb']
        line += f"{m:<12.2f}"
        memories['fatpack'] = m
    else:
        line += f"{'N/A':<12}"
    
    if packages_available['rainflow'] and size in results['rainflow']:
        m = results['rainflow'][size]['peak_mb']
        line += f"{m:<12.2f}"
        memories['rainflow'] = m
    else:
        line += f"{'N/A':<12}"
    
    if memories:
        best = min(memories.values())
        best_pkg = [k for k, v in memories.items() if v == best][0]
        line += f"{best_pkg:<12}"
    
    print(line)

print("\nRatio mémoire/signal:")
print("-" * 70)
header = f"{'Taille':<12}"
if packages_available['openrainflow']:
    header += f"{'OpenRF':<12}"
if packages_available['fatpack']:
    header += f"{'fatpack':<12}"
if packages_available['rainflow']:
    header += f"{'rainflow':<12}"
print(header)
print("-" * 70)

for size in signal_sizes:
    line = f"{size:<12,}"
    
    if packages_available['openrainflow'] and size in results['openrainflow']:
        ratio = results['openrainflow'][size]['peak_mb'] / results['openrainflow'][size]['signal_mb']
        line += f"{ratio:<12.2f}x"
    else:
        line += f"{'N/A':<12}"
    
    if packages_available['fatpack'] and size in results['fatpack']:
        ratio = results['fatpack'][size]['peak_mb'] / results['fatpack'][size]['signal_mb']
        line += f"{ratio:<12.2f}x"
    else:
        line += f"{'N/A':<12}"
    
    if packages_available['rainflow'] and size in results['rainflow']:
        ratio = results['rainflow'][size]['peak_mb'] / results['rainflow'][size]['signal_mb']
        line += f"{ratio:<12.2f}x"
    else:
        line += f"{'N/A':<12}"
    
    print(line)

# Sauvegarder
print("\n" + "="*70)
print("Sauvegarde")
print("="*70)

results_dir = Path(__file__).parent / 'results'
results_dir.mkdir(exist_ok=True)

import csv
csv_file = results_dir / 'benchmark_memory.csv'

with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Package', 'Size', 'Signal_MB', 'Current_MB', 'Peak_MB', 'Ratio'])
    
    for pkg_name, pkg_results in results.items():
        for size, mem in pkg_results.items():
            writer.writerow([
                pkg_name, size,
                mem['signal_mb'], mem['current_mb'], mem['peak_mb'],
                mem['peak_mb'] / mem['signal_mb']
            ])

print(f"✓ Résultats sauvegardés : {csv_file}")

# Graphique
try:
    import matplotlib.pyplot as plt
    
    plots_dir = Path(__file__).parent / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Mémoire absolue
    for pkg_name, pkg_results in results.items():
        sizes = list(pkg_results.keys())
        peaks = [pkg_results[s]['peak_mb'] for s in sizes]
        
        ax1.plot(sizes, peaks, 'o-', linewidth=2, markersize=6, 
                label=pkg_name.title())
    
    # Ligne de référence (taille du signal)
    signal_sizes_mb = [s * 8 / 1024 / 1024 for s in signal_sizes]
    ax1.plot(signal_sizes, signal_sizes_mb, '--', linewidth=2, 
            alpha=0.5, color='gray', label='Taille signal')
    
    ax1.set_xlabel('Taille du signal (points)', fontsize=12)
    ax1.set_ylabel('Mémoire pic (MB)', fontsize=12)
    ax1.set_title('Utilisation mémoire', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    
    # Plot 2: Ratio
    for pkg_name, pkg_results in results.items():
        sizes = list(pkg_results.keys())
        ratios = [pkg_results[s]['peak_mb'] / pkg_results[s]['signal_mb'] 
                 for s in sizes]
        
        ax2.semilogx(sizes, ratios, 'o-', linewidth=2, markersize=6,
                    label=pkg_name.title())
    
    ax2.axhline(1.0, linestyle='--', color='gray', alpha=0.5, 
               label='Taille signal (1x)')
    ax2.set_xlabel('Taille du signal (points)', fontsize=12)
    ax2.set_ylabel('Ratio mémoire/signal', fontsize=12)
    ax2.set_title('Efficacité mémoire', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = plots_dir / 'benchmark_memory.png'
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✓ Graphique sauvegardé : {plot_file}")
    
except ImportError:
    print("ℹ matplotlib non disponible")

print("\n" + "="*70)
print("Benchmark mémoire terminé !")
print("="*70)

