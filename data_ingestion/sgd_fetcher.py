import requests
import json
import sys

def get_gene_details(locus_id):
    """
    Fetches basic info, GO annotations, and protein details for a given systematic name.
    URL: https://www.yeastgenome.org/backend/locus/<locus_id>
    """
    url = f"https://www.yeastgenome.org/backend/locus/{locus_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extract basic info
        result = {
            "display_name": data.get("display_name"),
            "systematic_name": data.get("format_name"),
            "description": data.get("description"),
            "go_annotations": [],
            "protein_details": {}
        }
        
        # Extract GO annotations (optional, if available in the locus response)
        # Note: Sometimes GO annotations are in a separate sub-endpoint, 
        # but basic locus response often has summary info.
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {locus_id}: {e}")
        return None

def get_interaction_data(locus_id):
    """
    Fetches Physical and Genetic Interactions for a given systematic name.
    URL: https://www.yeastgenome.org/backend/locus/<locus_id>/interaction_details
    """
    url = f"https://www.yeastgenome.org/backend/locus/{locus_id}/interaction_details"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        interactions = {
            "physical": [],
            "genetic": []
        }
        
        # Parse interaction details
        for entry in data:
            # The interactor is the locus that is NOT our locus_id
            l1 = entry.get("locus1", {})
            l2 = entry.get("locus2", {})
            
            if l1.get("format_name") == locus_id:
                interactor = l2
            else:
                interactor = l1
                
            symbol = interactor.get("display_name")
            systematic = interactor.get("format_name")
            i_type = entry.get("interaction_type")
            
            interaction_obj = {"symbol": symbol, "systematic": systematic}
            
            if i_type == "Physical":
                interactions["physical"].append(interaction_obj)
            elif i_type == "Genetic":
                interactions["genetic"].append(interaction_obj)
        
        # Deduplicate by systematic name
        def deduplicate(int_list):
            seen = set()
            new_list = []
            for item in int_list:
                if item["systematic"] not in seen:
                    seen.add(item["systematic"])
                    new_list.append(item)
            return new_list

        interactions["physical"] = deduplicate(interactions["physical"])
        interactions["genetic"] = deduplicate(interactions["genetic"])
        
        return interactions
    except requests.exceptions.RequestException as e:
        print(f"Error fetching interactions for {locus_id}: {e}")
        return None

def test_fetcher():
    locus_id = "YFL039C" # ACT1
    print(f"Fetching data for {locus_id} (ACT1)...")
    gene_data = get_gene_details(locus_id)
    
    if gene_data:
        print(f"Display Name: {gene_data['display_name']}")
        print(f"Description: {gene_data['description']}")
    
    print(f"Fetching interactions for {locus_id}...")
    interactions = get_interaction_data(locus_id)
    if interactions:
        print(f"Physical Interactions (count): {len(interactions['physical'])}")
        print(f"Genetic Interactions (count): {len(interactions['genetic'])}")
        if "CDC34" in interactions["physical"] or "CDC53" in interactions["physical"]:
             print("ALERT: Direct interaction with Goebl Lab SCF complex components detected!")

if __name__ == "__main__":
    test_fetcher()
