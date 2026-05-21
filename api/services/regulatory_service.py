"""
Regulatory Service - Wraps goebl_regulatory_layer.py and grr1_sensor_module.py
"""
import json
import logging
from typing import Optional

from api.config import (
    REGULATORY_MAP_PATH, MODEL_VERSION,
    GRR1_HIGH_GLUCOSE_THRESHOLD, GRR1_LOW_GLUCOSE_THRESHOLD, BASE_NGAM
)

# Import the existing modules from sim_engine
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sim_engine.grr1_sensor_module import apply_grr1_sensor

logger = logging.getLogger(__name__)


class RegulatoryService:
    """Service for Goebl Regulatory Analysis"""

    def __init__(self):
        """Initialize and load regulatory map"""
        self.regulatory_map = self._load_regulatory_map()
        self.target_reactions = self._get_target_reactions()

    def _load_regulatory_map(self) -> dict:
        """Load the regulatory map"""
        if REGULATORY_MAP_PATH.exists():
            with open(REGULATORY_MAP_PATH, "r") as f:
                return json.load(f)
        logger.warning("regulatory_map.json not found")
        return {}

    def _get_target_reactions(self) -> set:
        """Get all reactions targeted by SCF-GRR1"""
        target_reactions = set()
        for symbol, data in self.regulatory_map.items():
            if "reactions" in data:
                target_reactions.update(data["reactions"])
        return target_reactions

    def analyze(
        self,
        glucose_uptake_rate: float,
        gene_knockouts: Optional[list[str]] = None
    ) -> dict:
        """
        Run Goebl regulatory analysis without full FBA.
        Returns regulatory state and affected reactions.
        """
        # Use GRR1 sensor to determine regulatory state
        ngam, proteolytic_tax, mode = apply_grr1_sensor(
            -glucose_uptake_rate,  # Negative because uptake
            BASE_NGAM
        )

        # Determine regulatory state
        if mode == "NUTRIENT_SIGNALING":
            regulatory_state = "glucose_repression"
            grr1_status = "nutrient_signaling_mode"
        elif mode == "REPRESSION_RELEASE":
            regulatory_state = "glucose_repression_release"
            grr1_status = "repression_release"
        else:
            regulatory_state = "normal"
            grr1_status = "normal"

        # Calculate proteolytic burden
        penalty_factor = 0.85 / proteolytic_tax
        proteolytic_burden = 1.0 - penalty_factor

        # Calculate SCF complex activity (inverse of proteolytic tax)
        scf_activity = min(1.0, 1.0 / proteolytic_tax)

        # Calculate affected reactions
        affected_reactions = []
        base_bound = 1000.0  # Default flux bound

        for rid in list(self.target_reactions)[:20]:  # Limit to 20 for response size
            penalized_bound = base_bound * penalty_factor
            affected_reactions.append({
                "reaction_id": rid,
                "original_flux_bound": base_bound,
                "penalized_flux_bound": round(penalized_bound, 2),
                "penalty_fraction": round(proteolytic_burden, 4)
            })

        # Calculate maintenance cost adjustment
        maintenance_adjustment = ngam - BASE_NGAM

        return {
            "proteolytic_burden": round(proteolytic_burden, 4),
            "regulatory_state": regulatory_state,
            "grr1_sensor_status": grr1_status,
            "scf_complex_activity": round(scf_activity, 4),
            "affected_reactions": affected_reactions,
            "maintenance_cost_adjustment": round(maintenance_adjustment, 4)
        }

    def compare(
        self,
        condition_a_label: str,
        condition_a_glucose: float,
        condition_b_label: str,
        condition_b_glucose: float
    ) -> dict:
        """
        Compare Goebl regulatory impact between two conditions.
        """
        # Analyze both conditions
        result_a = self.analyze(condition_a_glucose)
        result_b = self.analyze(condition_b_glucose)

        # Calculate differential
        burden_change = result_a["proteolytic_burden"] - result_b["proteolytic_burden"]
        state_transition = result_a["regulatory_state"] != result_b["regulatory_state"]

        # Find most affected reactions (simplified)
        most_affected = []
        if state_transition:
            # If there's a state transition, identify key pathway reactions
            glycolysis_rxns = [r for r in self.target_reactions if 'r_05' in r][:3]
            for rid in glycolysis_rxns:
                flux_change = burden_change * 100  # Simplified calculation
                most_affected.append({
                    "reaction_id": rid,
                    "flux_change": round(flux_change, 2),
                    "subsystem": "glycolysis"
                })

        return {
            "condition_a": {
                "label": condition_a_label,
                "proteolytic_burden": result_a["proteolytic_burden"],
                "regulatory_state": result_a["regulatory_state"]
            },
            "condition_b": {
                "label": condition_b_label,
                "proteolytic_burden": result_b["proteolytic_burden"],
                "regulatory_state": result_b["regulatory_state"]
            },
            "differential": {
                "burden_change": round(burden_change, 4),
                "state_transition": state_transition,
                "most_affected_reactions": most_affected
            }
        }

    def get_status(self) -> dict:
        """Get current Goebl layer configuration and status"""
        return {
            "version": "1.0.0",
            "high_glucose_threshold": GRR1_HIGH_GLUCOSE_THRESHOLD,
            "low_glucose_threshold": GRR1_LOW_GLUCOSE_THRESHOLD,
            "base_ngam": BASE_NGAM,
            "penalty_factor": 0.85,
            "regulatory_map_loaded": bool(self.regulatory_map),
            "target_reaction_count": len(self.target_reactions)
        }
