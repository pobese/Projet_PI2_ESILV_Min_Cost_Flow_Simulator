# backend/core/scenarios.py
import pandas as pd
from core.config import PMIN_FACTORS

def apply_scenarios(plants: pd.DataFrame, cities: pd.DataFrame, req) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Applique les modifications de l'utilisateur et les règles climatiques/économiques
    sur les DataFrames des centrales et des villes.
    """
    # 1. Application des modifications manuelles de l'éditeur HTML
    for node_id, new_val in req.custom_nodes.items():
        if node_id in plants['id'].values: 
            plants.loc[plants['id'] == node_id, 'capacity_mw'] = new_val
        elif node_id in cities['id'].values: 
            cities.loc[cities['id'] == node_id, 'demand'] = new_val

    # 2. Application des scénarios climatiques et économiques
    if req.scenario == "Grand Froid": 
        cities['demand'] *= 2
        
    elif req.scenario == "Canicule":
        plants.loc[plants['type'] == 'Nucléaire', 'capacity_mw'] *= 0.7
        plants.loc[plants['type'] == 'Hydraulique', 'capacity_mw'] *= 0.8
        cities['demand'] *= 1.1
        
    elif req.scenario == "Blackout":
        plants.loc[plants['type'] == 'Nucléaire', 'capacity_mw'] = 0
        plants.loc[plants['type'] == 'Hydraulique', 'capacity_mw'] *= 0.5
        cities['demand'] *= 2.5
        
    elif req.scenario == "Réaliste (Marge 20%)":
        # Stratégie de Dispatch (Merit Order + Minimum Technique)
        total_demand = cities['demand'].sum()
        target_cap = total_demand * 1.20 
        
        plants = plants.sort_values(by='cost', ascending=True)
        accumulated_cap = 0
        
        for idx, row in plants.iterrows():
            ptype = "Nucléaire" if "Nucléaire" in row['type'] else "Hydraulique" if "Hydraulique" in row['type'] else "Thermique" if "Thermique" in row['type'] else "Autre"
            p_min = row['capacity_mw'] * PMIN_FACTORS.get(ptype, 0.05)
            
            if accumulated_cap >= target_cap:
                plants.loc[idx, 'capacity_mw'] = 0 # Extinction
            else:
                needed = target_cap - accumulated_cap
                if needed < p_min:
                    plants.loc[idx, 'capacity_mw'] = int(p_min) # Contrainte de seuil
                    accumulated_cap += p_min
                else:
                    take = min(row['capacity_mw'], needed)
                    plants.loc[idx, 'capacity_mw'] = int(take)
                    accumulated_cap += take

    # 3. Coupe-circuit (Boutons du frontend)
    if not req.active_nuclear: plants.loc[plants['type'].str.contains('Nucléaire', case=False), 'capacity_mw'] = 0
    if not req.active_thermal: plants.loc[plants['type'].str.contains('Thermique', case=False), 'capacity_mw'] = 0
    if not req.active_hydro: plants.loc[plants['type'].str.contains('Hydraulique', case=False), 'capacity_mw'] = 0

    return plants, cities