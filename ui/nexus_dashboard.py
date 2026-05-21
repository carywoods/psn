import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import json
import os
import networkx as nx
import subprocess
import time
import numpy as np
import streamlit.components.v1 as components
from visualizer_module import generate_metabolic_graph, save_graph_html

# 1. Page Config (Standard Light Mode)
st.set_page_config(page_title="PSN Whole-Genome Dashboard", layout="wide", initial_sidebar_state="expanded")

def local_css():
    st.markdown("""
    <style>
    /* Force Light Mode Styles */
    .main { background-color: #f8f9fa; color: #212529; }
    .stApp { background-color: #f8f9fa; }
    .stSidebar { background-color: #ffffff; border-right: 1px solid #dee2e6; }
    h1, h2, h3 { color: #007bff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stSlider > div > div > div > div { background-color: #007bff; }
    .stTable { background-color: #ffffff; color: #212529; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# 2. Sidebar
st.sidebar.title("🧬 PSN NEXUS CORE")
st.sidebar.markdown("---")
top_base = st.sidebar.slider("Upper Threshold", 0.0, 2.0, 1.1)
bottom_base = st.sidebar.slider("Lower Threshold", 0.0, 2.0, 0.9)

# 3. Helpers
def get_db_data(query, params=()):
    db_path = 'data_ingestion/glpath_core.db'
    if not os.path.exists(db_path): return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_tables():
    db_path = 'data_ingestion/glpath_core.db'
    if not os.path.exists(db_path): return []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

# 4. Main UI
st.title("🚀 Saccharomyces-Nexus: Integrated Engine")

tabs = ["🗺️ Visual Map", "📂 Database Explorer", "🔍 Genome Search", "🔥 Metabolic Heatmap", "🛡️ Goebl Auditor"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs)

# --- TAB 1: VISUAL MAP ---
with tab1:
    st.subheader("Interactive Metabolic Network")
    net = generate_metabolic_graph()
    if net:
        html_path = save_graph_html(net)
        with open(html_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        components.html(source_code, height=650)
    else:
        st.error("Graph generation failed.")

# --- TAB 2: DATABASE EXPLORER ---
with tab2:
    st.subheader("🗄️ Database Table Registry")
    tables = get_tables()
    if tables:
        selected_table = st.selectbox("Select Table to View:", sorted(tables))
        df_table = get_db_data(f"SELECT * FROM {selected_table}")
        st.write(f"Displaying **{len(df_table)}** records from `{selected_table}`")
        st.dataframe(df_table, use_container_width=True)
    else:
        st.warning("No tables found in database.")

# --- TAB 3: GENOME SEARCH ---
with tab3:
    st.subheader("🔍 Genome Search")
    search_id = st.text_input("Search ORF_ID or GLNumber:", value="YMR300C")
    if search_id:
        match = get_db_data("SELECT * FROM global_registry WHERE orf_id = ? OR gl_number = ?", (search_id.upper(), search_id))
        if not match.empty:
            st.dataframe(match, use_container_width=True)
        else:
            st.warning("No matches found.")

# --- TAB 4: HEATMAP ---
with tab4:
    st.subheader("System Performance Heatmap")
    heat_data = np.random.uniform(0.5, 1.5, size=(10, 5))
    fig_heat = px.imshow(heat_data, color_continuous_scale='Viridis')
    st.plotly_chart(fig_heat, use_container_width=True)

# --- TAB 5: AUDITOR ---
with tab5:
    st.subheader("The Goebl Auditor")
    # Using a blue-ish gauge for light mode
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", 
        value=12.5, 
        title={'text': "Proteolytic Tax %"},
        gauge={'bar': {'color': "#007bff"}}
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "black"})
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")
st.caption("LIGHT MODE ACTIVE | DATABASE EXPLORER ENABLED | NODE 110")
