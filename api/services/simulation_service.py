"""
Simulation Service - Wraps run_fba.py and goebl_regulatory_layer.py
"""
import time
import logging
import json
import os
from typing import Optional
from copy import deepcopy

import cobra

from api.config import (
    MODEL_PATH, REGULATORY_MAP_PATH,
    CARBON_SOURCE_REACTIONS, CARBON_SOURCE_UPTAKE_RATES,
    OXYGEN_CONSTRAINTS, FLUX_THRESHOLD, BOTTLENECK_THRESHOLD,
    SOLVER_THREADS, MODEL_VERSION, BASE_NGAM
)

logger = logging.getLogger(__name__)


class SimulationService:
    """Service for running FBA simulations"""

    def __init__(self, model: cobra.Model):
        """
        Initialize with a pre-loaded COBRA model.
        The model should be loaded once at startup.
        """
        self.base_model = model
        self.regulatory_map = self._load_regulatory_map()

    def _load_regulatory_map(self) -> dict:
        """Load the regulatory map for Goebl tax calculation"""
        if REGULATORY_MAP_PATH.exists():
            with open(REGULATORY_MAP_PATH, "r") as f:
                return json.load(f)
        logger.warning("regulatory_map.json not found, Goebl tax will be limited")
        return {}

    def run_simulation(
        self,
        carbon_source: str,
        oxygen_constraint: str,
        gene_knockouts: Optional[list[str]] = None,
        apply_goebl_layer: bool = True,
        objective: str = "biomass"
    ) -> dict:
        """
        Run FBA simulation with the given parameters.
        Returns a dictionary with results.
        """
        start_time = time.time()

        # Create a copy of the model for this simulation
        model = self.base_model.copy()
        model.solver.configuration.processes = SOLVER_THREADS

        # Track knocked out genes
        knocked_out = []
        invalid_genes = []

        # Apply gene knockouts
        if gene_knockouts:
            for gene_id in gene_knockouts:
                try:
                    gene = model.genes.get_by_id(gene_id)
                    gene.knock_out()
                    knocked_out.append(gene_id)
                except KeyError:
                    invalid_genes.append(gene_id)

        # Return error if any invalid genes
        if invalid_genes:
            return {
                "error": True,
                "error_code": "INVALID_GENE",
                "error_message": f"Gene(s) not found in model: {', '.join(invalid_genes)}",
                "invalid_genes": invalid_genes
            }

        # Set carbon source constraints
        carbon_rxn_id = CARBON_SOURCE_REACTIONS.get(carbon_source)
        if carbon_rxn_id and carbon_rxn_id in model.reactions:
            uptake_rate = CARBON_SOURCE_UPTAKE_RATES.get(carbon_source, -10.0)
            model.reactions.get_by_id(carbon_rxn_id).lower_bound = uptake_rate

        # Set oxygen constraints
        o2_config = OXYGEN_CONSTRAINTS.get(oxygen_constraint)
        if o2_config and o2_config["reaction"] in model.reactions:
            rxn = model.reactions.get_by_id(o2_config["reaction"])
            rxn.lower_bound = o2_config["lower"]
            rxn.upper_bound = o2_config["upper"]

        # Apply Goebl regulatory layer if requested
        proteolytic_burden = None
        affected_reactions_count = 0
        if apply_goebl_layer and self.regulatory_map:
            proteolytic_burden, affected_reactions_count = self._apply_goebl_tax(model)

        # Run optimization
        try:
            solution = model.optimize()
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {
                "error": True,
                "error_code": "OPTIMIZATION_FAILED",
                "error_message": str(e)
            }

        computation_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        status = solution.status
        growth_rate = solution.objective_value if solution.objective_value else 0.0

        # Filter flux distribution to significant values
        flux_distribution = {}
        if solution.fluxes is not None:
            for rxn_id, flux in solution.fluxes.items():
                if abs(flux) > FLUX_THRESHOLD:
                    flux_distribution[rxn_id] = round(flux, 6)

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(model, solution)

        return {
            "error": False,
            "status": status,
            "growth_rate": round(growth_rate, 6),
            "objective_value": round(growth_rate, 6),
            "goebl_tax_applied": apply_goebl_layer,
            "proteolytic_burden": round(proteolytic_burden, 4) if proteolytic_burden else None,
            "flux_distribution": flux_distribution,
            "bottlenecks": bottlenecks,
            "knocked_out_genes": knocked_out,
            "carbon_source": carbon_source,
            "oxygen_constraint": oxygen_constraint,
            "model_version": MODEL_VERSION,
            "computation_time_ms": computation_time_ms
        }

    def _apply_goebl_tax(self, model: cobra.Model, proteolytic_tax: float = 1.0) -> tuple[float, int]:
        """
        Apply the Goebl proteolytic tax to the model.
        Returns (proteolytic_burden, affected_reaction_count)
        """
        # Collect all reactions associated with SCF-GRR1 interactors
        target_reactions = set()
        for symbol, data in self.regulatory_map.items():
            if "reactions" in data:
                target_reactions.update(data["reactions"])

        # Apply 15% penalty to flux bounds
        penalty_factor = 0.85 / proteolytic_tax
        burden = 1.0 - penalty_factor

        count = 0
        for rid in target_reactions:
            if rid in model.reactions:
                rxn = model.reactions.get_by_id(rid)
                rxn.lower_bound *= penalty_factor
                rxn.upper_bound *= penalty_factor
                count += 1

        logger.debug(f"Goebl Tax applied: 15% penalty to {count} reactions")
        return burden, count

    def _identify_bottlenecks(self, model: cobra.Model, solution) -> list[dict]:
        """Identify potential metabolic bottlenecks"""
        bottlenecks = []

        if solution.fluxes is None:
            return bottlenecks

        # Find reactions with very low flux that might be limiting
        for rxn in model.reactions:
            if rxn.id in solution.fluxes:
                flux = abs(solution.fluxes[rxn.id])
                # Check if it's a low-flux reaction in a central pathway
                if flux > 0 and flux < BOTTLENECK_THRESHOLD:
                    subsystem = rxn.subsystem or "unknown"
                    # Focus on central metabolism pathways
                    if any(keyword in subsystem.lower() for keyword in
                           ['glycolysis', 'tca', 'pentose', 'pyruvate', 'oxidative']):
                        bottlenecks.append({
                            "reaction_id": rxn.id,
                            "reaction_name": rxn.name,
                            "flux": round(flux, 6),
                            "subsystem": subsystem
                        })

        # Limit to top 10 bottlenecks
        return bottlenecks[:10]

    def get_options(self) -> dict:
        """Get available simulation options"""
        return {
            "carbon_sources": list(CARBON_SOURCE_REACTIONS.keys()),
            "oxygen_constraints": list(OXYGEN_CONSTRAINTS.keys()),
            "objectives": ["biomass"]
        }
