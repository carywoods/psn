"""
Pydantic models for Goebl Regulatory Analysis endpoints
"""
from typing import Optional
from pydantic import BaseModel, Field
from .common import Meta


class AffectedReaction(BaseModel):
    """Information about a reaction affected by regulatory layer"""
    reaction_id: str = Field(..., description="COBRA reaction ID")
    original_flux_bound: float = Field(..., description="Original flux bound before penalty")
    penalized_flux_bound: float = Field(..., description="Flux bound after penalty applied")
    penalty_fraction: float = Field(..., description="Fraction of flux penalty applied")


class RegulatoryAnalyzeRequest(BaseModel):
    """Request body for regulatory analysis"""
    glucose_uptake_rate: float = Field(
        ..., description="Glucose uptake rate (mmol/gDW/h)", ge=0.0, le=100.0
    )
    gene_knockouts: Optional[list[str]] = Field(
        default=None, description="List of systematic ORF names to knock out"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "glucose_uptake_rate": 10.5,
                    "gene_knockouts": []
                }
            ]
        }
    }


class RegulatoryAnalyzeResponse(BaseModel):
    """Response for regulatory analysis"""
    proteolytic_burden: float = Field(..., description="Total proteolytic tax coefficient")
    regulatory_state: str = Field(
        ..., description="Current regulatory state (glucose_repression, glucose_repression_release, normal)"
    )
    grr1_sensor_status: str = Field(
        ..., description="GRR1 sensor mode (nutrient_signaling_mode, repression_release, normal)"
    )
    scf_complex_activity: float = Field(
        ..., description="SCF complex activity level (0-1)"
    )
    affected_reactions: list[AffectedReaction] = Field(
        ..., description="Reactions affected by the regulatory layer"
    )
    maintenance_cost_adjustment: float = Field(
        ..., description="NGAM adjustment factor"
    )
    meta: Meta


class ConditionInput(BaseModel):
    """Input for a single condition in comparison"""
    label: str = Field(..., description="Label for this condition")
    glucose_uptake_rate: float = Field(
        ..., description="Glucose uptake rate", ge=0.0, le=100.0
    )


class RegulatoryCompareRequest(BaseModel):
    """Request body for regulatory comparison"""
    condition_a: ConditionInput = Field(..., description="First condition")
    condition_b: ConditionInput = Field(..., description="Second condition")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "condition_a": {
                        "label": "high_glucose",
                        "glucose_uptake_rate": 15.0
                    },
                    "condition_b": {
                        "label": "low_glucose",
                        "glucose_uptake_rate": 2.0
                    }
                }
            ]
        }
    }


class ConditionResult(BaseModel):
    """Result for a single condition"""
    label: str = Field(..., description="Condition label")
    proteolytic_burden: float = Field(..., description="Proteolytic burden")
    regulatory_state: str = Field(..., description="Regulatory state")


class MostAffectedReaction(BaseModel):
    """Most affected reaction in differential analysis"""
    reaction_id: str = Field(..., description="COBRA reaction ID")
    flux_change: float = Field(..., description="Change in flux between conditions")
    subsystem: str = Field(..., description="Metabolic subsystem")


class DifferentialResult(BaseModel):
    """Differential analysis between two conditions"""
    burden_change: float = Field(..., description="Change in proteolytic burden")
    state_transition: bool = Field(..., description="Whether regulatory state changed")
    most_affected_reactions: list[MostAffectedReaction] = Field(
        ..., description="Reactions most affected by the condition change"
    )


class RegulatoryCompareResponse(BaseModel):
    """Response for regulatory comparison"""
    condition_a: ConditionResult = Field(..., description="Results for condition A")
    condition_b: ConditionResult = Field(..., description="Results for condition B")
    differential: DifferentialResult = Field(..., description="Differential analysis")
    meta: Meta


class RegulatoryStatus(BaseModel):
    """Current Goebl layer configuration and status"""
    version: str = Field(..., description="Goebl regulatory layer version")
    high_glucose_threshold: float = Field(
        ..., description="GRR1 high glucose threshold"
    )
    low_glucose_threshold: float = Field(
        ..., description="GRR1 low glucose threshold"
    )
    base_ngam: float = Field(..., description="Base NGAM value")
    penalty_factor: float = Field(..., description="Default penalty factor (0.85)")
    regulatory_map_loaded: bool = Field(
        ..., description="Whether regulatory_map.json is loaded"
    )
    target_reaction_count: int = Field(
        ..., description="Number of reactions under regulatory control"
    )
    meta: Meta
