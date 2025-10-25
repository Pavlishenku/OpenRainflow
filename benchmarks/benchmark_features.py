"""
Comparaison des fonctionnalités disponibles dans chaque package
"""

print("""
╔═══════════════════════════════════════════════════════════════════╗
║        COMPARAISON DES FONCTIONNALITÉS - Packages Rainflow        ║
╚═══════════════════════════════════════════════════════════════════╝
""")

import sys

# Tester disponibilité
packages = {}

try:
    import openrainflow
    packages['openrainflow'] = openrainflow
    print("✓ OpenRainflow v" + openrainflow.__version__)
except ImportError:
    print("✗ OpenRainflow non disponible")

try:
    import fatpack
    packages['fatpack'] = fatpack
    print("✓ fatpack")
except ImportError:
    print("✗ fatpack non disponible")

try:
    import rainflow
    packages['rainflow'] = rainflow
    print("✓ rainflow")
except ImportError:
    print("✗ rainflow non disponible")

print("\n" + "="*70)
print("MATRICE DES FONCTIONNALITÉS")
print("="*70)

features = {
    'Comptage rainflow': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': True,
    },
    'Courbes S-N intégrées': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': False,
    },
    'Courbes Eurocode': {
        'openrainflow': True,
        'fatpack': False,
        'rainflow': False,
    },
    'Calcul de dommage Miner': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': False,
    },
    'Calcul de durée de vie': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': False,
    },
    'Facteurs de sécurité': {
        'openrainflow': True,
        'fatpack': False,
        'rainflow': False,
    },
    'Analyse de contribution': {
        'openrainflow': True,
        'fatpack': False,
        'rainflow': False,
    },
    'Traitement parallèle': {
        'openrainflow': True,
        'fatpack': False,
        'rainflow': False,
    },
    'Optimisation JIT (Numba)': {
        'openrainflow': True,
        'fatpack': False,
        'rainflow': False,
    },
    'Documentation Sphinx': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': False,
    },
    'Tests unitaires': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': True,
    },
    'Exemples d\'utilisation': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': True,
    },
    'Visualisation S-N': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': False,
    },
    'Export résultats': {
        'openrainflow': True,
        'fatpack': False,
        'rainflow': False,
    },
    'Courbes personnalisées': {
        'openrainflow': True,
        'fatpack': True,
        'rainflow': False,
    },
}

# Afficher la matrice
print(f"\n{'Fonctionnalité':<30} {'OpenRainflow':<15} {'fatpack':<15} {'rainflow':<15}")
print("-" * 75)

for feature, support in features.items():
    line = f"{feature:<30}"
    for pkg in ['openrainflow', 'fatpack', 'rainflow']:
        if pkg in packages:
            status = "✓" if support.get(pkg, False) else "✗"
            line += f"{status:<15}"
        else:
            line += f"{'N/A':<15}"
    print(line)

# Score total
print("\n" + "="*70)
print("SCORE DE FONCTIONNALITÉS")
print("="*70)

for pkg in ['openrainflow', 'fatpack', 'rainflow']:
    if pkg in packages:
        score = sum(1 for f, s in features.items() if s.get(pkg, False))
        total = len(features)
        percentage = (score / total) * 100
        
        print(f"{pkg.title():<15}: {score:>2}/{total} ({percentage:>5.1f}%)")
        
        # Barre de progression
        bar_length = 40
        filled = int(bar_length * percentage / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"                {bar}")

# Analyse détaillée
print("\n" + "="*70)
print("ANALYSE DÉTAILLÉE")
print("="*70)

if 'openrainflow' in packages:
    print("""
OpenRainflow - Package complet d'analyse de fatigue
---------------------------------------------------
✓ Workflow complet : comptage → courbe S-N → dommage → durée de vie
✓ Optimisation Numba pour haute performance
✓ Support Eurocode EN 1993-1-9 (14 catégories)
✓ Parallélisation multi-signaux
✓ Analyse avancée (contribution, équivalent, etc.)
✓ Documentation professionnelle Sphinx
✓ 50+ tests unitaires
    """)

if 'fatpack' in packages:
    print("""
fatpack - Package mature d'analyse de fatigue
----------------------------------------------
✓ Implémentation éprouvée du rainflow
✓ Support de plusieurs courbes S-N
✓ Calcul de dommage
✓ Bonne documentation
✗ Pas d'optimisation JIT
✗ Pas de parallélisation native
✗ Pas de support Eurocode spécifique
    """)

if 'rainflow' in packages:
    print("""
rainflow - Package léger de comptage
-------------------------------------
✓ Implémentation simple et directe
✓ Léger et facile à utiliser
✗ Comptage rainflow uniquement
✗ Pas de courbes S-N
✗ Pas de calcul de dommage
✗ Documentation minimale
    """)

# Cas d'usage recommandés
print("="*70)
print("CAS D'USAGE RECOMMANDÉS")
print("="*70)

print("""
OpenRainflow :
--------------
• Analyse complète de fatigue selon Eurocode
• Projets nécessitant haute performance
• Traitement de multiples signaux en parallèle
• Besoin de workflow intégré (comptage → dommage)
• Documentation et support requis

fatpack :
---------
• Analyse de fatigue générale
• Projets sans besoin de performance extrême
• Utilisation de courbes S-N non-Eurocode
• Besoin de package mature et stable

rainflow :
----------
• Comptage rainflow uniquement
• Intégration dans pipeline personnalisé
• Besoin de package minimal et léger
• Pas de calcul de dommage requis
""")

print("="*70)
print("Comparaison terminée !")
print("="*70)

