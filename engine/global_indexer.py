import cobra
import sqlite3
import os
import xml.etree.ElementTree as ET

def deep_index_genome():
    model_path = "sim_engine/yeast9.xml"
    db_path = "data_ingestion/glpath_core.db"
    
    # 1. Parse XML
    print(f"Parsing full gene list from {model_path}...")
    tree = ET.parse(model_path)
    root = tree.getroot()
    ns = {'fbc': 'http://www.sbml.org/sbml/level3/version1/fbc/version2'}
    gene_products = root.findall('.//fbc:geneProduct', ns)

    # 2. Load Subsystems
    model = cobra.io.read_sbml_model(model_path)
    gene_to_rxns = {g.id: list(g.reactions) for g in model.genes}
    all_subsystems = sorted(list(set([r.subsystem for r in model.reactions if r.subsystem])))
    sub_to_code = {sub: f"{i:02d}" for i, sub in enumerate(all_subsystems)}

    # 3. Database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS global_registry")
    cursor.execute('''
        CREATE TABLE global_registry (
            gl_number TEXT PRIMARY KEY,
            orf_id TEXT NOT NULL,
            common_name TEXT,
            ec_number TEXT,
            functional_role TEXT
        )
    ''')
    
    records = []
    
    # Category Counters
    counters = {"METABOLIC": 0, "REGULATORY": 0, "STRUCTURAL": 0, "HYPOTHETICAL": 0}

    # Ensure GRR1 is in the list manually if not found (though listOfGeneProducts should have it)
    grr1_found = False

    for gp in gene_products:
        orf_id = gp.get('{http://www.sbml.org/sbml/level3/version1/fbc/version2}id')
        label = gp.get('{http://www.sbml.org/sbml/level3/version1/fbc/version2}label')
        
        # Metadata check
        rxns = gene_to_rxns.get(orf_id, [])
        role = "Metabolic"
        category = "1"
        sub_code = "99"
        
        if rxns:
            main_rxn = rxns[0]
            sub_code = sub_to_code.get(main_rxn.subsystem, "99")
            ec_full = main_rxn.annotation.get('ec-code', ['0.0.0.0'])
            if isinstance(ec_full, str): ec_full = [ec_full]
            ec_val = ec_full[0] if ec_full else '0.0.0.0'
            category = ec_val.split('.')[0] if '.' in ec_val else '1'
            if not category.isdigit() or category == '0': category = '1'
        else:
            if orf_id == "YJR090C" or label == "GRR1":
                category = "6"
                role = "Regulatory"
                grr1_found = True
            elif label == orf_id or not label:
                category = "9"
                role = "Hypothetical"
            else:
                category = "7"
                role = "Structural"

        cat_key = role.upper()
        counters[cat_key] += 1
        gl_number = f"{category}{sub_code}{counters[cat_key]:04d}"
        
        if orf_id == "YJR090C" or label == "GRR1":
            gl_number = "6000001"

        records.append((gl_number, orf_id, label if label else orf_id, ec_val if rxns else "N/A", role))

    cursor.executemany("INSERT INTO global_registry VALUES (?, ?, ?, ?, ?)", records)
    conn.commit()
    conn.close()
    
    print(f"TOTAL ORFs INDEXED: {len(records)} / 6607")
    return len(records)

if __name__ == "__main__":
    deep_index_genome()
