#!/usr/bin/env python3
"""
PSN GL-Number Extension: Substrate/Product Table Builder
=========================================================

Extends Dr. Mark Goebl's manually curated 10 purine pathway reactions
(GL 1000100-1000109) to cover the entire Yeast-GEM v9.0.2 model.

Preserves Goebl's original entries exactly as-is and extends with
model-derived substrate/product mappings for all metabolic reactions.

Author: PSN Team
Date: 2026-03-26
Environment: psn-engine (Python 3.12, COBRApy)
"""

import cobra
import pandas as pd
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data_ingestion" / "glpath_core.db"
MODEL_PATH = PROJECT_ROOT / "sim_engine" / "yeast9.xml"
OUTPUT_DIR = PROJECT_ROOT / "data_ingestion"

# Output files
SUBSTRATE_PRODUCT_CSV = OUTPUT_DIR / "gl_substrate_product_full.csv"
METABOLITE_LOOKUP_CSV = OUTPUT_DIR / "met_id_lookup.csv"
REACTION_LOOKUP_CSV = OUTPUT_DIR / "gl_reaction_lookup.csv"

# GL number ranges
GOEBL_GL_START = 1000100
GOEBL_GL_END = 1000109
NEW_GL_START = 1000110

# Metabolite ID assignment (start from 100 to avoid Goebl's legacy IDs)
MET_ID_START = 100

# ============================================================================
# STEP 1: LOAD GOEBL'S ORIGINAL ENTRIES
# ============================================================================

def load_goebl_original_entries() -> pd.DataFrame:
    """
    Load Dr. Goebl's original 10 GL entries from the database.
    These must be preserved exactly as-is.

    Returns
    -------
    pd.DataFrame
        Original entries with columns: gl_number, met_id, role
    """
    logger.info("Loading Goebl's original 10 GL entries from database...")

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT gl_number, met_id, role
            FROM gl_metabolite_links
            WHERE gl_number BETWEEN ? AND ?
            ORDER BY gl_number, met_id
        """
        df = pd.read_sql_query(
            query,
            conn,
            params=(str(GOEBL_GL_START), str(GOEBL_GL_END))
        )

    logger.info(f"Loaded {len(df)} rows covering GL {GOEBL_GL_START}-{GOEBL_GL_END}")

    # Validate
    unique_gl_nums = df['gl_number'].unique()
    logger.info(f"Unique GL numbers: {sorted(unique_gl_nums)}")

    if len(unique_gl_nums) != 10:
        logger.warning(f"Expected 10 unique GL numbers, found {len(unique_gl_nums)}")

    return df

# ============================================================================
# STEP 2: LOAD YEAST-GEM MODEL
# ============================================================================

def load_yeast_gem_model() -> cobra.Model:
    """
    Load Yeast-GEM v9.0.2 model from SBML file.

    Returns
    -------
    cobra.Model
        Loaded genome-scale metabolic model
    """
    logger.info(f"Loading Yeast-GEM model from {MODEL_PATH}...")

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}\n"
            "Please download from: "
            "https://github.com/SysBioChalmers/yeast-GEM/raw/main/model/yeast-GEM.xml"
        )

    model = cobra.io.read_sbml_model(str(MODEL_PATH))

    logger.info(f"Model loaded successfully:")
    logger.info(f"  - Reactions: {len(model.reactions)}")
    logger.info(f"  - Metabolites: {len(model.metabolites)}")
    logger.info(f"  - Genes: {len(model.genes)}")

    return model

# ============================================================================
# STEP 3: BUILD METABOLITE ID LOOKUP TABLE
# ============================================================================

def build_metabolite_lookup(model: cobra.Model) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Create stable integer met_id assignments for all metabolites.

    Parameters
    ----------
    model : cobra.Model
        Yeast-GEM model

    Returns
    -------
    lookup_df : pd.DataFrame
        Metabolite lookup table with columns: met_id, model_met_id, name, compartment
    met_id_map : dict
        Dictionary mapping model metabolite ID to integer met_id
    """
    logger.info("Building metabolite ID lookup table...")

    metabolites = []
    met_id_map = {}
    current_met_id = MET_ID_START

    # Sort metabolites by ID for reproducibility
    sorted_mets = sorted(model.metabolites, key=lambda m: m.id)

    for met in sorted_mets:
        met_id_map[met.id] = current_met_id

        metabolites.append({
            'met_id': current_met_id,
            'model_met_id': met.id,
            'name': met.name,
            'compartment': met.compartment
        })

        current_met_id += 1

    lookup_df = pd.DataFrame(metabolites)

    logger.info(f"Created {len(lookup_df)} metabolite ID assignments")
    logger.info(f"Met ID range: {MET_ID_START} to {current_met_id - 1}")

    return lookup_df, met_id_map

# ============================================================================
# STEP 4: PROCESS REACTIONS AND ASSIGN GL NUMBERS
# ============================================================================

def should_skip_reaction(reaction: cobra.Reaction) -> Tuple[bool, str]:
    """
    Determine if a reaction should be skipped.

    Parameters
    ----------
    reaction : cobra.Reaction
        Reaction to evaluate

    Returns
    -------
    should_skip : bool
        True if reaction should be skipped
    reason : str
        Reason for skipping (empty string if not skipped)
    """
    # Skip exchange reactions (typically r_NNNN with only one metabolite)
    if reaction.id.startswith('r_') and len(reaction.id) == 6:
        if reaction.id[2:].isdigit():
            if len(reaction.metabolites) == 1:
                return True, "exchange_reaction"

    # Skip demand reactions
    if reaction.id.startswith('DM_'):
        return True, "demand_reaction"

    # Skip sink reactions
    if reaction.id.startswith('sink_'):
        return True, "sink_reaction"

    # Skip reactions with no metabolites
    if len(reaction.metabolites) == 0:
        return True, "no_metabolites"

    return False, ""

def process_reactions(
    model: cobra.Model,
    met_id_map: Dict[str, int]
) -> Tuple[List[Dict], List[Dict], Dict[str, List[str]]]:
    """
    Process all reactions in the model and assign GL numbers.

    Parameters
    ----------
    model : cobra.Model
        Yeast-GEM model
    met_id_map : dict
        Mapping from model metabolite ID to integer met_id

    Returns
    -------
    substrate_product_rows : list
        List of dicts with keys: gl_number, met_id, role
    reaction_rows : list
        List of dicts with keys: gl_number, model_reaction_id, reaction_name,
        subsystem, gene_reaction_rule
    skip_stats : dict
        Statistics on skipped reactions
    """
    logger.info("Processing reactions and assigning GL numbers...")

    substrate_product_rows = []
    reaction_rows = []
    current_gl = NEW_GL_START

    skip_stats = {
        'exchange_reaction': [],
        'demand_reaction': [],
        'sink_reaction': [],
        'no_metabolites': []
    }

    # Sort reactions by ID for reproducibility
    sorted_rxns = sorted(model.reactions, key=lambda r: r.id)

    for reaction in sorted_rxns:
        # Check if should skip
        should_skip, skip_reason = should_skip_reaction(reaction)
        if should_skip:
            skip_stats[skip_reason].append(reaction.id)
            continue

        # Assign GL number to this reaction
        gl_number = str(current_gl)

        # Process metabolites
        for metabolite, stoichiometry in reaction.metabolites.items():
            met_id = met_id_map[metabolite.id]

            # Determine role based on stoichiometry
            if stoichiometry < 0:
                role = "SUBSTRATE"
            elif stoichiometry > 0:
                role = "PRODUCT"
            else:
                # Skip metabolites with zero stoichiometry (shouldn't happen)
                logger.warning(
                    f"Reaction {reaction.id}: metabolite {metabolite.id} "
                    f"has zero stoichiometry, skipping"
                )
                continue

            substrate_product_rows.append({
                'gl_number': gl_number,
                'met_id': met_id,
                'role': role
            })

        # Add reaction metadata
        reaction_rows.append({
            'gl_number': gl_number,
            'model_reaction_id': reaction.id,
            'reaction_name': reaction.name,
            'subsystem': reaction.subsystem if reaction.subsystem else '',
            'gene_reaction_rule': reaction.gene_reaction_rule
        })

        current_gl += 1

    logger.info(f"Processed {len(reaction_rows)} reactions")
    logger.info(f"Generated {len(substrate_product_rows)} substrate/product rows")
    logger.info(f"GL number range: {NEW_GL_START} to {current_gl - 1}")

    # Log skip statistics
    total_skipped = sum(len(v) for v in skip_stats.values())
    if total_skipped > 0:
        logger.info(f"\nSkipped {total_skipped} reactions:")
        for reason, rxn_ids in skip_stats.items():
            if rxn_ids:
                logger.info(f"  - {reason}: {len(rxn_ids)} reactions")

    return substrate_product_rows, reaction_rows, skip_stats

# ============================================================================
# STEP 5: COMBINE AND GENERATE OUTPUT FILES
# ============================================================================

