# backend/core/solver.py
import networkx as nx
from core.config import TIER_2_SURCOST, TIER_3_SURCOST, SLACK_PENALTY

def build_and_solve_network(plants, cities, arcs_df, min_flow_pct, cut_line=None):
    """
    Construit le graphe orienté avec les coûts convexes (paliers),
    lance le solveur Simplexe et prépare les résultats des lignes.
    """
    arcs = arcs_df.copy()
    if min_flow_pct > 0:
        arcs['min_flow'] = (arcs['capacity'] * (min_flow_pct / 100)).astype(int)

    G = nx.DiGraph()
    imbalances = {}
    
    for _, r in plants.iterrows(): imbalances[str(r['id'])] = imbalances.get(str(r['id']), 0) + int(r['capacity_mw'])
    for _, r in cities.iterrows(): imbalances[str(r['id'])] = imbalances.get(str(r['id']), 0) - int(r['demand'])
    
    plant_costs = plants.set_index('id')['cost'].to_dict()

    # Création des arcs physiques et virtuels (Convexité des coûts)
    for _, r in arcs.iterrows():
        src, dst = str(r['source_id']), str(r['dest_id'])

        # --- CRASH TEST N-1 : On détruit la ligne ---
        if cut_line and src == cut_line[0] and dst == cut_line[1]:
            continue # L'algorithme saute cette ligne, elle n'existe plus physiquement !

        if src in imbalances and dst in imbalances:
            total_cap = int(r['capacity'])
            base_cost = int(float(r['cost']) * 100) + (int(plant_costs[src] * 10) if src in plant_costs else 0)
            min_flow = int(r.get('min_flow', 0))
            
            if min_flow > 0:
                min_flow = min(min_flow, total_cap)
                imbalances[src] -= min_flow
                imbalances[dst] += min_flow
                total_cap -= min_flow

            if total_cap > 0:
                cap_t1 = max(0, int(0.5 * int(r['capacity'])) - min_flow) # 0-50%
                cap_t2 = int(0.3 * int(r['capacity']))                    # 50-80%
                cap_t3 = total_cap - cap_t1 - cap_t2                      # 80-100%

                if cap_t1 > 0:
                    G.add_edge(src, dst, capacity=cap_t1, weight=base_cost, is_physical=True, base_cap=int(r['capacity']), forced_flow=min_flow, physical_u=src, physical_v=dst)
                
                if cap_t2 > 0:
                    v2 = f"V2_{src}_{dst}"
                    G.add_node(v2, dummy=True)
                    imbalances[v2] = 0
                    G.add_edge(src, v2, capacity=cap_t2, weight=int(base_cost * TIER_2_SURCOST), is_physical=True, base_cap=int(r['capacity']), forced_flow=0, physical_u=src, physical_v=dst)
                    G.add_edge(v2, dst, capacity=cap_t2, weight=0, is_physical=False)

                if cap_t3 > 0:
                    v3 = f"V3_{src}_{dst}"
                    G.add_node(v3, dummy=True)
                    imbalances[v3] = 0
                    G.add_edge(src, v3, capacity=cap_t3, weight=int(base_cost * TIER_3_SURCOST), is_physical=True, base_cap=int(r['capacity']), forced_flow=0, physical_u=src, physical_v=dst)
                    G.add_edge(v3, dst, capacity=cap_t3, weight=0, is_physical=False)
            elif min_flow > 0:
                G.add_edge(src, dst, capacity=0, weight=base_cost, is_physical=True, base_cap=int(r['capacity']), forced_flow=min_flow, physical_u=src, physical_v=dst)

    # Noeud Slack (Marché Européen de secours)
    tot_bal = sum(imbalances.values())
    G.add_node("D_SLACK")
    imbalances["D_SLACK"] = -tot_bal
    
    for n in list(G.nodes):
        if n != "D_SLACK" and not G.nodes[n].get('dummy'):
            G.add_edge("D_SLACK", n, capacity=10**15, weight=SLACK_PENALTY)
            G.add_edge(n, "D_SLACK", capacity=10**15, weight=SLACK_PENALTY)

    if tot_bal > 0:
        for pid in plants['id']:
            if str(pid) in G.nodes: G[str(pid)]["D_SLACK"]['weight'] = 0

    for n, bal in imbalances.items(): G.nodes[n]['demand'] = -bal

    # RÉSOLUTION
    _, flowDict = nx.network_simplex(G)
    
    # Agrégation des résultats
    physical_links = {}
    real_cost = 0
    
    for u, v, data in G.edges(data=True):
        if "D_SLACK" in u or "D_SLACK" in v: continue
        if not data.get('is_physical', False): continue 
        
        opt_flow = flowDict.get(u, {}).get(v, 0)
        forced = data.get('forced_flow', 0)
        total_flow = opt_flow + forced
        
        if total_flow > 0 or forced > 0:
            link_cost = total_flow * (data['weight'] / 100.0)
            real_cost += link_cost
            
            p_u, p_v = data['physical_u'], data['physical_v']
            key = (p_u, p_v)
            if key not in physical_links:
                physical_links[key] = {"source": p_u, "target": p_v, "flow": 0, "capacity": data['base_cap'], "total_cost": 0}
            
            physical_links[key]["flow"] += total_flow
            physical_links[key]["total_cost"] += link_cost

    return flowDict, physical_links, real_cost