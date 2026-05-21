import networkx as nx
from pyvis.network import Network
import sqlite3
import json
import os

def generate_metabolic_graph(db_path='data_ingestion/glpath_core.db', ratio_path='data_ingestion/test_array_data1.json'):
    # 1. Build NetworkX graph
    G = nx.DiGraph()
    
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query purine pathway structure
    cursor.execute("""
        SELECT s.gl_number, s.pre_process, s.post_process, e.enzyme_rec 
        FROM glpath_structure s
        JOIN glpath_enzymes e ON s.gl_number = e.gl_number
    """)
    rows = cursor.fetchall()
    
    # Load ratios
    ratios = {}
    if os.path.exists(ratio_path):
        with open(ratio_path, 'r') as f:
            ratios = json.load(f)
            
    # 2. Add nodes and edges
    for gl_num, pre, post, enzyme in rows:
        # Determine color
        ratio = float(ratios.get(gl_num, {}).get('ratio_mean', 1.0))
        color = "#00ccff" # Baseline
        if ratio < 0.9: color = "#ff3131" # Red
        elif ratio > 1.1: color = "#39ff14" # Green
        
        G.add_node(gl_num, label=f"{enzyme}\n({gl_num})", title=f"Ratio: {ratio:.2f}", color=color)
        
        if post != '-1':
            G.add_edge(gl_num, post)
            
    conn.close()
    
    # 3. Translate to Pyvis
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black", directed=True)
    net.from_nx(G)
    
    # Custom physics/layout
    net.toggle_physics(True)
    
    return net

def save_graph_html(net, filename="ui/metabolic_graph.html"):
    if net:
        net.save_graph(filename)
        return filename
    return None
