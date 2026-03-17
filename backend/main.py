# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

# Importation de nos propres modules
from models.request import SolveRequest
from core.scenarios import apply_scenarios
from core.solver import build_and_solve_network
from core.metrics import calculate_metrics


app = FastAPI(title="Smart Grid API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chargement initial des données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    raw_nodes = pd.read_csv(os.path.join(BASE_DIR, "data", "nodes_master.csv"), sep=";")
    raw_arcs = pd.read_csv(os.path.join(BASE_DIR, "data", "arcs.csv"), sep=";")
    RAW_NODES_LIST = raw_nodes.to_dict(orient="records")
except Exception as e:
    print(f"Erreur de chargement CSV : {e}")
    raw_nodes, raw_arcs, RAW_NODES_LIST = pd.DataFrame(), pd.DataFrame(), []


@app.get("/network-data")
def get_network_data():
    """Route pour charger la carte initiale sur le frontend."""
    return RAW_NODES_LIST


@app.post("/solve")
def solve_network(req: SolveRequest):
    """Route principale de résolution du réseau."""
    try:
        # 1. Initialisation des DataFrames
        plants = raw_nodes[raw_nodes['type'].str.contains('Centrale|Nucléaire|Thermique|Hydraulique', case=False)].copy()
        cities = raw_nodes[raw_nodes['type'].str.contains('Ville', case=False)].copy()
        
        # --- CALCUL DU COÛT DYNAMIQUE (MERIT ORDER + TAXE CARBONE) ---
        from core.config import PRODUCTION_COSTS, CO2_FACTORS
        
        # Modifications de l'éditeur HTML
        for node_id, new_val in req.custom_nodes.items():
            if node_id in plants['id'].values: plants.loc[plants['id'] == node_id, 'capacity_mw'] = new_val
            elif node_id in cities['id'].values: cities.loc[cities['id'] == node_id, 'demand'] = new_val

        req.custom_nodes = {}  # On vide pour éviter les conflits avec apply_scenarios

        # --- NOUVEAU : FACTEUR D'ÉCHELLE RÉALISTE (Variables via html) ---
        cities['demand'] = cities['demand'] * req.demand_factor
        scaled_arcs = raw_arcs.copy()
        scaled_arcs['capacity'] = scaled_arcs['capacity'] * req.line_factor # Virtuellement pour que les résultats saturent car pas la demande totale du pays
        # ----------------------------------------------------

        def calculate_market_price(row_type, carbon_price):
            # Identification de la filière
            ptype = "Nucléaire" if "Nucléaire" in row_type else "Hydraulique" if "Hydraulique" in row_type else "Thermique" if "Thermique" in row_type else "Autre"
            
            base_cost = PRODUCTION_COSTS.get(ptype, 50)
            emission_factor = CO2_FACTORS.get(ptype, 0.0)
            
            # Application de la taxe carbone
            return base_cost + (emission_factor * carbon_price)

        plants['cost'] = plants['type'].apply(lambda t: calculate_market_price(t, req.carbon_tax))

        # 2. Application du Scénario
        plants, cities = apply_scenarios(plants, cities, req)

        # 3. Résolution mathématique (Min Cost Flow)
        flowDict, physical_links, real_cost = build_and_solve_network(plants, cities, scaled_arcs, req.min_flow_pct, req.cut_line)

        # 4. Calcul des métriques et formatage
        kpis, mix, links_result, updated_nodes = calculate_metrics(
            plants, cities, RAW_NODES_LIST, flowDict, physical_links, real_cost
        )

        return {
            "status": "success",
            "kpi": kpis,
            "mix": mix,
            "nodes": updated_nodes,
            "links": links_result
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/solve-24h")
def solve_network_24h(req: SolveRequest):
    """Route pour simuler une journée complète (24 heures)"""
    try:
        from core.config import HOURLY_DEMAND_PROFILE, PRODUCTION_COSTS, CO2_FACTORS
        
        results_24h = []
        
        # NOUVEAU : On sauvegarde les données de l'interface web
        original_custom_nodes = req.custom_nodes.copy()
        
        for hour in range(24):
            plants = raw_nodes[raw_nodes['type'].str.contains('Centrale|Nucléaire|Thermique|Hydraulique', case=False)].copy()
            cities = raw_nodes[raw_nodes['type'].str.contains('Ville', case=False)].copy()
            
            # NOUVEAU : On applique les modifs de l'interface ICI, une seule fois
            for node_id, new_val in original_custom_nodes.items():
                if node_id in plants['id'].values: plants.loc[plants['id'] == node_id, 'capacity_mw'] = new_val
                elif node_id in cities['id'].values: cities.loc[cities['id'] == node_id, 'demand'] = new_val
            
            # On empêche apply_scenarios de ré-écraser nos données horaires
            req.custom_nodes = {} 
            
            def calculate_market_price(row_type, carbon_price):
                ptype = "Nucléaire" if "Nucléaire" in row_type else "Hydraulique" if "Hydraulique" in row_type else "Thermique" if "Thermique" in row_type else "Autre"
                return PRODUCTION_COSTS.get(ptype, 50) + (CO2_FACTORS.get(ptype, 0.0) * carbon_price)

            plants['cost'] = plants['type'].apply(lambda t: calculate_market_price(t, req.carbon_tax))

            
            # LA MAGIE OPÈRE ENFIN ICI SANS ÊTRE ÉCRASÉE
            multiplier = HOURLY_DEMAND_PROFILE[hour]
            cities['demand'] = (cities['demand'] * multiplier*req.demand_factor).astype(int)

            # On met aussi le réseau à l'échelle pour éviter la congestion totale
            scaled_arcs = raw_arcs.copy()
            scaled_arcs['capacity'] = scaled_arcs['capacity'] * req.line_factor
            
            plants, cities = apply_scenarios(plants, cities, req)

            flowDict, physical_links, real_cost = build_and_solve_network(
                plants, cities, scaled_arcs, req.min_flow_pct, req.cut_line
            )

            # 6. Calcul des métriques pour cette heure précise
            kpis, mix, links_result, updated_nodes = calculate_metrics(
                plants, cities, RAW_NODES_LIST, flowDict, physical_links, real_cost
            )
            
            # On sauvegarde la "photo" du réseau pour cette heure
            results_24h.append({
                "hour": hour,
                "multiplier": multiplier,
                "kpi": kpis,
                "mix": mix,
                "nodes": updated_nodes,
                "links": links_result
            })

        return {
            "status": "success", 
            "data_24h": results_24h
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}