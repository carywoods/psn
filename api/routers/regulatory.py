"""
Regulatory Router - /v1/regulatory endpoints for Goebl Regulatory Analysis
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_api_key
from api.models.regulatory import (
    RegulatoryAnalyzeRequest, RegulatoryAnalyzeResponse,
    RegulatoryCompareRequest, RegulatoryCompareResponse,
    RegulatoryStatus, AffectedReaction, ConditionResult,
    DifferentialResult, MostAffectedReaction
)
from api.models.common import Meta
from api.config import API_VERSION, MODEL_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/regulatory", tags=["Goebl Regulatory Analysis"])

# Service will be injected at startup
_regulatory_service = None


def get_regulatory_service():
    """Dependency to get the regulatory service"""
    if _regulatory_service is None:
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": "Regulatory service not initialized"}}
        )
    return _regulatory_service


def set_regulatory_service(service):
    """Set the regulatory service (called at startup)"""
    global _regulatory_service
    _regulatory_service = service


@router.post(
    "/analyze",
    response_model=RegulatoryAnalyzeResponse,
    summary="Analyze Regulatory State",
    description="Run Goebl regulatory analysis without full FBA simulation."
)
async def analyze_regulatory(
    request: RegulatoryAnalyzeRequest,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_regulatory_service)
):
    """
    Analyze the Goebl regulatory state for a given glucose uptake rate.
    Returns proteolytic burden, regulatory state, and affected reactions.

    This is the premium differentiator - the proprietary regulatory layer
    that no other metabolic simulation API offers.
    """
    logger.info(f"Regulatory analysis: glucose_uptake={request.glucose_uptake_rate}")

    result = service.analyze(
        glucose_uptake_rate=request.glucose_uptake_rate,
        gene_knockouts=request.gene_knockouts
    )

    # Build affected reactions list
    affected_reactions = [
        AffectedReaction(
            reaction_id=r["reaction_id"],
            original_flux_bound=r["original_flux_bound"],
            penalized_flux_bound=r["penalized_flux_bound"],
            penalty_fraction=r["penalty_fraction"]
        )
        for r in result.get("affected_reactions", [])
    ]

    return RegulatoryAnalyzeResponse(
        proteolytic_burden=result["proteolytic_burden"],
        regulatory_state=result["regulatory_state"],
        grr1_sensor_status=result["grr1_sensor_status"],
        scf_complex_activity=result["scf_complex_activity"],
        affected_reactions=affected_reactions,
        maintenance_cost_adjustment=result["maintenance_cost_adjustment"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.post(
    "/compare",
    response_model=RegulatoryCompareResponse,
    summary="Compare Regulatory Conditions",
    description="Compare Goebl regulatory impact across two conditions."
)
async def compare_regulatory(
    request: RegulatoryCompareRequest,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_regulatory_service)
):
    """
    Compare the Goebl regulatory impact between two conditions
    (e.g., high glucose vs. low glucose).
    """
    logger.info(f"Regulatory comparison: {request.condition_a.label} vs {request.condition_b.label}")

    result = service.compare(
        condition_a_label=request.condition_a.label,
        condition_a_glucose=request.condition_a.glucose_uptake_rate,
        condition_b_label=request.condition_b.label,
        condition_b_glucose=request.condition_b.glucose_uptake_rate
    )

    # Build response
    condition_a = ConditionResult(
        label=result["condition_a"]["label"],
        proteolytic_burden=result["condition_a"]["proteolytic_burden"],
        regulatory_state=result["condition_a"]["regulatory_state"]
    )

    condition_b = ConditionResult(
        label=result["condition_b"]["label"],
        proteolytic_burden=result["condition_b"]["proteolytic_burden"],
        regulatory_state=result["condition_b"]["regulatory_state"]
    )

    most_affected = [
        MostAffectedReaction(
            reaction_id=r["reaction_id"],
            flux_change=r["flux_change"],
            subsystem=r["subsystem"]
        )
        for r in result["differential"].get("most_affected_reactions", [])
    ]

    differential = DifferentialResult(
        burden_change=result["differential"]["burden_change"],
        state_transition=result["differential"]["state_transition"],
        most_affected_reactions=most_affected
    )

    return RegulatoryCompareResponse(
        condition_a=condition_a,
        condition_b=condition_b,
        differential=differential,
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/status",
    response_model=RegulatoryStatus,
    summary="Regulatory Layer Status",
    description="Returns current Goebl layer configuration parameters and version info."
)
async def get_status(
    api_key: dict = Depends(get_api_key),
    service = Depends(get_regulatory_service)
):
    """
    Get current Goebl layer configuration parameters, sensor thresholds, and version info.
    """
    result = service.get_status()

    return RegulatoryStatus(
        version=result["version"],
        high_glucose_threshold=result["high_glucose_threshold"],
        low_glucose_threshold=result["low_glucose_threshold"],
        base_ngam=result["base_ngam"],
        penalty_factor=result["penalty_factor"],
        regulatory_map_loaded=result["regulatory_map_loaded"],
        target_reaction_count=result["target_reaction_count"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )
