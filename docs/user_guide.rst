Guide utilisateur
=================

Ce guide explique en détail les concepts et l'utilisation d'OpenRainflow.

Algorithme Rainflow
-------------------

Principe
~~~~~~~~

L'algorithme rainflow est une méthode de comptage de cycles utilisée pour analyser 
les historiques de contraintes à amplitude variable. Il simule l'écoulement de gouttes 
d'eau le long d'un graphique contrainte-temps tourné de 90°.

Implémentation
~~~~~~~~~~~~~~

OpenRainflow implémente l'algorithme selon la norme **ASTM E1049-85** avec optimisations :

1. **Détection des reversals** : Identification des pics et vallées
2. **Méthode des trois points** : Extraction des cycles par analyse successive
3. **Optimisation Numba** : Compilation JIT pour performance maximale

.. code-block:: python

   from openrainflow import rainflow_count

   cycles = rainflow_count(
       signal,
       remove_zeros=True,  # Retirer les cycles de plage nulle
       gate=None           # Seuil minimal optionnel
   )

Paramètres avancés
~~~~~~~~~~~~~~~~~~

**Gate (seuil)** : Ignorer les petits cycles

.. code-block:: python

   # Ignorer les cycles < 10 MPa
   cycles = rainflow_count(signal, gate=10.0)

**Gestion des zéros** :

.. code-block:: python

   # Conserver tous les cycles
   cycles = rainflow_count(signal, remove_zeros=False)

Binning des cycles
~~~~~~~~~~~~~~~~~~

Pour créer des histogrammes :

.. code-block:: python

   from openrainflow.rainflow import bin_cycles

   # Histogramme 1D (par plage)
   bin_centers, counts, _ = bin_cycles(cycles, range_bins=50)

   # Histogramme 2D (plage × moyenne)
   range_centers, mean_centers, counts_2d = bin_cycles(
       cycles, 
       range_bins=30, 
       mean_bins=20
   )

Courbes d'endurance
-------------------

Équation S-N
~~~~~~~~~~~~

Les courbes S-N suivent :

.. math::

   N = \frac{C}{\Delta\sigma^m}

avec deux pentes :

* **Région 1** (:math:`N < N_{knee}`) : pente :math:`m_1 = 3`
* **Région 2** (:math:`N_{knee} < N < N_{cutoff}`) : pente :math:`m_2 = 5`
* **Région 3** (:math:`N > N_{cutoff}`) : vie infinie (< CAFL)

.. code-block:: python

   from openrainflow.eurocode import EurocodeCategory

   curve = EurocodeCategory.get_curve('71')

   # Calculer N pour une contrainte donnée
   N = curve.get_cycles_to_failure(delta_sigma=100.0)

   # Calculer la contrainte pour N cycles
   delta_sigma = curve.get_stress_range(N=1e6)

Paramètres des courbes
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   curve = EurocodeCategory.get_curve('71')

   print(f"Δσ_c (2M cycles) : {curve.delta_sigma_c} MPa")
   print(f"Pentes : m1={curve.m1}, m2={curve.m2}")
   print(f"Point de transition : {curve.N_knee:.2e} cycles")
   print(f"Limite d'endurance : {curve.delta_sigma_L:.2f} MPa")
   print(f"Limite de coupure : {curve.N_cutoff:.2e} cycles")

Courbes personnalisées
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.eurocode import create_custom_curve

   # Matériau aluminium
   al_curve = create_custom_curve(
       name='AL-6061-T6',
       delta_sigma_c=70.0,
       m1=4.0,              # Pente plus forte
       m2=6.0,
       N_ref=2e6,
       N_cutoff=5e8
   )

   # Courbe avec limite explicite
   custom = create_custom_curve(
       name='Custom',
       delta_sigma_c=90.0,
       delta_sigma_L=30.0   # CAFL personnalisée
   )