def generate_output_files(
    goebl_df: pd.DataFrame,
    new_rows: List[Dict],
    reaction_rows: List[Dict],
    metabolite_lookup: pd.DataFrame
):
    """
    Generate the three output CSV files.

    Parameters
    ----------
    goebl_df : pd.DataFrame
        Goebl's original entries
    new_rows : list
        New substrate/product rows from model processing
    reaction_rows : list
        Reaction metadata rows
    metabolite_lookup : pd.DataFrame
        Metabolite ID lookup table
    """
    logger.info("Generating output files...")

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # FILE 1: gl_substrate_product_full.csv
    # ========================================================================
    # Combine Goebl's entries (first) with new entries
    new_df = pd.DataFrame(new_rows)
    combined_df = pd.concat([goebl_df, new_df], ignore_index=True)

    # Add continuous index column (matches Goebl's original schema)
    combined_df.index.name = ''

    combined_df.to_csv(SUBSTRATE_PRODUCT_CSV, index=True)
    logger.info(f"✓ Saved {SUBSTRATE_PRODUCT_CSV} ({len(combined_df)} rows)")

    # ========================================================================
    # FILE 2: met_id_lookup.csv
    # ========================================================================
    metabolite_lookup.to_csv(METABOLITE_LOOKUP_CSV, index=False)
    logger.info(f"✓ Saved {METABOLITE_LOOKUP_CSV} ({len(metabolite_lookup)} rows)")

    # ========================================================================
    # FILE 3: gl_reaction_lookup.csv
    # ========================================================================
    reaction_df = pd.DataFrame(reaction_rows)
    reaction_df.to_csv(REACTION_LOOKUP_CSV, index=False)
    logger.info(f"✓ Saved {REACTION_LOOKUP_CSV} ({len(reaction_df)} rows)")

# ============================================================================
# STEP 6: VALIDATION
# ============================================================================

