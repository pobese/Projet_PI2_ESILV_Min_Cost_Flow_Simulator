# ⚡ Smart Grid Simulator : Optimisation & Marchés de l'Énergie

![Smart Grid Dashboard](https://img.shields.io/badge/Status-Completed-success)
![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Pandas-blue)
![Frontend](https://img.shields.io/badge/Frontend-Tailwind%20%7C%20JS%20%7C%20Leaflet-emerald)

## 📖 À propos du projet
Ce projet, développé dans le cadre de ma majeure **Énergie et Villes Durables**, est un simulateur interactif de réseau électrique (Smart Grid). Il modélise à la fois les contraintes physiques du transport d'électricité (lois des nœuds, congestion) et les mécanismes financiers des marchés de l'énergie (Merit Order, Taxe Carbone). 

L'objectif est d'optimiser le couplage offre/demande en temps réel et sur 24h, tout en assurant la résilience du réseau face aux aléas climatiques et techniques.

## ✨ Fonctionnalités Principales

* **🔌 Economic Dispatch & Unit Commitment :** Algorithme de minimisation des coûts (Minimum Cost Flow) pour répartir la production selon le *Merit Order* et piloter les centrales sur un profil journalier (24h).
* **💶 Mécanismes Financiers :** Intégration d'une taxe carbone (marché ETS) impactant dynamiquement le coût marginal des centrales thermiques.
* **🛡️ Résilience (Crash Test N-1) :** Simulation de la perte de la ligne la plus critique du réseau pour observer le redéploiement des flux et l'activation des imports de secours.
* **📊 Dashboard SCADA Temps Réel :** Cartographie interactive (Leaflet) visualisant la saturation des lignes, et graphiques dynamiques (Chart.js) du mix énergétique.
* **🌍 Scénarios Climatiques :** Simulation de situations de stress (Grand Froid, Canicule, Blackout) pour tester la robustesse des villes durables face aux pics de demande.

## 🛠️ Stack Technique

* **Backend :** Python, FastAPI, Pandas, Algorithmique des graphes.
* **Frontend :** HTML5, Vanilla JavaScript, Tailwind CSS (avec mode sombre industriel).
* **Data Visualisation :** Leaflet.js (Cartographie), Chart.js (Séries temporelles et KPIs).

## 🚀 Installation et Lancement

1. **Cloner le dépôt :**
   ```bash
   git clone [https://github.com/ton-pseudo/smart-grid-simulator.git](https://github.com/ton-pseudo/smart-grid-simulator.git)
   cd smart-grid-simulator