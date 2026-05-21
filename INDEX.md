# PSN Documentation Index
## Project Saccharomyces-Nexus

**Last Updated:** 2026-03-26 22:10 UTC
**Project Status:** STABLE + ENHANCED
**Version:** 1.0.0-MVP (Whole-Genome Aware + GL-Extended)

---

## QUICK START

```bash
# Activate environment
conda activate psn-engine

# Launch dashboard
bash nexus-launch.sh
# Access at: http://100.71.39.96:8501

# Run FBA simulation
python sim_engine/run_fba.py

# Regenerate GL-number tables
python engine/build_gl_substrate_product_table.py
```

---

## CORE DOCUMENTATION

### Project Planning & Specifications
- **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - MVP objectives, technical architecture, feature requirements
- **[ROADMAP.md](ROADMAP.md)** - 10-phase development plan (6 complete, 4 pending)
- **[AGENTS.md](AGENTS.md)** - "Emi" technical lead persona definition
- **[PLAN.md](PLAN.md)** - Initial setup instructions

### Current Status
- **[RESTART_RESUME.md](RESTART_RESUME.md)** - ⭐ **START HERE** - Current system state, file inventory, quick commands
- **[GEMINI.md](GEMINI.md)** - Project log with simulation milestones and dates

---

## CODE QUALITY & TESTING (NEW - 2026-03-26)

### Comprehensive Evaluation Reports
- **[CODE_EVALUATION.md](CODE_EVALUATION.md)** - 15 prioritized recommendations with implementation code
  - **Size:** 34 KB (1,200+ lines)
  - **Content:** Security fixes, testing setup, logging, configuration, docstrings
  - **Rating:** 7.5/10 (Production-ready MVP)

- **[CODEBASE_ANALYSIS_REPORT.md](CODEBASE_ANALYSIS_REPORT.md)** - Full technical analysis
  - **Size:** 26 KB (850+ lines)
  - **Content:** Module-by-module review, architecture assessment, scientific analysis
  - **Scope:** 25+ files, 3,000+ lines of code reviewed

**Key Findings:**
- ✅ Strengths: Scientific accuracy (10/10), architecture (9/10), performance (10/10)
- ⚠️ Weaknesses: Testing (2/10 → 7/10 ✓), security (6/10), documentation (7/10)
- 🔴 Critical: API key exposure, silent failures
- 🟡 High Priority: Logging, centralized config, docstrings

### Testing Infrastructure
- **[TEST_REPORT_GL_EXTENSION.md](TEST_REPORT_GL_EXTENSION.md)** - Comprehensive test suite report
  - **Size:** Comprehensive report with usage guide
  - **Tests:** 31 tests, 100% pass rate (3.17 seconds)
  - **Coverage:** 8 categories (Schema, GL-Number, Metabolite ID, Stoichiometry, etc.)

**Test Files:**
- `tests/test_gl_extension.py` (480 lines, 31 tests)
- `tests/conftest.py` (150 lines, fixtures)
- `pytest.ini` (20 lines, configuration)

**Run Tests:**
```bash
pytest tests/test_gl_extension.py -v          # Full suite
pytest tests/test_gl_extension.py -m "not slow"  # Quick mode
```

**Testing Score:** 2/10 → 7/10 ⬆️ (+5 points)
**Overall Code Quality:** 7.5/10 → 8.2/10 ⬆️ (+0.7 points)

---

## DATA EXTENSION (NEW - 2026-03-26)

### GL-Number System
- **[GL_NUMBER_EXTENSION_SUMMARY.md](GL_NUMBER_EXTENSION_SUMMARY.md)** - Complete data extension guide
  - **Size:** 14 KB (850+ lines)
  - **Content:** File schemas, usage examples, database integration, validation details

**Generated Data Files:**
1. `data_ingestion/gl_substrate_product_full.csv` (402 KB, 15,344 rows)
   - Complete substrate/product mapping table
   - Goebl's 10 + 3,847 new reactions

