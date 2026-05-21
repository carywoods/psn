/execute Initialize Project Saccharomyces-Nexus (PSN) with the following HarnessAI standards:

# 1. Identity & Role Mapping
- Persona: Emi (Technical Lead).
- Technical Guidelines: All other nodes (11, 42, 110) and models (Ollama, GLM-4.7-Flash) are functional assets and compute resources; they are not assigned personas or names.

# 2. Network Topology (Local & Tailscale)
- Execution Node (110): This machine (Minisforum i9-12900HK, 14C/20T, 64GB RAM, Ubuntu 24.04).
- Gateway Node (42): Open WebUI via Tailscale at http://100.86.129.26:8080.
- Inference Node (11): Endeavor (Mac M2 Studio) acting as the Ollama backend.

# 3. File Manifestation (Disk Writes)
1. Create 'AGENTS.md': Define the 'Emi' persona. Map the 'reasoning' target to the Gateway (100.86.129.26:8080). Explicitly state the 'Tools vs. Leads' distinction.
2. Create 'PRODUCT_SPEC.md': Define the PSN MVP—a CPU-optimized metabolic twin using the Yeast9 consensus model.
3. Create 'GEMINI.md': Initialize the project log. Record the hardware specs of the UN1290 and the verified connection to Node 42.
4. Create '.env': 
   OPEN_WEBUI_KEY=sk-f75f1ce1650a42c39db8fc8f232051db
   GATEWAY_URL=http://100.86.129.26:8080

# 4. Research & Integration
- Search for the 'Yeast-GEM' (Yeast9) SBML model file on GitHub.
- Save the download URL and initial flux constraints to 'docs/RESOURCES.md'.
- Create 'sim_engine/verify_pipeline.py' to test the API handshake between the i9 and the Gateway using the requests library and the psn-engine conda environment.

# 5. Final Step
- Output a 'System Ready' confirmation once all files are written to the 'psn/' directory.
