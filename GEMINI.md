# Project Log: Saccharomyces-Nexus (PSN)

## Hardware Specs: Execution Node (110)
- **Model:** Minisforum i9-12900HK (14C/20T)
- **RAM:** 64 GB | **OS:** Ubuntu 24.04
- **Network:** Tailscale IP 100.71.39.96

## Connections
- **Node 42 (Gateway):** http://100.86.129.26:8080
- **Node 11 (Inference):** Endeavor (M2 Studio)

## Simulation Milestones
| Run Date | Scenario | Growth Rate | Key Feature |
| :--- | :--- | :--- | :--- |
| 2026-03-23 | Baseline | 0.8877 | Yeast-GEM v9.0.2 |
| 2026-03-24 | G1_ARREST | 0.8870 | Goebl Regulatory Layer |
| 2026-03-24 | Deep Harvest | 0.8057 | Xylose/Glucose Co-fermentation |
| 2026-03-24 | Purine Bottleneck | 0.0560 | GL 1000109 Constraint |
| 2026-03-24 | Integrated Core | 0.0862 | Array-Ratio Score Adjustments |

## Milestone Updates: 2026-03-26
- **Milestone 4 (Genome Indexing):** COMPLETE
  - 6,620 ORFs mapped to 7-digit GLNumbers via `engine/genome_wide_mapper.py`.
- **Milestone 5 (DataViz Layer):** COMPLETE
  - Pro-Vista Dashboard (Streamlit) active at http://100.71.39.96:8501.
  - Interactive Pyvis force-directed graphs integrated.
  - Light Mode enabled by default.
  - Database Explorer active for all 7 registry tables.
- **Milestone 6 (System Reliability):** COMPLETE
  - Headless Streamlit configuration verified.
  - `nexus-launch.sh` updated with automated flags.

### Milestone 7 (Code Quality & Data Extension): COMPLETE - 2026-03-26
- **Comprehensive Code Evaluation:**
  - Full codebase analysis completed (3,000+ lines reviewed)
  - Overall rating: 7.5/10 (Production-ready MVP)
  - Documents created: `CODE_EVALUATION.md` (15 recommendations) + `CODEBASE_ANALYSIS_REPORT.md`
  - Critical findings: API key security, testing infrastructure, error handling
  - Validation: All core modules analyzed (sim_engine, engine, ui, data_ingestion)

- **GL-Number Extension System:**
  - Extended Goebl's 10 manual purine entries to entire Yeast-GEM v9.0.2
  - Script: `engine/build_gl_substrate_product_table.py` (500 lines)
  - Generated 3 comprehensive lookup tables:
    1. `gl_substrate_product_full.csv` - 15,344 substrate/product mappings
    2. `met_id_lookup.csv` - 2,806 metabolite ID assignments
    3. `gl_reaction_lookup.csv` - 3,857 reaction metadata entries
  - Coverage: GL 1000100-1003966 (3,867 total GL numbers)
  - Execution time: ~2 seconds (model loading + processing)
  - All validation checks passed ✓

- **Data Statistics:**
  - Metabolites indexed: 2,806 (met_id: 100-2905)
  - Reactions processed: 3,857 metabolic + transport reactions
  - Reactions excluded: 274 exchange reactions (boundary conditions)
  - Substrate entries: 7,211 rows
  - Product entries: 8,133 rows
  - Goebl's original entries: Preserved exactly (GL 1000100-1000109, 51 rows)

- **Documentation Updates:**
  - `GL_NUMBER_EXTENSION_SUMMARY.md` - Comprehensive data extension guide
  - `RESTART_RESUME.md` - Updated with current system state
  - `ROADMAP.md` - Updated with milestone 7 completion
  - `SESSION_LOG_2026-03-26.md` - Complete work log

- **System Status:**
  - Code quality: 7.5/10 (scientific accuracy: 10/10, testing: 2/10)
  - All systems: GREEN ✅
  - Database integrity: PASS
  - GL-extension validation: PASS (all checks)
  - Dashboard: Active at http://100.71.39.96:8501

### Milestone 8 (Testing Infrastructure): COMPLETE - 2026-03-26
- **Comprehensive Test Suite Implemented:**
  - 31 tests covering 8 categories (Schema, GL-Number, Metabolite ID, Stoichiometry, Self-Contradiction, Legacy Preservation, Exchange Exclusion, Regression)
  - All tests passed (100% pass rate)
  - Execution time: 3.17 seconds (full suite), 1.04 seconds (excluding slow tests)
  - Test infrastructure: conftest.py (fixtures), pytest.ini (configuration)

- **Test Coverage:**
  - Schema Integrity: 7 tests ✓
  - GL-Number Integrity: 5 tests ✓
  - Metabolite ID Integrity: 4 tests ✓
  - Stoichiometric Consistency: 2 tests ✓ (validates against Yeast-GEM model)
  - No Self-Contradiction: 1 test ✓
  - Goebl Legacy Preservation: 3 tests ✓
  - Exchange Reaction Exclusion: 2 tests ✓
  - Regression Snapshot: 7 tests ✓

- **Data Validated:**
  - gl_substrate_product_full.csv - 15,344 rows fully validated
  - met_id_lookup.csv - 2,806 metabolites fully validated
  - gl_reaction_lookup.csv - 3,857 reactions fully validated
  - Stoichiometry verified for 50 random reactions (seed=42)

- **Testing Score Improvement:**
  - Before: 2/10 (ad-hoc testing only)
  - After: 7/10 (comprehensive data integrity validation)
  - Overall Code Quality: 7.5/10 → 8.2/10 (estimated)

- **Documentation:**
  - TEST_REPORT_GL_EXTENSION.md - Complete test report with usage guide
  - Tests can be run with: `pytest tests/test_gl_extension.py -v`
  - Quick tests (skip model loading): `pytest -m "not slow"`

- **Regression Protection:**
  - Snapshot tests prevent accidental data changes
  - Will fail if build script is rerun with different model
  - Forces conscious review of any data regeneration


### GLPath Simulation Run (PURINE_BOTTLENECK): 2026-05-21 10:23:05
- **Scenario:** PURINE_BOTTLENECK
- **Target:** GL 1000109 (IMP Step)
- **Growth Rate:** 0.056004
- **Hardware Utilization:** 20 threads (i9-12900HK)
