"""
Exécuter tous les benchmarks
"""

import subprocess
import sys
from pathlib import Path

print("""
╔═══════════════════════════════════════════════════════════════════╗
║             SUITE COMPLÈTE DE BENCHMARKS - OpenRainflow           ║
╚═══════════════════════════════════════════════════════════════════╝
""")

benchmarks_dir = Path(__file__).parent

benchmarks = [
    ('benchmark_speed.py', 'Vitesse d\'exécution'),
    ('benchmark_accuracy.py', 'Précision des résultats'),
    ('benchmark_memory.py', 'Utilisation mémoire'),
]

print("Benchmarks à exécuter:")
for i, (script, desc) in enumerate(benchmarks, 1):
    print(f"  {i}. {desc} ({script})")

print("\n" + "="*70)

for i, (script, desc) in enumerate(benchmarks, 1):
    print(f"\n{'='*70}")
    print(f"BENCHMARK {i}/{len(benchmarks)}: {desc}")
    print(f"{'='*70}\n")
    
    script_path = benchmarks_dir / script
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=benchmarks_dir
    )
    
    if result.returncode != 0:
        print(f"\n⚠ Benchmark {script} terminé avec des erreurs")
    else:
        print(f"\n✓ Benchmark {script} terminé avec succès")

print("\n" + "="*70)
print("TOUS LES BENCHMARKS TERMINÉS")
print("="*70)

results_dir = benchmarks_dir / 'results'
plots_dir = benchmarks_dir / 'plots'

if results_dir.exists():
    print(f"\n📊 Résultats disponibles dans : {results_dir}")
    for csv_file in results_dir.glob('*.csv'):
        print(f"  - {csv_file.name}")

if plots_dir.exists():
    print(f"\n📈 Graphiques disponibles dans : {plots_dir}")
    for plot_file in plots_dir.glob('*.png'):
        print(f"  - {plot_file.name}")

print("\n" + "="*70)

