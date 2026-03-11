# backend/core/config.py

# --- COÛTS DE PRODUCTION (€/MW) ---
# Basé sur le Merit Order standard
PRODUCTION_COSTS = {
    "Nucléaire": 5,
    "Hydraulique": 10,
    "Thermique": 80,
    "Autre": 50
}

# --- MINIMUM TECHNIQUE (Pmin) ---
# Puissance minimale en % de la capacité nominale pour maintenir la stabilité
PMIN_FACTORS = {
    "Nucléaire": 0.30,   # Un réacteur ne descend pas sous 30% facilement
    "Thermique": 0.40,   # Gaz/Charbon ont des inerties fortes
    "Hydraulique": 0.10, # Très flexible
    "Autre": 0.05
}

# --- ÉCONOMIE & CARBONE ---
CARBON_TAX = 80.0  # € / tonne de CO2
CO2_FACTORS = {
    "Nucléaire": 0.012,
    "Hydraulique": 0.024,
    "Thermique": 0.490,
    "Autre": 0.200
}

# --- PARAMÈTRES DU RÉSEAU ---
SLACK_PENALTY = 50000  # Coût de l'importation de secours (très punitif)
TIER_2_SURCOST = 1.5   # +50% au delà de 50% de charge
TIER_3_SURCOST = 3.0   # +200% au delà de 80% de charge

# --- PROFIL TEMPOREL (24 Heures) ---
# Multiplicateur de la demande de base heure par heure
HOURLY_DEMAND_PROFILE = [
    0.60, 0.55, 0.50, 0.50, 0.55, 0.65, # 00h-05h : La nuit (creux à 3h-4h)
    0.85, 1.10, 1.15, 1.05, 1.00, 0.95, # 06h-11h : Réveil et usines (pic à 8h)
    0.95, 0.90, 0.85, 0.85, 0.90, 1.00, # 12h-17h : Plateau de l'après-midi
    1.20, 1.35, 1.25, 1.10, 0.95, 0.75  # 18h-23h : Retour à la maison (Grand pic 19h)
]