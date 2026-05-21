import sqlite3
import cobra
import os
import json

def update_gl_nexus_bridge():
    db_path = "data_ingestion/glpath_core.db"
    model_path = "sim_engine/yeast9.xml"
    gaps_path = "docs/MODEL_GAPS.md"
    
    if not os.path.exists(db_path) or not os.path.exists(model_path):
        print("Error: Database or model missing.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Loading model: {model_path}...")
    model = cobra.io.read_sbml_model(model_path)
    
    # 1. Map EC codes -> [Reaction IDs]
    ec_to_rxns = {}
    for rxn in model.reactions:
        ec_codes = rxn.annotation.get('ec-code', [])
        if isinstance(ec_codes, str): ec_codes = [ec_codes]
        for ec in ec_codes:
            if ec not in ec_to_rxns: ec_to_rxns[ec] = []
            ec_to_rxns[ec].append(rxn.id)
            
    # 2. Map Metabolite names -> [Metabolite IDs]
    name_to_mets = {}
    for met in model.metabolites:
        name = met.name.lower()
        if name not in name_to_mets: name_to_mets[name] = []
        name_to_mets[name].append(met.id)

    # 3. GL Synchronization and Verification
    cursor.execute("SELECT gl_number, ec_number FROM glpath_structure")
    gl_entries = cursor.fetchall()
    
    gaps = []
    sync_count = 0
    for gl_num, ec_num in gl_entries:
        model_rxns = ec_to_rxns.get(ec_num, [])
        if not model_rxns:
            gaps.append(f"- GL {gl_num} (EC {ec_num}): No reaction found in Yeast9 model.")
            continue
            
        # Fetch expected metabolites for this GL
        cursor.execute("""
            SELECT m.compound_name, l.role 
            FROM metabolites m 
            JOIN gl_metabolite_links l ON m.met_id = l.met_id 
            WHERE l.gl_number = ?
        """, (gl_num,))
        expected_mets = cursor.fetchall()
        
        # Verify each matched reaction
        for rid in model_rxns:
            rxn = model.reactions.get_by_id(rid)
            rxn_met_names = [m.name.lower() for m in rxn.metabolites]
            
            mismatches = []
            for name, role in expected_mets:
                if name.lower() not in rxn_met_names:
                    mismatches.append(name)
            
            if mismatches:
                gaps.append(f"- GL {gl_num} (RXN {rid}): Mismatch found. Missing: {', '.join(mismatches)}")
            else:
                print(f"NODE [{gl_num}] SYNCED TO [{rid}] (Metabolites Verified)")
                sync_count += 1
                
    # 4. Reporting
    with open(gaps_path, "w") as f:
        f.write("# Model Gaps (Yeast9 vs GLPath)\n\n")
        f.write("\n".join(gaps))
    print(f"Gaps logged to {gaps_path}")

    # Top 5 Connected Metabolites
    cursor.execute("""
        SELECT m.compound_name, COUNT(l.gl_number) as link_count
        FROM metabolites m
        JOIN gl_metabolite_links l ON m.met_id = l.met_id
        GROUP BY m.compound_name
        ORDER BY link_count DESC
        LIMIT 5
    """)
    top_mets = cursor.fetchall()
    print("\nTop 5 Most Connected Metabolites (Purine Pathway):")
    for name, count in top_mets:
        print(f"- {name}: {count} links")

    conn.close()
    return sync_count

if __name__ == "__main__":
    count = update_gl_nexus_bridge()
    print(f"\nSYSTEM UPDATED: GLPATH METABOLITE REGISTRY ACTIVE (Synced: {count})")
