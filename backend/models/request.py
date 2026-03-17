# backend/models/request.py
from pydantic import BaseModel
from typing import Dict, List, Optional

class SolveRequest(BaseModel):
    """
    Modèle de requête pour lancer une simulation.
    Contient le scénario, les contraintes de flux et l'état du parc.
    """
    scenario: str = "Normal"
    min_flow_pct: int = 0
    carbon_tax: float = 0.0  # NOUVEAU : Le prix de la tonne de CO2 sur le marché financier
    demand_factor: float = 1.0  # NOUVEAU
    line_factor: float = 1.0    # NOUVEAU
    custom_nodes: Dict[str, int] = {}  # Pour les modifs manuelles de l'éditeur
    
    # État des interrupteurs par filière
    active_nuclear: bool = True
    active_thermal: bool = True
    active_hydro: bool = True

    # NOUVEAU : La ligne à sectionner pour le test N-1 [source, destination]
    cut_line: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "scenario": "Réaliste (Marge 20%)",
                "min_flow_pct": 0,
                "active_nuclear": True,
                "active_thermal": False,
                "active_hydro": True
            }
        }
