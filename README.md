# Projet 10

## Développer un système de recommandation d'articles

### Objectif
🎯 **Développer un système de recommandation de contenu pour My Content, une start-up qui souhaite encourager la lecture en recommandant des articles et des livres pertinents à ses utilisateurs.

- 🔹 Déployer un modèle de recommandation sous forme d'Azure Functions pour une application MVP qui sélectionne cinq articles pour chaque utilisateur.

- 🖥️ Créer une interface simple qui permet de gérer le système de recommandation en affichant une liste d'ID utilisateurs et en affichant les résultats des recommandations.

### Structure du Projet
Ce projet est structuré comme suit :

📁 'function_app'
📁 'data_blob_storage' : Contient les fichiers de données utilisés par l'application, stockés dans un Azure Blob Storage.
📁 function : Contient le code source de l'Azure Function.
- __init__.py : Fichier principal de la fonction qui gère les requêtes et réponses.
- function.json : Fichier de configuration de la Function App.
- hybrid_recommender.py : Le système de recommandation hybride.
- host.json : Fichier de configuration de l'hôte pour les réglages de l'Azure Function.
- requirements.txt : Liste des dépendances nécessaires à l'exécution des scripts Python.
📄 'streamlit_app.py' : Application Streamlit permettant d'interagir avec le système de recommandation en local.
📄 'scripts.html' : Notebook de modélisation du système de recommandations