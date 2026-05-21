"""
PSN API Configuration
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PATH = PROJECT_ROOT / "sim_engine" / "yeast9.xml"
DATABASE_PATH = PROJECT_ROOT / "data_ingestion" / "glpath_core.db"
REGULATORY_MAP_PATH = PROJECT_ROOT / "data_ingestion" / "regulatory_map.json"
API_KEYS_DB_PATH = PROJECT_ROOT / "api" / "data" / "api_keys.db"
LOG_PATH = PROJECT_ROOT / "logs" / "api.log"

# CSV data paths
GL_SUBSTRATE_PRODUCT_PATH = PROJECT_ROOT / "data_ingestion" / "gl_substrate_product_full.csv"
MET_ID_LOOKUP_PATH = PROJECT_ROOT / "data_ingestion" / "met_id_lookup.csv"
GL_REACTION_LOOKUP_PATH = PROJECT_ROOT / "data_ingestion" / "gl_reaction_lookup.csv"

# API settings
API_VERSION = "1.0.0"
MODEL_VERSION = "Yeast-GEM v9.0.2"

# Rate limits by tier (calls per month)
RATE_LIMITS = {
    "free": 50,
    "pro": 1000,
    "enterprise": 10000
}

# Carbon source mappings to exchange reaction IDs
CARBON_SOURCE_REACTIONS = {
    "glucose": "r_1714",      # D-glucose exchange
    "xylose": "r_1718",       # D-xylose exchange
    "galactose": "r_1710",    # D-galactose exchange
    "ethanol": "r_1761",      # Ethanol exchange
    "glycerol": "r_1808"      # Glycerol exchange
}

# Default uptake rates for carbon sources
CARBON_SOURCE_UPTAKE_RATES = {
    "glucose": -10.0,
    "xylose": -10.0,
    "galactose": -10.0,
    "ethanol": -10.0,
    "glycerol": -10.0
}

# Oxygen constraint mappings
OXYGEN_CONSTRAINTS = {
    "aerobic": {"reaction": "r_1992", "lower": -1000.0, "upper": 1000.0},
    "anaerobic": {"reaction": "r_1992", "lower": 0.0, "upper": 0.0},
    "microaerobic": {"reaction": "r_1992", "lower": -2.0, "upper": 2.0}
}

# GRR1 sensor thresholds
GRR1_HIGH_GLUCOSE_THRESHOLD = 5.0
GRR1_LOW_GLUCOSE_THRESHOLD = 0.5
BASE_NGAM = 0.7

# Performance settings
FLUX_THRESHOLD = 1e-6  # Minimum flux to include in response
BOTTLENECK_THRESHOLD = 0.01  # Flux below this is a bottleneck
SOLVER_THREADS = 20
