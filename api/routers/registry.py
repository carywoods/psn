"""
Registry Router - /v1/registry endpoints for GL-Number lookups
"""
import logging
from typing import Optional
from urllib.parse import unquote
from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import get_api_key
from api.models.registry import (
    GeneResponse, ReactionResponse, MetaboliteResponse,
    SearchResponse, SearchResult, PathwayResponse, RegistryStats,
    ReactionInfo, SubstrateProductInfo
)
from api.models.common import Meta
from api.config import API_VERSION, MODEL_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/registry", tags=["GL-Number Registry"])

# Service will be injected at startup
_registry_service = None


def get_registry_service():
    """Dependency to get the registry service"""
    if _registry_service is None:
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": "Registry service not initialized"}}
        )
    return _registry_service


def set_registry_service(service):
    """Set the registry service (called at startup)"""
    global _registry_service
    _registry_service = service


@router.get(
    "/gene/{identifier}",
    response_model=GeneResponse,
    summary="Look Up Gene",
    description="Look up a gene by systematic ORF name (e.g., YDL022W) or common name (e.g., GPD1)."
)
async def lookup_gene(
    identifier: str,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_registry_service)
):
    """
    Look up a gene and return its GLNumber, EC codes, metabolic role, and associated reactions.
    """
    logger.info(f"Gene lookup: {identifier}")

    result = service.lookup_gene(identifier)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "GENE_NOT_FOUND",
                    "message": f"Gene '{identifier}' not found in registry"
                }
            }
        )

    # Build response
    associated_reactions = [
        ReactionInfo(
            gl_number=r["gl_number"],
            reaction_name=r["reaction_name"],
            subsystem=r["subsystem"]
        )
        for r in result.get("associated_reactions", [])
    ]

    return GeneResponse(
        gl_number=result["gl_number"],
        systematic_name=result["systematic_name"],
        common_name=result["common_name"],
        ec_codes=result["ec_codes"],
        metabolic_role=result["metabolic_role"],
        associated_reactions=associated_reactions,
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/reaction/{gl_number}",
    response_model=ReactionResponse,
    summary="Look Up Reaction",
    description="Look up a reaction by GLNumber. Returns substrates, products, and gene associations."
)
async def lookup_reaction(
    gl_number: int,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_registry_service)
):
    """
    Look up a reaction by GLNumber.
    """
    logger.info(f"Reaction lookup: GL {gl_number}")

    result = service.lookup_reaction(gl_number)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "REACTION_NOT_FOUND",
                    "message": f"Reaction with GLNumber {gl_number} not found"
                }
            }
        )

    # Build response
    substrates = [
        SubstrateProductInfo(
            met_id=s["met_id"],
            name=s["name"],
            compartment=s["compartment"]
        )
        for s in result.get("substrates", [])
    ]

    products = [
        SubstrateProductInfo(
            met_id=p["met_id"],
            name=p["name"],
            compartment=p["compartment"]
        )
        for p in result.get("products", [])
    ]

    return ReactionResponse(
        gl_number=result["gl_number"],
        model_reaction_id=result["model_reaction_id"],
        reaction_name=result["reaction_name"],
        subsystem=result["subsystem"],
        gene_reaction_rule=result["gene_reaction_rule"],
        substrates=substrates,
        products=products,
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/metabolite/{met_id}",
    response_model=MetaboliteResponse,
    summary="Look Up Metabolite",
    description="Look up a metabolite by met_id. Returns reactions it participates in."
)
async def lookup_metabolite(
    met_id: int,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_registry_service)
):
    """
    Look up a metabolite by its internal met_id.
    """
    logger.info(f"Metabolite lookup: {met_id}")

    result = service.lookup_metabolite(met_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "METABOLITE_NOT_FOUND",
                    "message": f"Metabolite with met_id {met_id} not found"
                }
            }
        )

    # Build response
    reactions_as_substrate = [
        ReactionInfo(
            gl_number=r["gl_number"],
            reaction_name=r["reaction_name"],
            subsystem=r["subsystem"]
        )
        for r in result.get("reactions_as_substrate", [])
    ]

    reactions_as_product = [
        ReactionInfo(
            gl_number=r["gl_number"],
            reaction_name=r["reaction_name"],
            subsystem=r["subsystem"]
        )
        for r in result.get("reactions_as_product", [])
    ]

    return MetaboliteResponse(
        met_id=result["met_id"],
        model_met_id=result["model_met_id"],
        name=result["name"],
        compartment=result["compartment"],
        reactions_as_substrate=reactions_as_substrate,
        reactions_as_product=reactions_as_product,
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Full-Text Search",
    description="Search across gene names, reaction names, metabolite names, and subsystems."
)
async def search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    api_key: dict = Depends(get_api_key),
    service = Depends(get_registry_service)
):
    """
    Full-text search across the registry. Returns top 20 results ranked by relevance.
    """
    logger.info(f"Registry search: '{q}'")

    result = service.search(q)

    # Build response
    search_results = [
        SearchResult(
            type=r["type"],
            identifier=r["identifier"],
            name=r["name"],
            description=r.get("description"),
            gl_number=r.get("gl_number")
        )
        for r in result.get("results", [])
    ]

    return SearchResponse(
        query=result["query"],
        results=search_results,
        total_count=result["total_count"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/pathway/{subsystem:path}",
    response_model=PathwayResponse,
    summary="Get Pathway Reactions",
    description="Returns all reactions in a given subsystem/pathway with their GLNumbers."
)
async def get_pathway(
    subsystem: str,
    api_key: dict = Depends(get_api_key),
    service = Depends(get_registry_service)
):
    """
    Get all reactions in a given subsystem/pathway.
    The subsystem parameter should be URL-encoded if it contains special characters.
    """
    # URL decode the subsystem
    subsystem_decoded = unquote(subsystem)
    logger.info(f"Pathway lookup: {subsystem_decoded}")

    result = service.get_pathway(subsystem_decoded)

    if not result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "PATHWAY_NOT_FOUND",
                    "message": f"Pathway '{subsystem_decoded}' not found"
                }
            }
        )

    # Build response - convert reaction dicts to ReactionResponse models
    reactions = []
    for r in result.get("reactions", []):
        substrates = [
            SubstrateProductInfo(
                met_id=s["met_id"],
                name=s["name"],
                compartment=s["compartment"]
            )
            for s in r.get("substrates", [])
        ]
        products = [
            SubstrateProductInfo(
                met_id=p["met_id"],
                name=p["name"],
                compartment=p["compartment"]
            )
            for p in r.get("products", [])
        ]
        reactions.append(
            ReactionResponse(
                gl_number=r["gl_number"],
                model_reaction_id=r["model_reaction_id"],
                reaction_name=r["reaction_name"],
                subsystem=r["subsystem"],
                gene_reaction_rule=r["gene_reaction_rule"],
                substrates=substrates,
                products=products,
                meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
            )
        )

    return PathwayResponse(
        subsystem=result["subsystem"],
        reactions=reactions,
        reaction_count=result["reaction_count"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )


@router.get(
    "/stats",
    response_model=RegistryStats,
    summary="Registry Statistics",
    description="Returns summary statistics: total GLNumbers, metabolites, reactions, model version."
)
async def get_stats(
    api_key: dict = Depends(get_api_key),
    service = Depends(get_registry_service)
):
    """
    Get registry summary statistics.
    """
    result = service.get_stats()

    return RegistryStats(
        total_gl_numbers=result["total_gl_numbers"],
        total_metabolites=result["total_metabolites"],
        total_reactions=result["total_reactions"],
        total_genes=result["total_genes"],
        model_version=result["model_version"],
        build_date=result["build_date"],
        meta=Meta(api_version=API_VERSION, model_version=MODEL_VERSION)
    )
