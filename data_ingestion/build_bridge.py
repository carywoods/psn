import json
import os
import cobra
from data_ingestion.sgd_fetcher import get_interaction_data

def build_bridge():
    # Systematic names for Goebl Lab targets
    targets = {
        "CDC34": "YDR054C",
        "CDC53": "YDL132W",
        "GRR1": "YJR090C"
    }

    print("Fetching interactions from SGD...")
    all_physical_interactors = []
    for name, locus_id in targets.items():
        print(f"Querying {name} ({locus_id})...")
        interactions = get_interaction_data(locus_id)
        if interactions:
            all_physical_interactors.extend(interactions["physical"])
    
    # Deduplicate interactors
    seen_systematic = set()
    unique_interactors = []
    for interactor in all_physical_interactors:
        if interactor["systematic"] not in seen_systematic:
            seen_systematic.add(interactor["systematic"])
            unique_interactors.append(interactor)
            
    print(f"Found {len(unique_interactors)} unique physical interactors.")

    # Load Yeast9 model to map genes to reactions
    print("Mapping genes to Yeast9 reactions...")
    model_path = "sim_engine/yeast9.xml"
    model = cobra.io.read_sbml_model(model_path)
    
    regulatory_map = {}
    for interactor in unique_interactors:
        systematic_id = interactor["systematic"]
        symbol = interactor["symbol"]
        
        if systematic_id in model.genes:
            gene_obj = model.genes.get_by_id(systematic_id)
            reactions = [r.id for r in gene_obj.reactions]
            if reactions:
                regulatory_map[symbol] = {
                    "systematic_id": systematic_id,
                    "reactions": reactions
                }

    print(f"Mapped {len(regulatory_map)} genes to metabolic reactions.")
    
    with open("data_ingestion/regulatory_map.json", "w") as f:
        json.dump(regulatory_map, f, indent=4)
    print("Saved regulatory_map.json")

if __name__ == "__main__":
    build_bridge()
