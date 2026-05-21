import sqlite3
import os
import re

def genome_wide_expansion():
    db_path = "data_ingestion/glpath_core.db"
    sgd_path = "data_ingestion/SGD_features.tab"
    
    if not os.path.exists(sgd_path):
        print(f"Error: {sgd_path} not found.")
        return

    # 1. Load existing ORFs from database to avoid duplicates
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT orf_id FROM global_registry")
    existing_orfs = set([row[0] for row in cursor.fetchall()])
    print(f"Existing indexed ORFs: {len(existing_orfs)}")

    # 2. Parse SGD Features
    print("Parsing SGD features...")
    new_records = []
    
    # Category Counters (Start from high bases to avoid overlap with existing 1MM range)
    counters = {
        "MET_EXP": 2000000,
        "REG": 6000000,
        "OTHER": 9000000
    }

    # Keywords for classification
    met_keywords = ["enzyme", "reductase", "kinase", "transferase", "synthase", "dehydrogenase", "catalyzes", "hydrolase", "isomerase", "ligase", "lyase"]
    reg_keywords = ["transcription factor", "activator", "repressor", "signaling", "regulates", "regulatory", "inhibitor", "sensor"]
    
    ec_pattern = re.compile(r"\d+\.\d+\.\d+\.\d+")

    with open(sgd_path, "r") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) < 16: continue
            
            f_type = parts[1].strip()
            if f_type != "ORF": continue
            
            orf_id = parts[3].strip()
            if orf_id in existing_orfs: continue
            
            common_name = parts[4].strip()
            if not common_name: common_name = orf_id
            
            desc = parts[15].strip()
            
            # Classification Logic
            role = "Structural/Hypothetical"
            category = "OTHER"
            ec_found = ec_pattern.search(desc)
            ec_val = ec_found.group(0) if ec_found else "N/A"
            
            if any(k in desc.lower() for k in met_keywords) or ec_val != "N/A":
                role = "Metabolic Expansion"
                category = "MET_EXP"
            elif any(k in desc.lower() for k in reg_keywords):
                role = "Regulatory"
                category = "REG"
            
            counters[category] += 1
            gl_number = str(counters[category])
            
            new_records.append((
                gl_number,
                orf_id,
                common_name,
                ec_val,
                role
            ))

    # 3. UPSERT into database
    print(f"Discovered {len(new_records)} new ORFs.")
    cursor.executemany("INSERT OR REPLACE INTO global_registry VALUES (?, ?, ?, ?, ?)", new_records)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM global_registry")
    total_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"TOTAL SYSTEM ADDRESSES: {total_count} / 6607")
    return total_count

if __name__ == "__main__":
    genome_wide_expansion()
