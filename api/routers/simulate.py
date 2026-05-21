"""
Simulation Router - /v1/simulate endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_api_key
from api.models.simulate import (
    SimulateRequest, SimulateResponse, SimulateOptions, BottleneckInfo
)
from api.models.common import Meta, ErrorDetail
from api.config import API_VERSION, MODEL_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/simulate", tags=["Metabolic Simulation"])

# Service will be injected at startup
_simulation_service = None


def get_simulation_service():
    """Dependency to get the simulation service"""
    if _simulation_service is None:
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": "Simulation service not initialized"}}
        )
    return _simulation_service


def set_simulation_service(service):
    """Set the simulation service (called at startup)"""
    global _simulation_service
    _simulation_service = service


@router.post(
    "",
    response_model=SimulateResponse,
    summary="Run FBA Simulation",
    description="Run Flux Balance Analysis on a yeast strain configuration with optional Goebl regulatory layer."
)
async def run_simulation(
    request: SimulateRequest,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_simulation_service)
):
    """
    Run a metabolic simulation with the specified parameters.

    - **carbon_source**: Carbon source for growth (glucose, xylose, galactose, ethanol, glycerol)
    - **oxygen_constraint**: Oxygen availability (aerobic, anaerobic, microaerobic)
    - **gene_knockouts**: List of genes to knock out (systematic ORF names)
    - **apply_goebl_layer**: Whether to apply the proprietary Goebl proteolytic tax
    - **objective**: Optimization objective (currently only biomass)
    """
    logger.info(f"Simulation request: {request.carbon_source}/{request.oxygen_constraint}, "
                f"knockouts={request.gene_knockouts}, goebl={request.apply_goebl_layer}")

    result = service.run_simulation(
        carbon_source=request.carbon_source,
        oxygen_constraint=request.oxygen_constraint,
        gene_knockouts=request.gene_knockouts,
        apply_goebl_layer=request.apply_goebl_layer,
        objective=request.objective
    )

    # Check for errors
    if result.get("error"):
        if result.get("error_code") == "INVALID_GENE":
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "INVALID_GENE",
                        "message": result.get("error_message"),
                        "details": {"invalid_genes": result.get("invalid_genes", [])}
                    }
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": result.get("error_code", "SIMULATION_ERROR"),
                        "message": result.get("error_message", "Simulation failed")
                    }
                }
            )

    # Build bottleneck list
    bottlenecks = [
        BottleneckInfo(
            reaction_id=b["reaction_id"],
            reaction_name=b["reaction_name"],
            flux=b["flux"],
            subsystem=b["subsystem"]
        )
        for b in result.get("bottlenecks", [])
    ]

    return SimulateResponse(
        status=result["status"],
        growth_rate=result["growth_rate"],
        objective_value=result["objective_value"],
        goebl_tax_applied=result["goebl_tax_applied"],
        proteolytic_burden=result.get("proteolytic_burden"),
        flux_distribution=result["flux_distribution"],
        bottlenecks=bottlenecks,
        knocked_out_genes=result["knocked_out_genes"],
        carbon_source=result["carbon_source"],
        oxygen_constraint=result["oxygen_constraint"],
        model_version=result["model_version"],
        computation_time_ms=result["computation_time_ms"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/options",
    response_model=SimulateOptions,
    summary="Get Simulation Options",
    description="Returns available carbon sources, oxygen constraints, and supported objectives."
)
async def get_options(
    api_key: dict = Depends(get_api_key),
    service = Depends(get_simulation_service)
):
    """Get available simulation options for building dynamic UIs."""
    options = service.get_options()

    return SimulateOptions(
        carbon_sources=options["carbon_sources"],
        oxygen_constraints=options["oxygen_constraints"],
        objectives=options["objectives"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )
