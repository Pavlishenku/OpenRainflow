Changelog
=========

Version 1.0.0 (2025-01-XX)
--------------------------

Première version stable d'OpenRainflow.

Fonctionnalités
~~~~~~~~~~~~~~~

* **Algorithme rainflow** optimisé avec Numba JIT
  
  - Implémentation selon ASTM E1049-85
  - Support des signaux de toute taille
  - Gating optionnel pour filtrage des petits cycles
  
* **Courbes d'endurance Eurocode** (EN 1993-1-9:2005)
  
  - 14 catégories standard (36 à 160 MPa)
  - Support des pentes doubles (m1=3, m2=5)
  - Limite d'endurance constante (CAFL)
  - Création de courbes personnalisées
  
* **Calcul de dommage de Miner**
  
  - Règle de cumul linéaire
  - Support des facteurs de sécurité partiels
  - Calcul de durée de vie
  - Contrainte équivalente
  - Analyse de contribution au dommage
  
* **Traitement parallèle**
  
  - Comptage rainflow parallèle avec joblib
  - Classe ``ParallelFatigueAnalyzer`` pour analyse de batch
  - Traitement de très grands signaux par segments
  
* **Utilitaires**
  
  - Filtrage de signaux (Butterworth)
  - Génération de signaux de test
  - Import/export de données
  - Statistiques de signal

Performance
~~~~~~~~~~~

* Optimisation Numba pour fonctions critiques
* Vectorisation NumPy
* Gestion mémoire efficace
* Cache de compilation JIT

Documentation
~~~~~~~~~~~~~

* Documentation Sphinx complète
* Guide utilisateur détaillé
* Exemples d'utilisation
* Référence API complète
* Guide de démarrage rapide

Tests
~~~~~

* 50+ tests unitaires
* Couverture > 90%
* Tests d'intégration
* Tests de performance

Version 0.9.0 (2025-01-XX) - Beta
---------------------------------

* Version beta initiale
* Fonctionnalités de base implémentées
* Tests préliminaires

Notes de migration
------------------

Depuis la version 0.x
~~~~~~~~~~~~~~~~~~~~~

Aucune version antérieure publique. Première version stable.

Roadmap
-------

Version 1.1.0 (prévue)
~~~~~~~~~~~~~~~~~~~~~~

* Support de courbes S-N additionnelles (DNV, IIW, etc.)
* Export vers formats standards (Excel, HDF5)
* Interface graphique basique
* Amélioration des performances pour très grands datasets
* Support Python 3.13

Version 1.2.0 (prévue)
~~~~~~~~~~~~~~~~~~~~~~

* Correction de contrainte moyenne (Goodman, Gerber, Soderberg)
* Analyse multi-axiale
* Statistiques avancées de cycles
* Intégration avec pandas DataFrames

Version 2.0.0 (future)
~~~~~~~~~~~~~~~~~~~~~~

* Refonte complète de l'API
* Support GPU pour très grands calculs
* Interface web interactive
* Base de données de courbes de fatigue étendue

