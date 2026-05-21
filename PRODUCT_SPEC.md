# Product Specification: Saccharomyces-Nexus (PSN)

## Project Goal
Develop a CPU-optimized metabolic twin using the Yeast9 (Yeast-GEM) consensus model.

## MVP Objectives
- Build a Python-based metabolic simulator using COBRApy.
- Integrate the Yeast9 model from official sources.
- Provide a CLI interface for flux balance analysis (FBA) simulations.
- Ensure the simulation engine can run efficiently on Execution Node (110).

----added later 

# PRODUCT_SPEC: Saccharomyces-Nexus (PSN)
**Version:** 1.0.0-MVP
**Lead:** Emi (Technical Lead)
**Owner:** Dr. Cary Woods (HarnessAI)

## 1. Executive Summary
PSN is a high-performance Digital Twin of *Saccharomyces cerevisiae* metabolism. It leverages a distributed architecture: Node 110 (Intel i9) for deterministic metabolic math and Node 11 (M2 Studio) for stochastic biological reasoning.

## 2. Technical Architecture
- **Execution Engine (110):** Ubuntu 24.04, i9-12900HK (20 Threads), 64GB RAM.
- **Inference Gateway (42):** Open WebUI via Tailscale (100.86.129.26:8080).
- **Reasoning Layer (11):** Endeavor (M2 Studio) via Ollama.
- **Base Model:** Yeast-GEM 9.x (Yeast9) SBML.

## 3. Core Feature Requirements (MVP)
### A. Metabolic Engine
- **Multi-Threaded FBA:** Optimization of genome-scale models using all 20 threads.
- **Enzyme Constraints (GECKO):** Integrating protein abundance data to bound flux.
- **Context-Specific Models:** Implementation of GIMME/iMAT for transcriptomics integration.

### B. Agentic Reasoning
- **Bottleneck Identification:** Automated shadow price analysis interpreted by LLM.
- **In-silico Knockout Screen:** Agent-led OptKnock simulations for yield optimization.
- **Natural Language Querying:** Ability to ask biological "What-If" questions via Node 42.

### C. Industrial Outputs
- **Production Envelopes:** Biomass vs. Product yield tradeoff curves.
- **Metabolic Burden:** Quantifying the cost of heterologous pathway expression.
- **SGD Live-Sync:** Real-time updates of GPR (Gene-Protein-Reaction) rules.
