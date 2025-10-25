"""
Benchmark de vitesse : comparaison OpenRainflow vs fatpack vs rainflow
"""

import numpy as np
import time
import sys
from pathlib import Path
import warnings

# Supprimer les warnings pour une sortie propre
warnings.filterwarnings('ignore')

print("""
╔═══════════════════════════════════════════════════════════════════╗
║              BENCHMARK VITESSE - Rainflow Counting                ║
╚═══════════════════════════════════════════════════════════════════╝
""")

# Vérifier la disponibilité des packages
packages_available = {}

# OpenRainflow
try:
    from openrainflow import rainflow_count
    packages_available['openrainflow'] = True
    print("✓ OpenRainflow importé")
except ImportError:
    packages_available['openrainflow'] = False
    print("✗ OpenRainflow non disponible")

# fatpack
try:
    import fatpack
    packages_available['fatpack'] = True
    print("✓ fatpack importé")
except ImportError:
    packages_available['fatpack'] = False
    print("✗ fatpack non disponible (pip install fatpack)")

# rainflow
try:
    import rainflow as rf_package
    packages_available['rainflow'] = True
    print("✓ rainflow importé")
except ImportError:
    packages_available['rainflow'] = False
    print("✗ rainflow non disponible (pip install rainflow)")

if not any(packages_available.values()):
    print("\n❌ Aucun package disponible pour le benchmark!")
    sys.exit(1)

print("\n" + "="*70)
print("Configuration du benchmark")
print("="*70)

# Tailles de signaux à tester
signal_sizes = [100, 1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]
n_runs = 5  # Nombre de répétitions pour moyenne

print(f"Tailles de signaux testées : {signal_sizes}")
print(f"Nombre de runs par taille : {n_runs}")
print(f"Seed aléatoire : 42 (reproductibilité)")

# Préparer les signaux
np.random.seed(42)
signals = {}
for size in signal_sizes:
    signals[size] = np.random.randn(size) * 50 + 100

print("\n" + "="*70)
print("Exécution des benchmarks")
print("="*70)

results = {
    'openrainflow': {},
    'openrainflow_cached': {},
    'fatpack': {},
    'rainflow': {}
}

# Fonction de benchmark
def benchmark_function(func, signal, name):
    """Benchmark une fonction de comptage rainflow."""
    times = []
    for run in range(n_runs):
        start = time.perf_counter()
        try:
            result = func(signal)
            end = time.perf_counter()
            times.append(end - start)
        except Exception as e:
            print(f"  ✗ Erreur dans {name}: {e}")
            return None
    
    return {
        'mean': np.mean(times),
        'std': np.std(times),
        'min': np.min(times),
        'max': np.max(times)
    }

# Benchmark OpenRainflow
if packages_available['openrainflow']:
    print("\n📊 OpenRainflow (avec compilation JIT)")
    print("-" * 70)
    
    for size in signal_sizes:
        signal = signals[size]
        print(f"\n  Signal: {size:>9,} points")
        
        # Premier appel (avec compilation)
        print(f"    Premier appel (avec compilation JIT)...", end=' ')
        result = benchmark_function(rainflow_count, signal, 'openrainflow')
        if result:
            results['openrainflow'][size] = result
            print(f"{result['mean']*1000:.2f} ms ± {result['std']*1000:.2f}")
        
        # Appels suivants (cached)
        print(f"    Appels suivants (JIT cached)...", end=' ')
        result = benchmark_function(rainflow_count, signal, 'openrainflow_cached')
        if result:
            results['openrainflow_cached'][size] = result
            print(f"{result['mean']*1000:.2f} ms ± {result['std']*1000:.2f}")
            speedup = results['openrainflow'][size]['mean'] / result['mean']
            print(f"    → Speedup après compilation: {speedup:.1f}x")

# Benchmark fatpack
if packages_available['fatpack']:
    print("\n📊 fatpack")
    print("-" * 70)
    
    def fatpack_count(signal):
        return fatpack.find_rainflow_ranges(signal)
    
    for size in signal_sizes:
        signal = signals[size]
        print(f"  Signal: {size:>9,} points...", end=' ')
        
        result = benchmark_function(fatpack_count, signal, 'fatpack')
        if result:
            results['fatpack'][size] = result
            print(f"{result['mean']*1000:.2f} ms ± {result['std']*1000:.2f}")

# Benchmark rainflow
if packages_available['rainflow']:
    print("\n📊 rainflow")
    print("-" * 70)
    
    def rainflow_count_pkg(signal):
        return list(rf_package.extract_cycles(signal))
    
    for size in signal_sizes:
        signal = signals[size]
        print(f"  Signal: {size:>9,} points...", end=' ')
        
        result = benchmark_function(rainflow_count_pkg, signal, 'rainflow')
        if result:
            results['rainflow'][size] = result
            print(f"{result['mean']*1000:.2f} ms ± {result['std']*1000:.2f}")

# Résumé comparatif
print("\n" + "="*70)
print("RÉSUMÉ COMPARATIF")
print("="*70)

print("\nTemps moyens (ms) par taille de signal:")
print("-" * 70)
header = f"{'Taille':<12}"
if packages_available['openrainflow']:
    header += f"{'OpenRF(1st)':<14}{'OpenRF(cached)':<16}"
if packages_available['fatpack']:
    header += f"{'fatpack':<12}"
