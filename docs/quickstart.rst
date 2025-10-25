Guide de démarrage rapide
==========================

Ce guide vous permettra de commencer à utiliser OpenRainflow en quelques minutes.

Exemple minimal (30 secondes)
------------------------------

.. code-block:: python

   import numpy as np
   from openrainflow import rainflow_count, calculate_damage
   from openrainflow.eurocode import EurocodeCategory

   # 1. Votre historique de contraintes
   stress_history = np.random.randn(10000) * 50 + 100

   # 2. Comptage rainflow
   cycles = rainflow_count(stress_history)

   # 3. Courbe de fatigue
   fatigue_curve = EurocodeCategory.get_curve('71')

   # 4. Calcul du dommage
   damage = calculate_damage(cycles, fatigue_curve)

   # 5. Résultats
   print(f"Dommage : {damage:.6e}")
   print(f"Vie : {1/damage:.2e} répétitions")

Les bases du comptage rainflow
-------------------------------

L'algorithme rainflow identifie les cycles de contrainte dans un historique variable :

.. code-block:: python

   from openrainflow import rainflow_count
   import numpy as np

   # Créer un signal de test
   signal = np.array([0, 10, 2, 8, 1, 9, 0])

   # Compter les cycles
   cycles = rainflow_count(signal)

   # Explorer les résultats
   print(f"Nombre de cycles : {len(cycles)}")
   print(f"Plage de contrainte : {cycles['range']}")
   print(f"Contrainte moyenne : {cycles['mean']}")
   print(f"Comptage (0.5 ou 1.0) : {cycles['count']}")

Résultat de ``cycles`` :

* ``range`` : Amplitude du cycle (pic à vallée)
* ``mean`` : Valeur moyenne du cycle
* ``count`` : 1.0 pour cycle complet, 0.5 pour demi-cycle

Sélection d'une courbe de fatigue
----------------------------------

OpenRainflow implémente les 14 catégories standard de l'Eurocode 3 :

.. code-block:: python

   from openrainflow.eurocode import EurocodeCategory

   # Catégorie 71 (joints soudés courants)
   curve = EurocodeCategory.get_curve('71')

   # Informations sur la courbe
   print(f"Nom : {curve.name}")
   print(f"Résistance caractéristique : {curve.delta_sigma_c} MPa")
   print(f"Limite d'endurance : {curve.delta_sigma_L} MPa")

   # Lister toutes les catégories disponibles
   categories = EurocodeCategory.list_categories()
   print(f"Catégories : {categories}")

Catégories Eurocode disponibles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

========  ===========  ===================================
Catégorie Δσ_c (MPa)  Application typique
========  ===========  ===================================
160       160          Matériau parent laminé
125       125          Matériau parent oxycoupé
112       112          Joints soudés haute qualité
100       100          Joints soudés bonne qualité
90        90           Attaches soudées
80        80           Soudures bout à bout transversales
71        71           Détails soudés courants
63        63           Attaches soudées
56        56           Joints en croix
50        50           Soudures porteuses
45        45           Joints soudés complexes
40        40           Concentration de contrainte sévère
36        36           Concentration très sévère
========  ===========  ===================================

Calcul du dommage de Miner
---------------------------

La règle de Miner calcule le dommage cumulé :

.. math::

   D = \sum_{i=1}^{k} \frac{n_i}{N_i}

où :

* :math:`n_i` : nombre de cycles à l'amplitude i
* :math:`N_i` : nombre de cycles à rupture pour l'amplitude i
* Rupture attendue quand :math:`D \approx 1.0`

.. code-block:: python

   from openrainflow import calculate_damage, calculate_life

   # Calculer le dommage
   damage = calculate_damage(cycles, fatigue_curve)

   # Calculer la durée de vie
   life = calculate_life(cycles, fatigue_curve)

   print(f"Dommage par répétition : {damage:.6e}")
   print(f"Durée de vie : {life:.2e} répétitions")

Avec facteur de sécurité
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Appliquer un facteur de sécurité partiel γ_Mf = 1.25
   damage = calculate_damage(
       cycles, 
       fatigue_curve, 
       partial_safety_factor=1.25
   )

Évaluation de sécurité
----------------------

Rapport complet d'évaluation :

.. code-block:: python

   from openrainflow.damage import print_damage_report

   print_damage_report(
       cycles,
       fatigue_curve,
       design_life=1000,  # Nombre de répétitions requis
       partial_safety_factor=1.25
   )

Résultat détaillé :

.. code-block:: text

   ======================================================================
   FATIGUE DAMAGE ASSESSMENT REPORT
   ======================================================================
   
   Fatigue Curve: 71
     Δσ_c at 2E6:  71.0 MPa
     Slopes:       m1=3, m2=5
     CAFL:         52.26 MPa
   
   Load History:
     Total cycles:       5024.5
     Max stress range:   248.32 MPa
     Equiv. stress (2M): 89.45 MPa
   
   Damage Analysis:
     Design life:        1.00e+03 repetitions
     Damage per cycle:   3.456789e-04
     Total damage:       0.345679
     Actual life:        2.89e+03 repetitions
   
   Safety Assessment:
     Utilization:        34.57%
     Reserve factor:     2.89
     Safety factor:      1.25
     Status:             PASS
   
   ✓ Fatigue assessment PASSED
   ======================================================================

Traitement parallèle
--------------------

Pour de multiples signaux :

.. code-block:: python

   from openrainflow.parallel import ParallelFatigueAnalyzer

   # Créer l'analyseur
   analyzer = ParallelFatigueAnalyzer(n_jobs=4)

   # Ajouter plusieurs signaux
   signals = [signal1, signal2, signal3, ...]
   analyzer.add_signals(signals)

   # Définir la courbe
   analyzer.set_fatigue_curve('71')

   # Analyser
   results = analyzer.analyze(design_life=1000)

   # Résultats
   print(f"Dommages : {results['damages']}")
   print(f"Vies : {results['lives']}")
   print(f"Utilisations : {results['utilizations']}")

Courbe personnalisée
--------------------

Créer votre propre courbe S-N :

.. code-block:: python

   from openrainflow.eurocode import create_custom_curve

   custom_curve = create_custom_curve(
       name='MonMatériau',
       delta_sigma_c=85.0,    # Résistance à 2M cycles [MPa]
       m1=3.5,                # Pente normale
       m2=5.5,                # Pente haute durée
       N_knee=5e6,            # Point de transition
       N_cutoff=1e8           # Limite de coupure
   )

   # Utiliser comme une courbe standard
   damage = calculate_damage(cycles, custom_curve)

Prochaines étapes
-----------------

* Consultez le :doc:`user_guide` pour des explications détaillées
* Explorez les :doc:`examples` pour des cas d'usage réels
* Lisez la :doc:`api/rainflow` pour la référence complète de l'API

