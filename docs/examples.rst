Exemples d'utilisation
======================

Cette section présente des exemples pratiques d'utilisation d'OpenRainflow.

Exemple basique
---------------

Analyse de fatigue simple d'un historique de contrainte.

.. literalinclude:: ../examples/basic_usage.py
   :language: python
   :lines: 1-50

Sortie attendue :

.. code-block:: text

   ======================================================================
   OPENRAINFLOW - BASIC USAGE EXAMPLE
   ======================================================================
   
   1. Generating sample stress history...
      Generated 10000 stress values
      Mean: 100.05 MPa
      Std: 49.98 MPa
   
   2. Performing rainflow cycle counting...
      Total cycles identified: 5024
      Full cycles: 2512
      Half cycles: 2512
   
   3. Selecting Eurocode fatigue curve...
      Selected category: 71
      Characteristic strength (2M cycles): 71.0 MPa
   
   4. Calculating cumulative damage (Miner's rule)...
      Damage per load cycle: 3.456e-04
   
   5. Calculating fatigue life...
      Expected life: 2.89e+03 repetitions

Analyse avancée avec parallélisation
-------------------------------------

Traitement de multiples signaux en parallèle.

.. literalinclude:: ../examples/advanced_analysis.py
   :language: python
   :lines: 1-80

Courbes de fatigue personnalisées
----------------------------------

Création et utilisation de courbes S-N personnalisées.

.. literalinclude:: ../examples/custom_fatigue_curve.py
   :language: python
   :lines: 1-60

Comparaison de matériaux
~~~~~~~~~~~~~~~~~~~~~~~~~

Comparer différents matériaux pour un même chargement :

.. code-block:: python

   from openrainflow import rainflow_count, calculate_life
   from openrainflow.eurocode import create_custom_curve
   import matplotlib.pyplot as plt

   # Chargement commun
   stress = np.loadtxt('component_stress.txt')
   cycles = rainflow_count(stress)

   # Définir différents matériaux
   materials = {
       'Acier S355 (Cat 71)': create_custom_curve('S355', 71.0, m1=3.0),
       'Acier S690 (Cat 90)': create_custom_curve('S690', 90.0, m1=3.0),
       'Aluminium 6061': create_custom_curve('AL6061', 65.0, m1=4.0, m2=6.0),
       'Acier inox 316': create_custom_curve('SS316', 75.0, m1=3.5),
   }

   # Calculer la vie pour chaque matériau
   lives = {}
   for name, curve in materials.items():
       life = calculate_life(cycles, curve)
       lives[name] = life
       print(f"{name:25s}: {life:.2e} répétitions")

   # Visualisation
   fig, ax = plt.subplots(figsize=(10, 6))
   names = list(lives.keys())
   values = list(lives.values())
   
   ax.barh(names, np.log10(values))
   ax.set_xlabel('Log₁₀(Vie [répétitions])')
   ax.set_title('Comparaison de durée de vie par matériau')
   ax.grid(True, alpha=0.3)
   plt.tight_layout()
   plt.savefig('material_comparison.png', dpi=150)

Optimisation de conception
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Trouver la catégorie minimale acceptable :

.. code-block:: python

   from openrainflow import rainflow_count, calculate_damage
   from openrainflow.eurocode import EurocodeCategory

   # Chargement de conception
   design_load = np.loadtxt('design_load.txt')
   cycles = rainflow_count(design_load)

   # Critères
   design_life = 5000  # répétitions
   safety_factor = 1.25
   max_utilization = 0.80  # 80%

   # Tester toutes les catégories
   categories = EurocodeCategory.list_categories()
   
   print("Recherche de la catégorie optimale...\n")
   
   optimal = None
   for cat in reversed(categories):  # Commencer par la plus faible
       curve = EurocodeCategory.get_curve(cat)
       damage = calculate_damage(
           cycles, 
           curve, 
           partial_safety_factor=safety_factor
       )
       utilization = damage * design_life
       
       status = "✓" if utilization <= max_utilization else "✗"
       print(f"{status} Cat {cat:3s}: Utilisation = {utilization:.2%}")
       
       if utilization <= max_utilization and optimal is None:
           optimal = cat

   print(f"\n→ Catégorie minimale recommandée : {optimal}")

Traitement de très grandes données
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour des fichiers de mesure très volumineux :

.. code-block:: python

   from openrainflow.parallel import parallel_rainflow_batch
   from openrainflow import calculate_damage
   from openrainflow.eurocode import EurocodeCategory

   # Charger un très grand fichier (ex: 50 millions de points)
   # En pratique, utiliser memmap pour éviter saturation mémoire
   import numpy as np
   
   # Créer memmap pour grand fichier
   big_data = np.memmap(
       'huge_stress_history.dat', 
       dtype='float64', 
       mode='r', 
       shape=(50_000_000,)
   )

   # Traitement parallèle par batch
   print("Traitement par batch...")
   cycles = parallel_rainflow_batch(
       big_data[:],  # Charger en RAM si possible, sinon traiter par segments
       batch_size=5_000_000,
       n_jobs=8,
       overlap=1000
   )

   print(f"Cycles identifiés : {len(cycles)}")

   # Calcul de dommage
   curve = EurocodeCategory.get_curve('71')
   damage = calculate_damage(cycles, curve)
   
   print(f"Dommage : {damage:.6e}")

