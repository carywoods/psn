# PSN Runbook

Last validated: 2026-05-21
Node: 110
Project root: `/home/cary/code/psn`
Conda environment: `psn-engine`

## Start the environment

```bash
cd ~/code/psn
conda activate psn-engine
```

## Launch the dashboard

Preferred command:

```bash
source nexus-launch.sh
nexus-ui
```

Direct command:

```bash
streamlit run ui/nexus_dashboard.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Local access:

```text
http://localhost:8501
```

## Run the core FBA simulation

Run this from the repository root:

```bash
python -m sim_engine.run_fba
```

Do not use this as the preferred command:

```bash
python sim_engine/run_fba.py
```

Direct file execution can fail because Python may not treat the project root as the package context.

## Validated output from 2026-05-21

```text
Loading model: sim_engine/yeast9.xml...
Scenario: Simulating Purine Bottleneck (GL 1000109)...
Constraint applied to r_0570 (inosine monophosphate cyclohydrolase): bounds set to 0.01
Constraint applied to r_0912 (phosphoribosylaminoimidazolecarboxamide formyltransferase): bounds set to 0.01
Running 20-threaded Optimization...
--- PURINE_BOTTLENECK Results ---
Growth Rate: 0.0560
Logged results to GEMINI.md
```

## Regenerate GL-number tables

```bash
python engine/build_gl_substrate_product_table.py
```

## Query the local database

```bash
sqlite3 data_ingestion/glpath_core.db
```
