import json
import os

def apply_goebl_tax(model, proteolytic_tax=1.0):
    """
    Goebl Regulatory Layer (The Goebl Tax):
    Applies a 15% flux penalty to enzymes targeted by the SCF-GRR1 complex.
    The penalty is scaled by the proteolytic_tax from the GRR1 sensor.
    """
    map_path = "data_ingestion/regulatory_map.json"
    if not os.path.exists(map_path):
        print("Warning: regulatory_map.json not found. Goebl Tax skipped.")
        return model

    with open(map_path, "r") as f:
        regulatory_map = json.load(f)

    # Collect all reactions associated with SCF-GRR1 interactors
    target_reactions = set()
    for symbol, data in regulatory_map.items():
        target_reactions.update(data["reactions"])

    # Apply 15% penalty to flux bounds
    penalty_factor = 0.85 / proteolytic_tax # Increase tax = decrease factor
    
    count = 0
    for rid in target_reactions:
        if rid in model.reactions:
            rxn = model.reactions.get_by_id(rid)
            rxn.lower_bound *= penalty_factor
            rxn.upper_bound *= penalty_factor
            count += 1
            
    print(f"Goebl Tax applied: 15% penalty to {count} reactions (Proteolytic Tax: {proteolytic_tax:.2f})")
    return model

def calculate_regulatory_burden(cell_state="NORMAL"):
    # Keeping old function for compatibility if needed, but the user requested the map-based approach
    burdens = {
        "NORMAL": 0.0,
        "G1_ARREST": 0.15,
        "STRESS": 0.25
    }
    return burdens.get(cell_state, 0.0)
