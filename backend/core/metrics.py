# backend/core/metrics.py
import pandas as pd

def calculate_metrics(plants, cities, raw_nodes_list, flowDict, physical_links, real_cost):
    """
    Calcule les KPIs (Mix, Rendements) et formate les données pour le frontend.
    """
    # 1. CALCUL DU MIX ÉNERGÉTIQUE
    mix = {}
    for _, plant in plants.iterrows():
        if plant['capacity_mw'] > 0:
            ptype = plant['type']
            mix[ptype] = mix.get(ptype, 0) + int(plant['capacity_mw'])

    import_vol = sum(flowDict.get("D_SLACK", {}).values())
    if import_vol > 0:
        mix["IMPORT (Secours)"] = int(import_vol)

    # 2. FORMATAGE DES LIGNES ET COÛT IDÉAL
    links_result = []
    ideal_cost_sum = 0
    
    for link in physical_links.values():
        if link["flow"] > 0:
            link["charge_pct"] = (link["flow"] / link["capacity"]) * 100 if link["capacity"] > 0 else 0
            link["unit_cost_avg"] = link["total_cost"] / link["flow"]
            links_result.append(link)
            
            # Calcul pour le rendement d'optimisation (Coût si tout était fluide)
            base_price = link["unit_cost_avg"]
            if link["charge_pct"] > 80: 
                base_price /= 3.0  # Retire la pénalité Tier 3
            elif link["charge_pct"] > 50: 
                base_price /= 1.5  # Retire la pénalité Tier 2
            ideal_cost_sum += link["flow"] * base_price

    # 3. CALCUL DES RENDEMENTS
    total_prod = int(plants['capacity_mw'].sum())
    total_dem = int(cities['demand'].sum())
    
    # Rendement Énergétique (Adéquation Offre/Demande)
    eff_energy = (total_dem / total_prod * 100) if total_prod > 0 else 0
    eff_energy = min(100, round(eff_energy, 1))

    # Rendement d'Optimisation (Fluidité)
    eff_optim = (ideal_cost_sum / real_cost * 100) if real_cost > 0 else 100
    eff_optim = min(100, round(eff_optim, 1))

    # 4. RECONSTRUCTION DES NOEUDS POUR LA CARTE LEAFLET
    updated_nodes_list = []
    plants_cap = plants.set_index('id')['capacity_mw'].to_dict()
    cities_dem = cities.set_index('id')['demand'].to_dict()

    for raw_node in raw_nodes_list:
        node = raw_node.copy()
        if node['id'] in plants_cap: 
            node['capacity_mw'] = int(plants_cap[node['id']])
        if node['id'] in cities_dem: 
            node['demand'] = int(cities_dem[node['id']])
            
        for k, v in node.items():
            if pd.isna(v): node[k] = None 
        updated_nodes_list.append(node)

    # 5. ASSEMBLAGE DE LA RÉPONSE
    kpis = {
        "cost": real_cost, 
        "production": total_prod, 
        "demand": total_dem,
        "efficiency_energy": eff_energy,
        "efficiency_optim": eff_optim
    }
    
    return kpis, mix, links_result, updated_nodes_list