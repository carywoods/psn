"""
PSN GL-Number Extension: Data Integrity & Regression Test Suite

Tests validate the GL-number extension from 10 reactions to 3,857 reactions
covering the entire Yeast-GEM v9.0.2 model.

Test Categories:
1. Schema Integrity
2. GL-Number Integrity
3. Metabolite ID Integrity
4. Stoichiometric Consistency (requires model)
5. No Self-Contradiction
6. Goebl Legacy Preservation
7. Exchange Reaction Exclusion
8. Regression Snapshot
"""

import pytest
import pandas as pd
import numpy as np


# ============================================================================
# CATEGORY 1: SCHEMA INTEGRITY
# ============================================================================

class TestSchemaIntegrity:
    """Validate CSV structure and column names."""

    def test_substrate_product_schema(self, substrate_product_df):
        """Substrate/product CSV has expected columns."""
        expected_columns = ['gl_number', 'met_id', 'role']
        assert list(substrate_product_df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, got {list(substrate_product_df.columns)}"

    def test_metabolite_lookup_schema(self, metabolite_lookup_df):
        """Metabolite lookup CSV has expected columns."""
        expected_columns = ['met_id', 'model_met_id', 'name', 'compartment']
        assert list(metabolite_lookup_df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, got {list(metabolite_lookup_df.columns)}"

    def test_reaction_lookup_schema(self, reaction_lookup_df):
        """Reaction lookup CSV has expected columns."""
        expected_columns = ['gl_number', 'model_reaction_id', 'reaction_name',
                           'subsystem', 'gene_reaction_rule']
        assert list(reaction_lookup_df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, got {list(reaction_lookup_df.columns)}"

    def test_no_null_values_substrate_product(self, substrate_product_df):
        """No null/NaN values in required columns of substrate/product table."""
        required_cols = ['gl_number', 'met_id', 'role']
        for col in required_cols:
            null_count = substrate_product_df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' has {null_count} null values"

    def test_no_null_values_metabolite_lookup(self, metabolite_lookup_df):
        """No null/NaN values in required columns of metabolite lookup."""
        required_cols = ['met_id', 'model_met_id', 'name', 'compartment']
        for col in required_cols:
            null_count = metabolite_lookup_df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' has {null_count} null values"

    def test_no_null_values_reaction_lookup(self, reaction_lookup_df):
        """No null/NaN values in required columns of reaction lookup."""
        # Note: subsystem and gene_reaction_rule can be empty strings, but not NaN
        required_cols = ['gl_number', 'model_reaction_id', 'reaction_name']
        for col in required_cols:
            null_count = reaction_lookup_df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' has {null_count} null values"

    def test_role_values_only_substrate_or_product(self, substrate_product_df):
        """Role column contains only 'SUBSTRATE' or 'PRODUCT'."""
        valid_roles = {'SUBSTRATE', 'PRODUCT'}
        actual_roles = set(substrate_product_df['role'].unique())
        assert actual_roles == valid_roles, \
            f"Expected roles {valid_roles}, found {actual_roles}"


# ============================================================================
# CATEGORY 2: GL-NUMBER INTEGRITY
# ============================================================================

class TestGLNumberIntegrity:
    """Validate GL number uniqueness and ranges."""

    def test_gl_numbers_unique_in_reaction_lookup(self, reaction_lookup_df):
        """GL numbers are unique in reaction lookup (one GL per reaction)."""
        gl_counts = reaction_lookup_df['gl_number'].value_counts()
        duplicates = gl_counts[gl_counts > 1]
        assert len(duplicates) == 0, \
            f"Found {len(duplicates)} duplicate GL numbers: {duplicates.index.tolist()}"

    def test_goebl_range_no_gaps(self, substrate_product_df):
        """Goebl's GL numbers (1000100-1000109) have no gaps."""
        goebl_gls = substrate_product_df[
            substrate_product_df['gl_number'].astype(int).between(1000100, 1000109)
        ]['gl_number'].astype(int).unique()

        expected_goebl_gls = list(range(1000100, 1000110))  # 1000100 through 1000109
        assert sorted(goebl_gls) == expected_goebl_gls, \
            f"Expected {expected_goebl_gls}, got {sorted(goebl_gls)}"

    def test_new_gl_numbers_start_at_1000110(self, reaction_lookup_df):
        """New GL numbers start at 1000110."""
        all_gls = reaction_lookup_df['gl_number'].astype(int).sort_values()
        # Filter to GL numbers > 1000109
        new_gls = all_gls[all_gls > 1000109]

        if len(new_gls) > 0:
            assert new_gls.iloc[0] == 1000110, \
                f"Expected first new GL to be 1000110, got {new_gls.iloc[0]}"

    def test_total_unique_gl_numbers(self, substrate_product_df, expected_summary_stats):
        """Total unique GL numbers matches expected count (3,867)."""
        unique_gls = substrate_product_df['gl_number'].nunique()
        expected = expected_summary_stats['unique_gl_numbers']
        assert unique_gls == expected, \
            f"Expected {expected} unique GL numbers, got {unique_gls}"

    def test_gl_numbers_in_substrate_product_have_lookup(
        self, substrate_product_df, reaction_lookup_df
    ):
        """
        Every GL number in substrate/product table (except Goebl legacy)
        has a corresponding entry in reaction lookup.
        """
        # Get all GL numbers from substrate/product table
        sp_gls = set(substrate_product_df['gl_number'].astype(str))

        # Get all GL numbers from reaction lookup
        rl_gls = set(reaction_lookup_df['gl_number'].astype(str))

        # Filter to non-Goebl GL numbers (> 1000109)
        non_goebl_sp_gls = {gl for gl in sp_gls if int(gl) > 1000109}

        # All non-Goebl GL numbers should have lookup entries
        missing_lookups = non_goebl_sp_gls - rl_gls

        assert len(missing_lookups) == 0, \
            f"Found {len(missing_lookups)} GL numbers without reaction lookup: {sorted(missing_lookups)[:10]}"


# ============================================================================
# CATEGORY 3: METABOLITE ID INTEGRITY
# ============================================================================

class TestMetaboliteIDIntegrity:
    """Validate metabolite ID consistency."""

    def test_met_ids_in_substrate_product_exist_in_lookup(
        self, substrate_product_df, metabolite_lookup_df
    ):
        """
        All met_ids in substrate/product table (excluding Goebl legacy met_ids < 100)
        exist in metabolite lookup.
        """
        # Get met_ids from substrate/product table (excluding legacy < 100)
        sp_met_ids = set(substrate_product_df[substrate_product_df['met_id'] >= 100]['met_id'])

        # Get met_ids from lookup table
        lookup_met_ids = set(metabolite_lookup_df['met_id'])

        # Find missing
        missing_met_ids = sp_met_ids - lookup_met_ids

        assert len(missing_met_ids) == 0, \
            f"Found {len(missing_met_ids)} met_ids without lookup: {sorted(missing_met_ids)[:10]}"

    def test_met_ids_unique_in_lookup(self, metabolite_lookup_df):
        """met_ids in lookup table are unique."""
        met_id_counts = metabolite_lookup_df['met_id'].value_counts()
        duplicates = met_id_counts[met_id_counts > 1]
        assert len(duplicates) == 0, \
            f"Found {len(duplicates)} duplicate met_ids: {duplicates.index.tolist()}"

    def test_new_met_ids_start_at_100(self, metabolite_lookup_df):
        """New met_ids start at 100 (no collision with Goebl's legacy 1-50)."""
        min_met_id = metabolite_lookup_df['met_id'].min()
        assert min_met_id == 100, \
            f"Expected minimum met_id to be 100, got {min_met_id}"

    def test_all_metabolites_have_names(self, metabolite_lookup_df):
        """Every metabolite in lookup table has a non-empty name."""
        empty_names = metabolite_lookup_df[
            metabolite_lookup_df['name'].str.strip() == ''
        ]
        assert len(empty_names) == 0, \
            f"Found {len(empty_names)} metabolites with empty names"


# ============================================================================
# CATEGORY 4: STOICHIOMETRIC CONSISTENCY (requires model)
# ============================================================================

@pytest.mark.slow
class TestStoichiometricConsistency:
    """Validate stoichiometry against Yeast-GEM model."""

    def test_sample_reactions_stoichiometry(
        self, substrate_product_df, reaction_lookup_df,
        metabolite_lookup_df, yeast_model
    ):
        """
        For 50 random GL numbers, verify stoichiometric coefficients
        match model (substrates negative, products positive).
        """
        # Get 50 random GL numbers (seeded for reproducibility)
        np.random.seed(42)
        all_gls = reaction_lookup_df['gl_number'].astype(str).unique()
        sample_gls = np.random.choice(all_gls, size=min(50, len(all_gls)), replace=False)

        errors = []

        for gl_num in sample_gls:
            # Get reaction ID from lookup
            rxn_row = reaction_lookup_df[reaction_lookup_df['gl_number'] == gl_num]
            if len(rxn_row) == 0:
                continue  # Skip if no lookup (Goebl legacy)

            model_rxn_id = rxn_row.iloc[0]['model_reaction_id']

            # Get stoichiometry from model
            if model_rxn_id not in yeast_model.reactions:
                errors.append(f"GL {gl_num}: Reaction {model_rxn_id} not found in model")
                continue

            reaction = yeast_model.reactions.get_by_id(model_rxn_id)
            stoich = {met.id: coeff for met, coeff in reaction.metabolites.items()}

            # Get substrates and products from CSV
            sp_rows = substrate_product_df[substrate_product_df['gl_number'] == gl_num]

            csv_substrates = sp_rows[sp_rows['role'] == 'SUBSTRATE']['met_id'].tolist()
            csv_products = sp_rows[sp_rows['role'] == 'PRODUCT']['met_id'].tolist()

            # Map met_ids to model_met_ids
            def met_id_to_model_id(met_id):
                lookup = metabolite_lookup_df[metabolite_lookup_df['met_id'] == met_id]
                if len(lookup) > 0:
                    return lookup.iloc[0]['model_met_id']
                return None

            # Verify substrates have negative coefficients
            for met_id in csv_substrates:
                model_met_id = met_id_to_model_id(met_id)
                if model_met_id and model_met_id in stoich:
                    if stoich[model_met_id] >= 0:
                        errors.append(
                            f"GL {gl_num}: met_id {met_id} ({model_met_id}) "
                            f"marked as SUBSTRATE but has coefficient {stoich[model_met_id]}"
                        )

            # Verify products have positive coefficients
            for met_id in csv_products:
                model_met_id = met_id_to_model_id(met_id)
                if model_met_id and model_met_id in stoich:
                    if stoich[model_met_id] <= 0:
                        errors.append(
                            f"GL {gl_num}: met_id {met_id} ({model_met_id}) "
                            f"marked as PRODUCT but has coefficient {stoich[model_met_id]}"
                        )

        assert len(errors) == 0, \
            f"Found {len(errors)} stoichiometry errors:\n" + "\n".join(errors[:10])

    @pytest.mark.slow
    def test_sample_reactions_complete_coverage(
        self, substrate_product_df, reaction_lookup_df,
        metabolite_lookup_df, yeast_model
    ):
        """
        For 50 random GL numbers, verify no metabolites from model
        are missing from CSV.
        """
        np.random.seed(42)
        all_gls = reaction_lookup_df['gl_number'].astype(str).unique()
        sample_gls = np.random.choice(all_gls, size=min(50, len(all_gls)), replace=False)

        errors = []

        for gl_num in sample_gls:
            # Get reaction ID from lookup
            rxn_row = reaction_lookup_df[reaction_lookup_df['gl_number'] == gl_num]
            if len(rxn_row) == 0:
                continue

            model_rxn_id = rxn_row.iloc[0]['model_reaction_id']

            # Get stoichiometry from model
            stoich = get_model_reaction_stoichiometry(yeast_model, model_rxn_id)
            if stoich is None:
                continue

            model_met_ids = set(stoich.keys())

            # Get metabolites from CSV
            sp_rows = substrate_product_df[substrate_product_df['gl_number'] == gl_num]
            csv_met_ids_int = sp_rows['met_id'].tolist()

            # Map to model IDs
            csv_model_met_ids = set()
            for met_id in csv_met_ids_int:
                lookup = metabolite_lookup_df[metabolite_lookup_df['met_id'] == met_id]
                if len(lookup) > 0:
                    csv_model_met_ids.add(lookup.iloc[0]['model_met_id'])

            # Check for missing metabolites
            missing = model_met_ids - csv_model_met_ids
            if missing:
                errors.append(
                    f"GL {gl_num} ({model_rxn_id}): Missing metabolites in CSV: {missing}"
                )

        assert len(errors) == 0, \
            f"Found {len(errors)} reactions with missing metabolites:\n" + "\n".join(errors[:10])


# ============================================================================
# CATEGORY 5: NO SELF-CONTRADICTION
# ============================================================================

class TestNoSelfContradiction:
    """Verify no metabolite is both substrate and product in same reaction."""

    def test_no_metabolite_both_substrate_and_product(self, substrate_product_df):
        """No metabolite appears as both SUBSTRATE and PRODUCT within same GL number."""
        errors = []

        for gl_num in substrate_product_df['gl_number'].unique():
            gl_rows = substrate_product_df[substrate_product_df['gl_number'] == gl_num]

            substrates = set(gl_rows[gl_rows['role'] == 'SUBSTRATE']['met_id'])
            products = set(gl_rows[gl_rows['role'] == 'PRODUCT']['met_id'])

            contradiction = substrates & products  # Intersection
            if contradiction:
                errors.append(
                    f"GL {gl_num}: met_ids {contradiction} appear as both SUBSTRATE and PRODUCT"
                )

        assert len(errors) == 0, \
            f"Found {len(errors)} self-contradictions:\n" + "\n".join(errors[:10])


# ============================================================================
# CATEGORY 6: GOEBL LEGACY PRESERVATION
# ============================================================================

class TestGobelLegacyPreservation:
    """Validate preservation of Goebl's original 10 GL entries."""

    def test_goebl_rows_count(self, goebl_legacy_rows, expected_summary_stats):
        """Goebl's legacy rows count is exactly 51."""
        expected = expected_summary_stats['goebl_legacy_rows']
        assert len(goebl_legacy_rows) == expected, \
            f"Expected {expected} Goebl legacy rows, got {len(goebl_legacy_rows)}"

    def test_legacy_met_ids_only_in_goebl_rows(self, substrate_product_df):
        """Legacy met_ids (< 100) appear only in Goebl's legacy rows."""
        # Get all rows with met_id < 100
        legacy_met_id_rows = substrate_product_df[substrate_product_df['met_id'] < 100]

        # All should be in Goebl's GL range
        non_goebl_legacy = legacy_met_id_rows[
            ~legacy_met_id_rows['gl_number'].astype(int).between(1000100, 1000109)
        ]

        assert len(non_goebl_legacy) == 0, \
            f"Found {len(non_goebl_legacy)} legacy met_ids outside Goebl range"

    def test_goebl_range_has_expected_gl_numbers(self, goebl_legacy_rows):
        """Goebl's range contains all 10 expected GL numbers."""
        goebl_gls = sorted(goebl_legacy_rows['gl_number'].astype(int).unique())
        expected = list(range(1000100, 1000110))  # 10 GL numbers
        assert goebl_gls == expected, \
            f"Expected {expected}, got {goebl_gls}"


# ============================================================================
# CATEGORY 7: EXCHANGE REACTION EXCLUSION
# ============================================================================

@pytest.mark.slow
class TestExchangeReactionExclusion:
    """Verify no exchange/boundary reactions included."""

    def test_no_single_metabolite_reactions(
        self, substrate_product_df, reaction_lookup_df
    ):
        """No reaction in lookup has only one metabolite (exchange characteristic)."""
        errors = []

        for gl_num in reaction_lookup_df['gl_number']:
            # Count metabolites for this reaction
            met_count = len(substrate_product_df[substrate_product_df['gl_number'] == gl_num])

            if met_count == 1:
                rxn_info = reaction_lookup_df[reaction_lookup_df['gl_number'] == gl_num].iloc[0]
                errors.append(
                    f"GL {gl_num} ({rxn_info['model_reaction_id']}): "
                    f"Only 1 metabolite (likely exchange reaction)"
                )

        assert len(errors) == 0, \
            f"Found {len(errors)} single-metabolite reactions:\n" + "\n".join(errors[:10])

    @pytest.mark.slow
    def test_no_exchange_reactions_in_lookup(self, reaction_lookup_df, yeast_model):
        """No reaction IDs from model's exchange reactions appear in lookup."""
        # Get all exchange reaction IDs from model
        exchange_rxns = [
            rxn.id for rxn in yeast_model.reactions
            if rxn.id.startswith('r_') and len(rxn.id) == 6 and len(rxn.metabolites) == 1
        ]

        # Check if any are in reaction lookup
        lookup_rxn_ids = set(reaction_lookup_df['model_reaction_id'])
        found_exchanges = set(exchange_rxns) & lookup_rxn_ids

        assert len(found_exchanges) == 0, \
            f"Found {len(found_exchanges)} exchange reactions in lookup: {sorted(found_exchanges)[:10]}"


# ============================================================================
# CATEGORY 8: REGRESSION SNAPSHOT
# ============================================================================

class TestRegressionSnapshot:
    """Hardcoded summary statistics from Milestone 7."""

    def test_total_rows(self, substrate_product_df, expected_summary_stats):
        """Total rows matches expected value (15,344)."""
        actual = len(substrate_product_df)
        expected = expected_summary_stats['total_rows']
        assert actual == expected, \
            f"Expected {expected} total rows, got {actual}"

    def test_unique_gl_numbers(self, substrate_product_df, expected_summary_stats):
        """Unique GL numbers matches expected value (3,867)."""
        actual = substrate_product_df['gl_number'].nunique()
        expected = expected_summary_stats['unique_gl_numbers']
        assert actual == expected, \
            f"Expected {expected} unique GL numbers, got {actual}"

    def test_unique_met_ids_new(self, metabolite_lookup_df, expected_summary_stats):
        """Unique new met_ids (>= 100) matches expected value (2,806)."""
        actual = len(metabolite_lookup_df[metabolite_lookup_df['met_id'] >= 100])
        expected = expected_summary_stats['unique_met_ids_new']
        assert actual == expected, \
            f"Expected {expected} unique new met_ids, got {actual}"

    def test_substrate_rows_count(self, substrate_product_df, expected_summary_stats):
        """Substrate rows matches expected value (7,211)."""
        actual = len(substrate_product_df[substrate_product_df['role'] == 'SUBSTRATE'])
        expected = expected_summary_stats['substrate_rows']
        assert actual == expected, \
            f"Expected {expected} substrate rows, got {actual}"

    def test_product_rows_count(self, substrate_product_df, expected_summary_stats):
        """Product rows matches expected value (8,133)."""
        actual = len(substrate_product_df[substrate_product_df['role'] == 'PRODUCT'])
        expected = expected_summary_stats['product_rows']
        assert actual == expected, \
            f"Expected {expected} product rows, got {actual}"

    def test_goebl_legacy_rows_count(self, goebl_legacy_rows, expected_summary_stats):
        """Goebl legacy rows matches expected value (51)."""
        actual = len(goebl_legacy_rows)
        expected = expected_summary_stats['goebl_legacy_rows']
        assert actual == expected, \
            f"Expected {expected} Goebl legacy rows, got {actual}"

    def test_summary_statistics_snapshot(
        self, substrate_product_df, metabolite_lookup_df, expected_summary_stats
    ):
        """
        Comprehensive snapshot test - all statistics at once.
        This will fail if data is regenerated, forcing conscious review.
        """
        actual_stats = {
            'total_rows': len(substrate_product_df),
            'unique_gl_numbers': substrate_product_df['gl_number'].nunique(),
            'unique_met_ids_new': len(metabolite_lookup_df[metabolite_lookup_df['met_id'] >= 100]),
            'substrate_rows': len(substrate_product_df[substrate_product_df['role'] == 'SUBSTRATE']),
            'product_rows': len(substrate_product_df[substrate_product_df['role'] == 'PRODUCT']),
            'goebl_legacy_rows': len(substrate_product_df[
                substrate_product_df['gl_number'].astype(int).between(1000100, 1000109)
            ]),
        }

        mismatches = []
        for key in actual_stats:
            if actual_stats[key] != expected_summary_stats[key]:
                mismatches.append(
                    f"{key}: expected {expected_summary_stats[key]}, got {actual_stats[key]}"
                )

        assert len(mismatches) == 0, \
            f"Regression snapshot failed - data may have been regenerated:\n" + "\n".join(mismatches)