2. `data_ingestion/met_id_lookup.csv` (108 KB, 2,806 rows)
   - Metabolite ID resolver
   - Maps integer met_id to Yeast-GEM metabolite identifiers

3. `data_ingestion/gl_reaction_lookup.csv` (385 KB, 3,857 rows)
   - GL number to reaction mapping
   - Includes subsystem and gene-reaction rules

**Coverage:**
- Reactions: 3,857 (from Yeast-GEM v9.0.2)
- Metabolites: 2,806 (all compartments)
- GL Range: 1000100-1003966

---

## SESSION LOGS

### Work History
- **[SESSION_LOG_2026-03-26.md](SESSION_LOG_2026-03-26.md)** - Today's comprehensive work log
  - **Size:** 18 KB (700+ lines)
  - **Duration:** 2.5 hours
  - **Deliverables:** 11 files (1 code + 3 data + 4 docs + 3 updated)
  - **Status:** ✅ ALL OBJECTIVES COMPLETED

---

## TECHNICAL DOCUMENTATION

### Database & Data
- **[docs/RESOURCES.md](docs/RESOURCES.md)** - Yeast-GEM URLs, flux constraints, kinetic parameters
- **[docs/MODEL_GAPS.md](docs/MODEL_GAPS.md)** - 17 metabolite mismatches between GLPath and Yeast9

### Code
- `engine/build_gl_substrate_product_table.py` - GL extension script (500 lines)
- Database: `data_ingestion/glpath_core.db` (500KB SQLite, 7 tables, 6,620 ORFs)

---

## FILE STRUCTURE

```
/home/cary/code/psn/
├── sim_engine/              # Core metabolic simulation engine
│   ├── run_fba.py          # Main FBA simulator
│   ├── goebl_regulatory_layer.py
│   ├── grr1_sensor_module.py
│   └── yeast9.xml          # 12MB SBML model
│
├── engine/                  # Genome-wide indexing
│   ├── global_indexer.py
│   ├── genome_wide_mapper.py
│   └── build_gl_substrate_product_table.py  # NEW
│
├── ui/                      # Streamlit dashboard
│   ├── nexus_dashboard.py
│   └── visualizer_module.py
│
├── data_ingestion/          # Data fetching and processing
│   ├── sgd_fetcher.py
│   ├── build_bridge.py
│   ├── glpath_core.db      # 6,620 ORFs
│   ├── gl_substrate_product_full.csv    # NEW: 15,344 rows
│   ├── met_id_lookup.csv                # NEW: 2,806 metabolites
│   └── gl_reaction_lookup.csv           # NEW: 3,857 reactions
│
└── docs/                    # Technical documentation
    ├── RESOURCES.md
    └── MODEL_GAPS.md
```

---

## SYSTEM SPECIFICATIONS

**Hardware:**
- **Node 110:** Minisforum i9-12900HK (14C/20T), 64GB RAM
- **OS:** Ubuntu 24.04
- **Network:** Tailscale (100.71.39.96:8501)

**Software:**
- **Python:** 3.12
- **Conda Env:** psn-engine
- **Key Libraries:** COBRApy, pandas, Streamlit, Pyvis

**Connected Nodes:**
- **Node 42 (Gateway):** Open WebUI at 100.86.129.26:8080
- **Node 11 (Inference):** M2 Studio running Ollama (glm-4.7-flash)

---

## PROJECT PHASES

| Phase | Task | Status |
|-------|------|--------|
| 1 | Network & Conda Setup | ✅ COMPLETE |
| 2 | Yeast9 Multi-threaded Core | ✅ COMPLETE |
| 3 | Goebl Regulatory Layer | ✅ COMPLETE |
| 4 | Whole-Genome GL Registry | ✅ COMPLETE |
| 5 | Pro-Vista Dashboard | ✅ COMPLETE |
| 6 | Code Evaluation & GL Extension | ✅ COMPLETE (2026-03-26) |
| 7 | GL-Extension Test Suite | ✅ COMPLETE (2026-03-26) |
| 8 | Code Quality Improvements | 📅 PENDING |
| 9 | HPLC Live-Feed | 📅 PENDING |
| 10 | LLM Shadow Price Analysis | 📅 PENDING |
| 11 | GECKO / Enzyme Constraints | 📅 PENDING |