Visualisation des courbes
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.eurocode import plot_sn_curve
   import matplotlib.pyplot as plt

   curves = [
       EurocodeCategory.get_curve('36'),
       EurocodeCategory.get_curve('71'),
       EurocodeCategory.get_curve('112'),
   ]

   plot_sn_curve(curves, show_knee=True, show_cafl=True)
   plt.show()

Calcul de dommage
-----------------

Règle de Miner
~~~~~~~~~~~~~~

Le dommage cumulatif selon Palmgren-Miner :

.. math::

   D = \sum_{i=1}^{k} \frac{n_i}{N_i}

Critère de rupture : :math:`D \geq 1.0`

.. code-block:: python

   from openrainflow import calculate_damage

   damage = calculate_damage(cycles, fatigue_curve)

   if damage >= 1.0:
       print("⚠ Rupture attendue!")
   else:
       print(f"✓ OK - Dommage = {damage:.2%}")

Durée de vie
~~~~~~~~~~~~

.. code-block:: python

   from openrainflow import calculate_life

   life = calculate_life(cycles, fatigue_curve)

   print(f"Vie estimée : {life:.2e} répétitions")

Relation : :math:`\text{Vie} = \frac{1}{\text{Dommage par cycle}}`

Facteur de sécurité partiel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Eurocode recommande :math:`\gamma_{Mf} = 1.15` à :math:`1.35` :

.. code-block:: python

   damage = calculate_damage(
       cycles, 
       fatigue_curve,
       partial_safety_factor=1.25  # γ_Mf
   )

Effet : multiplie les contraintes par :math:`\gamma_{Mf}`, augmentant le dommage.

Contrainte équivalente
~~~~~~~~~~~~~~~~~~~~~~

Contrainte constante qui causerait le même dommage :

.. code-block:: python

   from openrainflow.damage import calculate_equivalent_stress

   delta_sigma_eq = calculate_equivalent_stress(
       cycles, 
       fatigue_curve,
       N_eq=2e6  # Nombre de cycles de référence
   )

   print(f"Contrainte équivalente (2M) : {delta_sigma_eq:.2f} MPa")

Évaluation de sécurité
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.damage import assess_fatigue_safety

   util, status, details = assess_fatigue_safety(
       cycles,
       fatigue_curve,
       design_life=1000,
       partial_safety_factor=1.25
   )

   print(f"Statut : {status}")  # PASS, WARNING, ou FAIL
   print(f"Utilisation : {util:.2%}")
   print(f"Facteur de réserve : {details['reserve_factor']:.2f}")

Statuts :

* **PASS** : utilisation < 80%
* **WARNING** : 80% ≤ utilisation < 100%
* **FAIL** : utilisation ≥ 100%

Analyse de contribution
~~~~~~~~~~~~~~~~~~~~~~~~

Identifier les plages de contrainte les plus dommageables :

.. code-block:: python

   from openrainflow.damage import damage_contribution_analysis

   bins, counts, damage_fractions = damage_contribution_analysis(
       cycles, 
       fatigue_curve,
       n_bins=20
   )

   # Trouver le bin le plus dommageable
   max_idx = np.argmax(damage_fractions)
   print(f"Plage la plus dommageable : {bins[max_idx]:.1f} MPa")
   print(f"Contribution : {damage_fractions[max_idx]*100:.1f}%")

   # Visualiser
   import matplotlib.pyplot as plt
   plt.bar(bins, damage_fractions*100)
   plt.xlabel('Plage de contrainte [MPa]')
   plt.ylabel('Contribution au dommage [%]')
   plt.show()

Traitement parallèle
--------------------

Multiples signaux
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow import rainflow_count_parallel

   # Liste de signaux
   signals = [signal1, signal2, signal3, ...]

   # Comptage parallèle
   cycles_list = rainflow_count_parallel(
       signals,
       n_jobs=4,      # Nombre de processus (-1 = tous les CPUs)
       remove_zeros=True,
       gate=None
   )

   # cycles_list[i] contient les cycles de signals[i]

Analyseur parallèle
~~~~~~~~~~~~~~~~~~~

Classe de haut niveau pour analyse complète :

