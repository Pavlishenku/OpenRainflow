OpenRainflow Documentation
==========================

**OpenRainflow** est un package Python haute performance pour l'analyse de fatigue avec la méthode rainflow, 
les courbes d'endurance de l'Eurocode, et le calcul de dommage selon la règle de cumul linéaire de Miner.

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.8+

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

Caractéristiques principales
-----------------------------

✨ **Implémentation optimisée** de l'algorithme rainflow avec Numba JIT compilation

🚀 **Haute performance** : traitement rapide avec gestion mémoire optimale

🔄 **Parallélisation** : support multi-threading pour grandes données

📊 **Courbes Eurocode** : implémentation complète des courbes d'endurance EN 1993-1-9

🔬 **Calcul de dommage** : règle de Miner pour évaluation de durée de vie

🧪 **Testé** : couverture complète avec tests unitaires

Installation rapide
-------------------

.. code-block:: bash

   pip install -e .

Pour le support de parallélisation :

.. code-block:: bash

   pip install -e ".[parallel]"

Exemple d'utilisation
---------------------

.. code-block:: python

   import numpy as np
   from openrainflow import rainflow_count, calculate_damage
   from openrainflow.eurocode import EurocodeCategory

   # Données de contrainte temporelle
   stress_history = np.random.randn(10000) * 100 + 200

   # Comptage rainflow
   cycles = rainflow_count(stress_history)

   # Définir la courbe d'endurance (catégorie 36 de l'Eurocode)
   fatigue_curve = EurocodeCategory.get_curve('36')

   # Calculer le dommage cumulé
   damage = calculate_damage(cycles, fatigue_curve)

   print(f"Dommage cumulé : {damage:.6f}")
   print(f"Durée de vie estimée : {1/damage:.2f} répétitions")

Table des matières
------------------

.. toctree::
   :maxdepth: 2
   :caption: Guide utilisateur

   installation
   quickstart
   user_guide
   examples

.. toctree::
   :maxdepth: 2
   :caption: Référence API

   api/rainflow
   api/eurocode
   api/damage
   api/parallel
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Développement

   contributing
   changelog

Indices et tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

