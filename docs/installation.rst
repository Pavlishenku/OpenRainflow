Installation
============

Prérequis
---------

OpenRainflow nécessite Python 3.8 ou supérieur et les dépendances suivantes :

* NumPy >= 1.20.0
* Numba >= 0.56.0
* SciPy >= 1.7.0

Installation standard
---------------------

Installation depuis le code source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/openrainflow/openrainflow.git
   cd openrainflow
   pip install -e .

Installation avec support parallèle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour activer le traitement parallèle :

.. code-block:: bash

   pip install -e ".[parallel]"

Cette commande installe en plus :

* joblib >= 1.2.0

Installation pour le développement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pour contribuer au projet :

.. code-block:: bash

   pip install -e ".[dev]"

Cela installe les outils de développement :

* pytest >= 7.0.0
* pytest-cov >= 4.0.0
* black >= 22.0.0
* flake8 >= 5.0.0
* mypy >= 0.990

Vérification de l'installation
-------------------------------

Pour vérifier que l'installation a réussi :

.. code-block:: python

   import openrainflow
   print(openrainflow.__version__)
   print("Installation réussie!")

Exécuter les tests :

.. code-block:: bash

   pytest

Configuration de l'environnement virtuel
-----------------------------------------

Nous recommandons l'utilisation d'un environnement virtuel :

.. code-block:: bash

   # Créer un environnement virtuel
   python -m venv venv

   # Activer (Linux/Mac)
   source venv/bin/activate

   # Activer (Windows)
   venv\Scripts\activate

   # Installer OpenRainflow
   pip install -e .

Dépendances optionnelles
-------------------------

Pour la visualisation
~~~~~~~~~~~~~~~~~~~~~

Si vous souhaitez utiliser les fonctions de visualisation :

.. code-block:: bash

   pip install matplotlib

Pour la documentation
~~~~~~~~~~~~~~~~~~~~~

Pour générer la documentation :

.. code-block:: bash

   pip install sphinx sphinx-rtd-theme

Ensuite :

.. code-block:: bash

   cd docs
   make html

Problèmes courants
------------------

Erreur Numba
~~~~~~~~~~~~

Si vous rencontrez des problèmes avec Numba :

.. code-block:: bash

   pip install --upgrade numba

Erreur NumPy
~~~~~~~~~~~~

Assurez-vous d'avoir une version compatible de NumPy :

.. code-block:: bash

   pip install --upgrade numpy>=1.20.0

Problèmes de compilation
~~~~~~~~~~~~~~~~~~~~~~~~~

Sur certains systèmes, vous pourriez avoir besoin d'outils de compilation :

**Linux/Mac:**

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install build-essential

   # Mac (installer Xcode Command Line Tools)
   xcode-select --install

**Windows:**

Installer Microsoft C++ Build Tools.

Désinstallation
---------------

.. code-block:: bash

   pip uninstall openrainflow