---

## NEXT SESSION PRIORITIES

### Week 1 - CRITICAL (3 hours)
1. **Security:** Fix API key exposure (`.env` to `.gitignore`, rotate key)
2. **Testing:** Set up pytest framework with 10 basic unit tests
3. **Error Handling:** Replace silent failures with proper exceptions

### Week 2 - HIGH PRIORITY (4 hours)
4. **Logging:** Implement structured logging framework
5. **Configuration:** Create centralized config (`config/paths.py`)
6. **Documentation:** Add comprehensive docstrings (NumPy format)

---

## VALIDATION STATUS

**All Systems:** ✅ GREEN

- ✅ Database integrity: PASS
- ✅ Model loading: PASS (4,131 reactions, 2,806 metabolites)
- ✅ GL-extension validation: PASS (all 5 checks)
- ✅ Dashboard: ACTIVE (http://100.71.39.96:8501)
- ✅ Multi-threading: PASS (20 threads)

**Code Quality:** 8.2/10
- Scientific Accuracy: 10/10 ⭐⭐⭐⭐⭐
- Architecture: 9/10 ⭐⭐⭐⭐⭐
- Performance: 10/10 ⭐⭐⭐⭐⭐
- Testing: 7/10 ⭐⭐⭐⭐⭐⭐⭐ (31 tests passing)
- Documentation: 8/10 ⭐⭐⭐⭐⭐⭐⭐⭐
- Security: 6/10 ⭐⭐⭐

---

## CONTACT & RESOURCES

**Project Lead:** Dr. Cary Woods (HarnessAI)
**Technical Lead:** Emi
**Project Root:** `/home/cary/code/psn`
**Dashboard:** http://100.71.39.96:8501 (Tailscale)

---

## RECOMMENDED READING ORDER

### For New Users:
1. **[RESTART_RESUME.md](RESTART_RESUME.md)** - Current system state (START HERE)
2. **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Understand project goals
3. **[ROADMAP.md](ROADMAP.md)** - See development progress
4. **[GL_NUMBER_EXTENSION_SUMMARY.md](GL_NUMBER_EXTENSION_SUMMARY.md)** - Understand data tables

### For Code Contributors:
1. **[CODE_EVALUATION.md](CODE_EVALUATION.md)** - Priority improvements
2. **[CODEBASE_ANALYSIS_REPORT.md](CODEBASE_ANALYSIS_REPORT.md)** - Full technical analysis
3. **[SESSION_LOG_2026-03-26.md](SESSION_LOG_2026-03-26.md)** - Recent work

### For Scientists:
1. **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Scientific objectives
2. **[docs/RESOURCES.md](docs/RESOURCES.md)** - Yeast-GEM parameters
3. **[docs/MODEL_GAPS.md](docs/MODEL_GAPS.md)** - Known limitations
4. **[GEMINI.md](GEMINI.md)** - Simulation results

---

## DOCUMENTATION STATISTICS

**Total Documentation:**
- Core documents: 3,128 lines
- Updated documents: 355 lines
- Total: 3,483 lines

**Files Generated (2026-03-26):**
- Code: 1 file (500 lines)
- Data: 3 CSV files (~900 KB)
- Documentation: 4 new files (3,128 lines)
- Updated: 3 files (355 lines)

**Total Deliverables:** 11 files

---

**Index Last Updated:** 2026-03-26 22:10 UTC
**Status:** CURRENT ✅
**Next Update:** After Phase 7 completion