if packages_available['rainflow']:
    header += f"{'rainflow':<12}"
header += f"{'Speedup':<10}"
print(header)
print("-" * 70)

for size in signal_sizes:
    line = f"{size:<12,}"
    
    if packages_available['openrainflow'] and size in results['openrainflow']:
        t1 = results['openrainflow'][size]['mean'] * 1000
        t2 = results['openrainflow_cached'][size]['mean'] * 1000
        line += f"{t1:<14.2f}{t2:<16.2f}"
    else:
        line += f"{'N/A':<14}{'N/A':<16}"
    
    if packages_available['fatpack'] and size in results['fatpack']:
        t = results['fatpack'][size]['mean'] * 1000
        line += f"{t:<12.2f}"
    else:
        line += f"{'N/A':<12}"
    
    if packages_available['rainflow'] and size in results['rainflow']:
        t = results['rainflow'][size]['mean'] * 1000
        line += f"{t:<12.2f}"
    else:
        line += f"{'N/A':<12}"
    
    # Calculer speedup (OpenRainflow cached vs le plus lent)
    if packages_available['openrainflow'] and size in results['openrainflow_cached']:
        times = []
        if size in results['fatpack']:
            times.append(results['fatpack'][size]['mean'])
        if size in results['rainflow']:
            times.append(results['rainflow'][size]['mean'])
        
        if times:
            max_time = max(times)
            openrf_time = results['openrainflow_cached'][size]['mean']
            speedup = max_time / openrf_time
            line += f"{speedup:<10.2f}x"
    
    print(line)

# Débit (points/seconde)
print("\nDébit (millions de points/seconde):")
print("-" * 70)
header = f"{'Taille':<12}"
if packages_available['openrainflow']:
    header += f"{'OpenRF(cached)':<16}"
if packages_available['fatpack']:
    header += f"{'fatpack':<12}"
if packages_available['rainflow']:
    header += f"{'rainflow':<12}"
print(header)
print("-" * 70)

for size in signal_sizes:
    line = f"{size:<12,}"
    
    if packages_available['openrainflow'] and size in results['openrainflow_cached']:
        t = results['openrainflow_cached'][size]['mean']
        throughput = (size / t) / 1e6
        line += f"{throughput:<16.2f}"
    else:
        line += f"{'N/A':<16}"
    
    if packages_available['fatpack'] and size in results['fatpack']:
        t = results['fatpack'][size]['mean']
        throughput = (size / t) / 1e6
        line += f"{throughput:<12.2f}"
    else:
        line += f"{'N/A':<12}"
    
    if packages_available['rainflow'] and size in results['rainflow']:
        t = results['rainflow'][size]['mean']
        throughput = (size / t) / 1e6
        line += f"{throughput:<12.2f}"
    else:
        line += f"{'N/A':<12}"
    
    print(line)

# Sauvegarder les résultats
print("\n" + "="*70)
print("Sauvegarde des résultats")
print("="*70)

results_dir = Path(__file__).parent / 'results'
results_dir.mkdir(exist_ok=True)

import csv
csv_file = results_dir / 'benchmark_speed.csv'

with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Package', 'Size', 'Mean(s)', 'Std(s)', 'Min(s)', 'Max(s)', 'Throughput(Mpts/s)'])
    
    for pkg_name, pkg_results in results.items():
        for size, timing in pkg_results.items():
            throughput = (size / timing['mean']) / 1e6
            writer.writerow([
                pkg_name, size, 
                timing['mean'], timing['std'], 
                timing['min'], timing['max'],
                throughput
            ])

print(f"✓ Résultats sauvegardés dans : {csv_file}")

# Créer un graphique
try:
    import matplotlib.pyplot as plt
    
    plots_dir = Path(__file__).parent / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Temps d'exécution
    for pkg_name, pkg_results in results.items():
        if pkg_results and pkg_name != 'openrainflow':  # Skip first-run results
            sizes = list(pkg_results.keys())
            times = [pkg_results[s]['mean'] * 1000 for s in sizes]
            
            label = pkg_name.replace('_', ' ').title()
            ax1.loglog(sizes, times, 'o-', linewidth=2, markersize=6, label=label)
    
    ax1.set_xlabel('Taille du signal (points)', fontsize=12)
    ax1.set_ylabel('Temps d\'exécution (ms)', fontsize=12)
    ax1.set_title('Performance de comptage rainflow', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Débit
    for pkg_name, pkg_results in results.items():
        if pkg_results and pkg_name != 'openrainflow':
            sizes = list(pkg_results.keys())
            throughputs = [(s / pkg_results[s]['mean']) / 1e6 for s in sizes]
            
            label = pkg_name.replace('_', ' ').title()
            ax2.semilogx(sizes, throughputs, 'o-', linewidth=2, markersize=6, label=label)
    
    ax2.set_xlabel('Taille du signal (points)', fontsize=12)
    ax2.set_ylabel('Débit (millions points/s)', fontsize=12)
    ax2.set_title('Débit de traitement', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_file = plots_dir / 'benchmark_speed.png'
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✓ Graphique sauvegardé dans : {plot_file}")
    
except ImportError:
    print("ℹ matplotlib non disponible - graphiques non générés")
    print("  Installation : pip install matplotlib")

print("\n" + "="*70)
print("Benchmark terminé !")
print("="*70)

