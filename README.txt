
GAÏA NEXUS – IA SÉCHERESSE V2
=============================

Ce projet permet de prédire les niveaux de sécheresse à l’échelle régionale grâce à une IA LSTM, une interface Streamlit, une carte satellite interactive et un export PDF prêt pour présentation à des collectivités.

------------------------------------
LANCER LE DASHBOARD (après setup) :
------------------------------------

1. Ouvrir un terminal dans le dossier du projet
2. Installer les dépendances :
   pip install -r requirements.txt

3. Lancer l'interface :
   streamlit run scripts/dashboard_secheresse.py

------------------------------------
STRUCTURE DES DOSSIERS :
------------------------------------

data/      → Données .csv et .npy
models/    → Modèle LSTM entraîné (.h5)
scripts/   → Tous les scripts Python
assets/    → Logo, visuels
exports/   → Fichiers générés (PDF, CSV)
config/    → Clé Mapbox, options éventuelles

------------------------------------
INFOS SUPPLÉMENTAIRES :
------------------------------------
- Région ciblée : PACA (centrée sur le Var)
- IA : LSTM multiclasses (aucune / modérée / sévère)
- Export PDF auto avec carte + résumé

Auteur : Projet Gaïa Nexus
