"""
Pydantic models for GL-Number Registry endpoints
"""
from typing import Optional
from pydantic import BaseModel, Field
from .common import Meta


class ReactionInfo(BaseModel):
    """Basic reaction information"""
    gl_number: int = Field(..., description="GLNumber identifier")
    reaction_name: str = Field(..., description="Reaction name")
    subsystem: str = Field(..., description="Metabolic subsystem/pathway")


class SubstrateProductInfo(BaseModel):
    """Metabolite information for substrates/products"""
    met_id: int = Field(..., description="Internal metabolite ID")
    name: str = Field(..., description="Metabolite name")
    compartment: str = Field(..., description="Cellular compartment")


class GeneResponse(BaseModel):
    """Response for gene lookup"""
    gl_number: int = Field(..., description="GLNumber identifier")
    systematic_name: str = Field(..., description="Systematic ORF name (e.g., YDL022W)")
    common_name: str = Field(..., description="Common gene name (e.g., GPD1)")
    ec_codes: list[str] = Field(..., description="EC numbers associated with the gene")
    metabolic_role: str = Field(..., description="Functional role description")
    associated_reactions: list[ReactionInfo] = Field(
        ..., description="Reactions associated with this gene"
    )
    meta: Meta


class ReactionResponse(BaseModel):
    """Response for reaction lookup"""
    gl_number: int = Field(..., description="GLNumber identifier")
    model_reaction_id: str = Field(..., description="COBRA model reaction ID")
    reaction_name: str = Field(..., description="Reaction name")
    subsystem: str = Field(..., description="Metabolic subsystem/pathway")
    gene_reaction_rule: str = Field(..., description="Boolean gene-reaction rule")
    substrates: list[SubstrateProductInfo] = Field(..., description="Substrate metabolites")
    products: list[SubstrateProductInfo] = Field(..., description="Product metabolites")
    meta: Meta


class MetaboliteResponse(BaseModel):
    """Response for metabolite lookup"""
    met_id: int = Field(..., description="Internal metabolite ID")
    model_met_id: str = Field(..., description="COBRA model metabolite ID")
    name: str = Field(..., description="Metabolite name")
    compartment: str = Field(..., description="Cellular compartment")
    reactions_as_substrate: list[ReactionInfo] = Field(
        ..., description="Reactions where this is a substrate"
    )
    reactions_as_product: list[ReactionInfo] = Field(
        ..., description="Reactions where this is a product"
    )
    meta: Meta


class SearchResult(BaseModel):
    """Individual search result"""
    type: str = Field(..., description="Result type (gene, reaction, metabolite)")
    identifier: str = Field(..., description="Primary identifier")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(default=None, description="Additional context")
    gl_number: Optional[int] = Field(default=None, description="GLNumber if applicable")


class SearchResponse(BaseModel):
    """Response for full-text search"""
    query: str = Field(..., description="Original search query")
    results: list[SearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    meta: Meta


class PathwayResponse(BaseModel):
    """Response for pathway/subsystem lookup"""
    subsystem: str = Field(..., description="Pathway/subsystem name")
    reactions: list[ReactionResponse] = Field(
        ..., description="All reactions in this pathway"
    )
    reaction_count: int = Field(..., description="Total reactions in pathway")
    meta: Meta


class RegistryStats(BaseModel):
    """Summary statistics for the registry"""
    total_gl_numbers: int = Field(..., description="Total GLNumber entries")
    total_metabolites: int = Field(..., description="Total metabolites")
    total_reactions: int = Field(..., description="Total reactions")
    total_genes: int = Field(..., description="Total genes in registry")
    model_version: str = Field(..., description="Yeast-GEM version")
    build_date: str = Field(..., description="Registry build date")
    meta: Meta