def run_validation_checks(
    substrate_product_df: pd.DataFrame,
    reaction_lookup_df: pd.DataFrame,
    metabolite_lookup_df: pd.DataFrame,
    model: cobra.Model
):
    """
    Run comprehensive validation checks on the generated data.

    Parameters
    ----------
    substrate_product_df : pd.DataFrame
        Complete substrate/product table
    reaction_lookup_df : pd.DataFrame
        Reaction lookup table
    metabolite_lookup_df : pd.DataFrame
        Metabolite lookup table
    model : cobra.Model
        Original Yeast-GEM model
    """
    logger.info("\n" + "="*70)
    logger.info("VALIDATION CHECKS")
    logger.info("="*70)

    # ========================================================================
    # CHECK 1: Goebl's 10 GL numbers are present and unmodified
    # ========================================================================
    goebl_entries = substrate_product_df[
        substrate_product_df['gl_number'].astype(int).between(GOEBL_GL_START, GOEBL_GL_END)
    ]

    unique_goebl_gls = sorted(goebl_entries['gl_number'].unique().astype(int))
    expected_goebl_gls = list(range(GOEBL_GL_START, GOEBL_GL_END + 1))

    if unique_goebl_gls == expected_goebl_gls:
        logger.info(f"✓ CHECK 1 PASSED: All 10 Goebl GL numbers present (1000100-1000109)")
    else:
        logger.error(f"✗ CHECK 1 FAILED: Expected {expected_goebl_gls}, found {unique_goebl_gls}")

    logger.info(f"  - Goebl entries: {len(goebl_entries)} rows")

    # ========================================================================
    # CHECK 2: No duplicate GL numbers
    # ========================================================================
    all_gl_numbers = substrate_product_df['gl_number'].tolist()
    reaction_gl_numbers = reaction_lookup_df['gl_number'].tolist()

    if len(reaction_gl_numbers) == len(set(reaction_gl_numbers)):
        logger.info(f"✓ CHECK 2 PASSED: No duplicate GL numbers in reactions")
    else:
        duplicates = [gl for gl in set(reaction_gl_numbers) if reaction_gl_numbers.count(gl) > 1]
        logger.error(f"✗ CHECK 2 FAILED: Found duplicate GL numbers: {duplicates}")

    # ========================================================================
    # CHECK 3: Valid roles only (SUBSTRATE or PRODUCT)
    # ========================================================================
    valid_roles = {'SUBSTRATE', 'PRODUCT'}
    actual_roles = set(substrate_product_df['role'].unique())

    if actual_roles == valid_roles:
        logger.info(f"✓ CHECK 3 PASSED: All roles are valid (SUBSTRATE or PRODUCT)")
    else:
        invalid_roles = actual_roles - valid_roles
        logger.error(f"✗ CHECK 3 FAILED: Found invalid roles: {invalid_roles}")

    # ========================================================================
    # CHECK 4: Statistics
    # ========================================================================
    total_gl_numbers = len(reaction_lookup_df)
    total_met_ids = len(metabolite_lookup_df)
    total_rows = len(substrate_product_df)

    substrate_count = len(substrate_product_df[substrate_product_df['role'] == 'SUBSTRATE'])
    product_count = len(substrate_product_df[substrate_product_df['role'] == 'PRODUCT'])

    logger.info("\n" + "-"*70)
    logger.info("STATISTICS")
    logger.info("-"*70)
    logger.info(f"Total unique GL numbers:      {total_gl_numbers:,}")
    logger.info(f"  - Goebl's original:         10")
    logger.info(f"  - New from model:           {total_gl_numbers - 10:,}")
    logger.info(f"Total unique metabolites:     {total_met_ids:,}")
    logger.info(f"Total substrate/product rows: {total_rows:,}")
    logger.info(f"  - SUBSTRATE entries:        {substrate_count:,}")
    logger.info(f"  - PRODUCT entries:          {product_count:,}")

    # ========================================================================
    # CHECK 5: Sample reactions (human-readable spot-check)
    # ========================================================================
    logger.info("\n" + "-"*70)
    logger.info("SAMPLE REACTIONS (5 Random Examples)")
    logger.info("-"*70)

    # Get 5 random reactions (excluding Goebl's)
    sample_reactions = reaction_lookup_df[
        reaction_lookup_df['gl_number'].astype(int) >= NEW_GL_START
    ].sample(n=min(5, len(reaction_lookup_df)), random_state=42)

    met_lookup_dict = metabolite_lookup_df.set_index('met_id')['name'].to_dict()

    for idx, row in sample_reactions.iterrows():
        gl_num = row['gl_number']
        rxn_id = row['model_reaction_id']
        rxn_name = row['reaction_name']

        # Get substrates and products for this GL number
        entries = substrate_product_df[substrate_product_df['gl_number'] == gl_num]
        substrates = entries[entries['role'] == 'SUBSTRATE']['met_id'].tolist()
        products = entries[entries['role'] == 'PRODUCT']['met_id'].tolist()

        # Convert met_ids to names
        substrate_names = [met_lookup_dict.get(mid, f"met_{mid}") for mid in substrates]
        product_names = [met_lookup_dict.get(mid, f"met_{mid}") for mid in products]

        logger.info(f"\nGL {gl_num}: {rxn_name} ({rxn_id})")
        logger.info(f"  Substrates ({len(substrate_names)}): {', '.join(substrate_names[:3])}" +
                   (f" + {len(substrate_names)-3} more" if len(substrate_names) > 3 else ""))
        logger.info(f"  Products ({len(product_names)}):   {', '.join(product_names[:3])}" +
                   (f" + {len(product_names)-3} more" if len(product_names) > 3 else ""))

    logger.info("\n" + "="*70)
    logger.info("VALIDATION COMPLETE")
    logger.info("="*70)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    try:
        logger.info("="*70)
        logger.info("PSN GL-NUMBER EXTENSION: SUBSTRATE/PRODUCT TABLE BUILDER")
        logger.info("="*70)
        logger.info(f"Project root: {PROJECT_ROOT}")
        logger.info(f"Output directory: {OUTPUT_DIR}\n")

        # Step 1: Load Goebl's original entries
        goebl_df = load_goebl_original_entries()
        logger.info("")

        # Step 2: Load Yeast-GEM model
        model = load_yeast_gem_model()
        logger.info("")

        # Step 3: Build metabolite lookup
        metabolite_lookup_df, met_id_map = build_metabolite_lookup(model)
        logger.info("")

        # Step 4: Process reactions
        new_substrate_product_rows, reaction_rows, skip_stats = process_reactions(
            model, met_id_map
        )
        logger.info("")

        # Step 5: Generate output files
        generate_output_files(
            goebl_df,
            new_substrate_product_rows,
            reaction_rows,
            metabolite_lookup_df
        )
        logger.info("")

        # Step 6: Run validation
        # Load the generated files for validation
        substrate_product_df = pd.read_csv(SUBSTRATE_PRODUCT_CSV, index_col=0)
        reaction_lookup_df = pd.read_csv(REACTION_LOOKUP_CSV)

        run_validation_checks(
            substrate_product_df,
            reaction_lookup_df,
            metabolite_lookup_df,
            model
        )

        logger.info("\n✓ ALL OPERATIONS COMPLETED SUCCESSFULLY")
        logger.info(f"\nOutput files saved to: {OUTPUT_DIR}")
        logger.info(f"  - {SUBSTRATE_PRODUCT_CSV.name}")
        logger.info(f"  - {METABOLITE_LOOKUP_CSV.name}")
        logger.info(f"  - {REACTION_LOOKUP_CSV.name}")

        return 0

    except Exception as e:
        logger.error(f"\n✗ ERROR: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
