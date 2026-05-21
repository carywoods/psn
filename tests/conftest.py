"""
PSN Test Suite Configuration
Shared fixtures for GL-number extension testing
"""

import pytest
import pandas as pd
import cobra
from pathlib import Path


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Data ingestion directory containing CSVs."""
    return project_root / "data_ingestion"


@pytest.fixture(scope="session")
def model_path(project_root):
    """Path to Yeast-GEM model."""
    return project_root / "sim_engine" / "yeast9.xml"


# ============================================================================
# CSV DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def substrate_product_df(data_dir):
    """
    Load gl_substrate_product_full.csv.

    Returns
    -------
    pd.DataFrame
        Complete substrate/product mapping table
    """
    csv_path = data_dir / "gl_substrate_product_full.csv"
    if not csv_path.exists():
        pytest.skip(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, index_col=0)
    return df


@pytest.fixture(scope="session")
def metabolite_lookup_df(data_dir):
    """
    Load met_id_lookup.csv.

    Returns
    -------
    pd.DataFrame
        Metabolite ID lookup table
    """
    csv_path = data_dir / "met_id_lookup.csv"
    if not csv_path.exists():
        pytest.skip(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    return df


@pytest.fixture(scope="session")
def reaction_lookup_df(data_dir):
    """
    Load gl_reaction_lookup.csv.

    Returns
    -------
    pd.DataFrame
        Reaction metadata lookup table
    """
    csv_path = data_dir / "gl_reaction_lookup.csv"
    if not csv_path.exists():
        pytest.skip(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    return df


# ============================================================================
# MODEL FIXTURE
# ============================================================================

@pytest.fixture(scope="session")
def yeast_model(model_path):
    """
    Load Yeast-GEM v9.0.2 model.

    This is marked as slow because model loading takes ~1 second.

    Returns
    -------
    cobra.Model
        Loaded genome-scale metabolic model
    """
    if not model_path.exists():
        pytest.skip(f"Model not found: {model_path}")

    model = cobra.io.read_sbml_model(str(model_path))
    return model


# ============================================================================
# GOEBL LEGACY DATA FIXTURE
# ============================================================================

@pytest.fixture(scope="session")
def goebl_legacy_rows(substrate_product_df):
    """
    Extract Goebl's original 10 GL entries (1000100-1000109).

    Returns
    -------
    pd.DataFrame
        Rows with GL numbers in Goebl's range
    """
    goebl_rows = substrate_product_df[
        substrate_product_df['gl_number'].astype(int).between(1000100, 1000109)
    ]
    return goebl_rows


# ============================================================================
# CONSTANTS
# ============================================================================

@pytest.fixture(scope="session")
def expected_summary_stats():
    """
    Expected summary statistics from Milestone 7.

    These are regression snapshot values - if they change,
    it indicates the data has been regenerated and tests
    need conscious updating.

    Returns
    -------
    dict
        Expected values for regression testing
    """
    return {
        'total_rows': 15344,
        'unique_gl_numbers': 3867,
        'unique_met_ids_new': 2806,  # met_id >= 100
        'substrate_rows': 7211,
        'product_rows': 8133,
        'goebl_legacy_rows': 51,
        'goebl_gl_start': 1000100,
        'goebl_gl_end': 1000109,
        'new_gl_start': 1000110,
        'met_id_start': 100,
    }


# ============================================================================
# HELPER FUNCTIONS (not fixtures, but test utilities)
# ============================================================================

def get_model_reaction_stoichiometry(model, reaction_id):
    """
    Get stoichiometry for a reaction from the model.

    Parameters
    ----------
    model : cobra.Model
        Loaded model
    reaction_id : str
        Reaction ID (e.g., 'r_0001')

    Returns
    -------
    dict
        Dictionary mapping metabolite IDs to stoichiometric coefficients
    """
    if reaction_id not in model.reactions:
        return None

    reaction = model.reactions.get_by_id(reaction_id)
    return {met.id: coeff for met, coeff in reaction.metabolites.items()}
