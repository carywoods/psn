"""
Registry Service - Wraps CSV lookups and database queries for GL-Number Registry
"""
import sqlite3
import logging
from typing import Optional
from datetime import datetime

import pandas as pd

from api.config import (
    DATABASE_PATH, GL_SUBSTRATE_PRODUCT_PATH,
    MET_ID_LOOKUP_PATH, GL_REACTION_LOOKUP_PATH, MODEL_VERSION
)

logger = logging.getLogger(__name__)


class RegistryService:
    """Service for GL-Number Registry lookups"""

    def __init__(self):
        """Initialize and load data into memory"""
        self.db_path = DATABASE_PATH
        self.gl_substrate_product_df = None
        self.met_id_lookup_df = None
        self.gl_reaction_lookup_df = None
        self._load_data()

    def _load_data(self):
        """Load CSV files into memory for fast lookups"""
        try:
            if GL_SUBSTRATE_PRODUCT_PATH.exists():
                self.gl_substrate_product_df = pd.read_csv(GL_SUBSTRATE_PRODUCT_PATH)
                logger.info(f"Loaded {len(self.gl_substrate_product_df)} substrate/product mappings")
            else:
                logger.warning(f"File not found: {GL_SUBSTRATE_PRODUCT_PATH}")

            if MET_ID_LOOKUP_PATH.exists():
                self.met_id_lookup_df = pd.read_csv(MET_ID_LOOKUP_PATH)
                logger.info(f"Loaded {len(self.met_id_lookup_df)} metabolite lookups")
            else:
                logger.warning(f"File not found: {MET_ID_LOOKUP_PATH}")

            if GL_REACTION_LOOKUP_PATH.exists():
                self.gl_reaction_lookup_df = pd.read_csv(GL_REACTION_LOOKUP_PATH)
                logger.info(f"Loaded {len(self.gl_reaction_lookup_df)} reaction lookups")
            else:
                logger.warning(f"File not found: {GL_REACTION_LOOKUP_PATH}")

        except Exception as e:
            logger.error(f"Error loading registry data: {e}")

    def _get_db_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)

    def lookup_gene(self, identifier: str) -> Optional[dict]:
        """
        Look up a gene by systematic ORF name or common name.
        Returns gene info with GLNumber, EC codes, and associated reactions.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Search by ORF ID or common name
        cursor.execute("""
            SELECT gl_number, orf_id, common_name, ec_number, functional_role
            FROM global_registry
            WHERE orf_id = ? OR common_name = ? COLLATE NOCASE
        """, (identifier.upper(), identifier.upper()))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        gl_number = int(row[0]) if row[0] and row[0].isdigit() else 0
        orf_id = row[1]
        common_name = row[2]
        ec_number = row[3]
        functional_role = row[4]

        # Parse EC codes
        ec_codes = [ec_number] if ec_number and ec_number != "N/A" else []

        # Find associated reactions
        associated_reactions = self._find_reactions_for_gene(orf_id)

        return {
            "gl_number": gl_number,
            "systematic_name": orf_id,
            "common_name": common_name or orf_id,
            "ec_codes": ec_codes,
            "metabolic_role": functional_role or "Unknown",
            "associated_reactions": associated_reactions
        }

    def _find_reactions_for_gene(self, orf_id: str) -> list[dict]:
        """Find all reactions associated with a gene"""
        reactions = []

        if self.gl_reaction_lookup_df is None:
            return reactions

        # Search for gene in gene_reaction_rule column
        mask = self.gl_reaction_lookup_df['gene_reaction_rule'].str.contains(
            orf_id, case=False, na=False
        )

        for _, row in self.gl_reaction_lookup_df[mask].head(20).iterrows():
            reactions.append({
                "gl_number": int(row['gl_number']),
                "reaction_name": row['reaction_name'],
                "subsystem": row['subsystem'] or "Unknown"
            })

        return reactions

    def lookup_reaction(self, gl_number: int) -> Optional[dict]:
        """
        Look up a reaction by GLNumber.
        Returns reaction info with substrates, products, and gene associations.
        """
        if self.gl_reaction_lookup_df is None:
            return None

        # Find the reaction
        matches = self.gl_reaction_lookup_df[
            self.gl_reaction_lookup_df['gl_number'] == gl_number
        ]

        if matches.empty:
            return None

        row = matches.iloc[0]

        # Get substrates and products
        substrates = self._get_metabolites_for_reaction(gl_number, "SUBSTRATE")
        products = self._get_metabolites_for_reaction(gl_number, "PRODUCT")

        return {
            "gl_number": int(row['gl_number']),
            "model_reaction_id": row['model_reaction_id'],
            "reaction_name": row['reaction_name'],
            "subsystem": row['subsystem'] or "Unknown",
            "gene_reaction_rule": row['gene_reaction_rule'] or "",
            "substrates": substrates,
            "products": products
        }

    def _get_metabolites_for_reaction(self, gl_number: int, role: str) -> list[dict]:
        """Get substrates or products for a reaction"""
        metabolites = []

        if self.gl_substrate_product_df is None or self.met_id_lookup_df is None:
            return metabolites

        # Find met_ids for this reaction and role
        mask = (
            (self.gl_substrate_product_df['gl_number'] == gl_number) &
            (self.gl_substrate_product_df['role'] == role)
        )

        for _, row in self.gl_substrate_product_df[mask].iterrows():
            met_id = int(row['met_id'])

            # Look up metabolite details
            met_matches = self.met_id_lookup_df[self.met_id_lookup_df['met_id'] == met_id]

            if not met_matches.empty:
                met_row = met_matches.iloc[0]
                metabolites.append({
                    "met_id": met_id,
                    "name": met_row['name'],
                    "compartment": self._expand_compartment(met_row['compartment'])
                })

        return metabolites

    def _expand_compartment(self, abbrev: str) -> str:
        """Expand compartment abbreviation to full name"""
        compartment_map = {
            'c': 'cytoplasm',
            'ce': 'cell envelope',
            'e': 'extracellular',
            'm': 'mitochondria',
            'n': 'nucleus',
            'er': 'endoplasmic reticulum',
            'erm': 'endoplasmic reticulum membrane',
            'g': 'golgi',
            'gm': 'golgi membrane',
            'mm': 'mitochondrial membrane',
            'p': 'peroxisome',
            'pm': 'peroxisomal membrane',
            'v': 'vacuole',
            'vm': 'vacuolar membrane'
        }
        return compartment_map.get(abbrev, abbrev)

    def lookup_metabolite(self, met_id: int) -> Optional[dict]:
        """
        Look up a metabolite by met_id.
        Returns metabolite info with reactions it participates in.
        """
        if self.met_id_lookup_df is None:
            return None

        matches = self.met_id_lookup_df[self.met_id_lookup_df['met_id'] == met_id]

        if matches.empty:
            return None

        row = matches.iloc[0]

        # Find reactions where this is a substrate or product
        reactions_as_substrate = self._find_reactions_for_metabolite(met_id, "SUBSTRATE")
        reactions_as_product = self._find_reactions_for_metabolite(met_id, "PRODUCT")

        return {
            "met_id": int(row['met_id']),
            "model_met_id": row['model_met_id'],
            "name": row['name'],
            "compartment": self._expand_compartment(row['compartment']),
            "reactions_as_substrate": reactions_as_substrate,
            "reactions_as_product": reactions_as_product
        }

    def _find_reactions_for_metabolite(self, met_id: int, role: str) -> list[dict]:
        """Find reactions where a metabolite participates as substrate or product"""
        reactions = []

        if self.gl_substrate_product_df is None or self.gl_reaction_lookup_df is None:
            return reactions

        # Find gl_numbers for this metabolite
        mask = (
            (self.gl_substrate_product_df['met_id'] == met_id) &
            (self.gl_substrate_product_df['role'] == role)
        )

        gl_numbers = self.gl_substrate_product_df[mask]['gl_number'].unique()

        for gl_num in gl_numbers[:20]:  # Limit to 20
            rxn_matches = self.gl_reaction_lookup_df[
                self.gl_reaction_lookup_df['gl_number'] == gl_num
            ]
            if not rxn_matches.empty:
                rxn_row = rxn_matches.iloc[0]
                reactions.append({
                    "gl_number": int(gl_num),
                    "reaction_name": rxn_row['reaction_name'],
                    "subsystem": rxn_row['subsystem'] or "Unknown"
                })

        return reactions

    def search(self, query: str, limit: int = 20) -> dict:
        """
        Full-text search across genes, reactions, metabolites, and subsystems.
        Returns top results ranked by relevance.
        """
        if len(query) < 2:
            return {"query": query, "results": [], "total_count": 0}

        results = []
        query_lower = query.lower()

        # Search genes in database
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gl_number, orf_id, common_name, functional_role
            FROM global_registry
            WHERE orf_id LIKE ? OR common_name LIKE ? OR functional_role LIKE ?
            LIMIT 10
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        for row in cursor.fetchall():
            results.append({
                "type": "gene",
                "identifier": row[1],
                "name": row[2] or row[1],
                "description": row[3],
                "gl_number": int(row[0]) if row[0] and str(row[0]).isdigit() else None
            })
        conn.close()

        # Search reactions
        if self.gl_reaction_lookup_df is not None:
            mask = (
                self.gl_reaction_lookup_df['reaction_name'].str.contains(query, case=False, na=False) |
                self.gl_reaction_lookup_df['subsystem'].str.contains(query, case=False, na=False)
            )
            for _, row in self.gl_reaction_lookup_df[mask].head(10).iterrows():
                results.append({
                    "type": "reaction",
                    "identifier": row['model_reaction_id'],
                    "name": row['reaction_name'],
                    "description": row['subsystem'],
                    "gl_number": int(row['gl_number'])
                })

        # Search metabolites
        if self.met_id_lookup_df is not None:
            mask = self.met_id_lookup_df['name'].str.contains(query, case=False, na=False)
            for _, row in self.met_id_lookup_df[mask].head(10).iterrows():
                results.append({
                    "type": "metabolite",
                    "identifier": str(row['met_id']),
                    "name": row['name'],
                    "description": f"Compartment: {self._expand_compartment(row['compartment'])}",
                    "gl_number": None
                })

        # Deduplicate and limit
        seen = set()
        unique_results = []
        for r in results:
            key = (r['type'], r['identifier'])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return {
            "query": query,
            "results": unique_results[:limit],
            "total_count": len(unique_results)
        }

    def get_pathway(self, subsystem: str) -> Optional[dict]:
        """
        Get all reactions in a given subsystem/pathway.
        """
        if self.gl_reaction_lookup_df is None:
            return None

        # Find reactions in this subsystem
        mask = self.gl_reaction_lookup_df['subsystem'].str.contains(
            subsystem, case=False, na=False
        )

        if not mask.any():
            return None

        reactions = []
        for _, row in self.gl_reaction_lookup_df[mask].iterrows():
            gl_number = int(row['gl_number'])
            substrates = self._get_metabolites_for_reaction(gl_number, "SUBSTRATE")
            products = self._get_metabolites_for_reaction(gl_number, "PRODUCT")

            reactions.append({
                "gl_number": gl_number,
                "model_reaction_id": row['model_reaction_id'],
                "reaction_name": row['reaction_name'],
                "subsystem": row['subsystem'],
                "gene_reaction_rule": row['gene_reaction_rule'] or "",
                "substrates": substrates,
                "products": products
            })

        return {
            "subsystem": subsystem,
            "reactions": reactions,
            "reaction_count": len(reactions)
        }

    def get_stats(self) -> dict:
        """Get registry summary statistics"""
        stats = {
            "total_gl_numbers": 0,
            "total_metabolites": 0,
            "total_reactions": 0,
            "total_genes": 0,
            "model_version": MODEL_VERSION,
            "build_date": "2026-03-26"
        }

        # Count genes from database
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM global_registry")
            stats["total_genes"] = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            logger.error(f"Error counting genes: {e}")

        # Count from DataFrames
        if self.gl_reaction_lookup_df is not None:
            stats["total_reactions"] = len(self.gl_reaction_lookup_df)
            stats["total_gl_numbers"] = self.gl_reaction_lookup_df['gl_number'].nunique()

        if self.met_id_lookup_df is not None:
            stats["total_metabolites"] = len(self.met_id_lookup_df)

        return stats
