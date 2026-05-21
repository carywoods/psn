"""
Pydantic models for simulation endpoints
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from .common import Meta


class BottleneckInfo(BaseModel):
    """Information about a metabolic bottleneck"""
    reaction_id: str = Field(..., description="COBRA reaction ID")
    reaction_name: str = Field(..., description="Human-readable reaction name")
    flux: float = Field(..., description="Current flux value")
    subsystem: str = Field(..., description="Metabolic subsystem/pathway")


class FluxDistribution(BaseModel):
    """Wrapper for flux distribution data"""
    fluxes: dict[str, float] = Field(..., description="Reaction ID to flux value mapping")


class SimulateRequest(BaseModel):
    """Request body for FBA simulation"""
    carbon_source: Literal["glucose", "xylose", "galactose", "ethanol", "glycerol"] = Field(
        ..., description="Carbon source for the simulation"
    )
    oxygen_constraint: Literal["aerobic", "anaerobic", "microaerobic"] = Field(
        ..., description="Oxygen availability condition"
    )
    gene_knockouts: Optional[list[str]] = Field(
        default=None, description="List of systematic ORF names to knock out (e.g., YDL022W)"
    )
    apply_goebl_layer: Optional[bool] = Field(
        default=True, description="Whether to apply the Goebl proteolytic tax"
    )
    objective: Optional[Literal["biomass"]] = Field(
        default="biomass", description="Optimization objective (currently only biomass supported)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "carbon_source": "glucose",
                    "oxygen_constraint": "aerobic",
                    "gene_knockouts": ["YDL022W", "YBR249C"],
                    "apply_goebl_layer": True,
                    "objective": "biomass"
                }
            ]
        }
    }


class SimulateResponse(BaseModel):
    """Response body for FBA simulation"""
    status: str = Field(..., description="Solver status (optimal, infeasible, unbounded)")
    growth_rate: float = Field(..., description="Predicted growth rate (1/h)")
    objective_value: float = Field(..., description="Objective function value")
    goebl_tax_applied: bool = Field(..., description="Whether Goebl regulatory layer was applied")
    proteolytic_burden: Optional[float] = Field(
        default=None, description="Total proteolytic tax applied (only if goebl_tax_applied)"
    )
    flux_distribution: dict[str, float] = Field(
        ..., description="Reaction ID to flux value mapping (only |flux| > 1e-6)"
    )
    bottlenecks: list[BottleneckInfo] = Field(
        ..., description="Reactions with low flux that may be limiting"
    )
    knocked_out_genes: list[str] = Field(..., description="Genes that were knocked out")
    carbon_source: str = Field(..., description="Carbon source used")
    oxygen_constraint: str = Field(..., description="Oxygen constraint applied")
    model_version: str = Field(..., description="Yeast-GEM version used")
    computation_time_ms: int = Field(..., description="Wall clock time for simulation in ms")
    meta: Meta


class SimulateOptions(BaseModel):
    """Available simulation options for client UI building"""
    carbon_sources: list[str] = Field(..., description="Available carbon sources")
    oxygen_constraints: list[str] = Field(..., description="Available oxygen constraints")
    objectives: list[str] = Field(..., description="Supported optimization objectives")
    meta: Meta