.. code-block:: python

   from openrainflow.parallel import ParallelFatigueAnalyzer

   analyzer = ParallelFatigueAnalyzer(n_jobs=4, verbose=1)

   # Ajouter les signaux
   analyzer.add_signals(signals)

   # Définir la courbe
   analyzer.set_fatigue_curve('71')  # ou un objet FatigueCurve

   # Analyser
   results = analyzer.analyze(design_life=1000)

   print(results['damages'])       # Dommages
   print(results['lives'])         # Vies
   print(results['utilizations'])  # Utilisations
   print(results['max_damage'])    # Dommage maximum
   print(results['min_life'])      # Vie minimum

Calcul de dommage par lot
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.parallel import batch_damage_calculation

   damages = batch_damage_calculation(
       cycles_list,
       fatigue_curve,  # ou liste de courbes
       n_jobs=4,
       partial_safety_factor=1.25
   )

Très grands signaux
~~~~~~~~~~~~~~~~~~~

Pour signaux > 10M points, traitement par batch :

.. code-block:: python

   from openrainflow.parallel import parallel_rainflow_batch

   # Signal très long
   big_signal = np.random.randn(50_000_000)

   # Traitement par batch avec chevauchement
   cycles = parallel_rainflow_batch(
       big_signal,
       batch_size=1_000_000,  # Taille des lots
       n_jobs=8,
       overlap=1000           # Chevauchement entre lots
   )

**Note** : Approximation due aux frontières de batch.

Utilitaires
-----------

Statistiques de signal
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.utils import calculate_statistics

   stats = calculate_statistics(signal)

   print(stats['mean'])
   print(stats['std'])
   print(stats['min'])
   print(stats['max'])
   print(stats['rms'])
   print(stats['median'])
   print(stats['q25'])   # 1er quartile
   print(stats['q75'])   # 3e quartile

Filtrage de signal
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.utils import filter_signal

   # Filtre passe-bas Butterworth
   filtered = filter_signal(
       signal,
       cutoff_freq=10.0,      # Hz
       sampling_freq=100.0,   # Hz
       filter_type='lowpass',
       order=4
   )

Génération de signaux de test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.utils import (
       generate_random_signal,
       generate_sine_signal
   )

   # Signal aléatoire Gaussien
   random_sig = generate_random_signal(
       n_points=10000,
       mean=100.0,
       std=25.0,
       seed=42
   )

   # Signal sinusoïdal
   sine_sig = generate_sine_signal(
       n_points=1000,
       amplitude=50.0,
       frequency=1.0,
       sampling_freq=100.0,
       offset=100.0
   )

Import/Export
~~~~~~~~~~~~~

.. code-block:: python

   from openrainflow.utils import (
       load_signal_from_file,
       save_cycles_to_file
   )

   # Charger signal depuis fichier
   signal = load_signal_from_file(
       'data.txt',
       column=0,
       skip_rows=1,
       delimiter=','
   )

   # Sauvegarder cycles
   save_cycles_to_file(
       cycles,
       'cycles_output.csv',
       header=True
   )

Bonnes pratiques
----------------

1. **Validation des données**

   .. code-block:: python

      assert len(signal) > 10, "Signal trop court"
      assert np.all(np.isfinite(signal)), "Valeurs non finies"

2. **Choix de la courbe**

   Consultez EN 1993-1-9 pour sélectionner la catégorie appropriée selon
   le détail constructif.

3. **Facteur de sécurité**

   Eurocode recommande :math:`\gamma_{Mf}` :
   
   * 1.15 pour vérifications de fatigue
   * 1.25 à 1.35 selon conséquences de rupture

4. **Interprétation du dommage**

   * D < 0.5 : très sûr
   * 0.5 ≤ D < 0.8 : acceptable
   * 0.8 ≤ D < 1.0 : critique, vérifier
   * D ≥ 1.0 : rupture attendue

5. **Performance**

   * Première exécution : compilation Numba (~1s)
   * Exécutions suivantes : cache utilisé (rapide)
   * Signaux > 1M points : considérer traitement parallèle

