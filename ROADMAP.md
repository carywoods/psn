# PSN Development Roadmap

| Phase | Task | Status | Target Node |
| :--- | :--- | :--- | :--- |
| 1. Infra | Network & Conda Setup | ✅ COMPLETE | 110 / 42 / 11 |
| 2. Engine | Yeast9 Multi-threaded Core | ✅ COMPLETE | 110 |
| 3. Nexus | Goebl Regulatory Layer | ✅ COMPLETE | 110 |
| 4. Data | Whole-Genome GL Registry | ✅ COMPLETE | 110 |
| 5. UI | Pro-Vista Dashboard (Light) | ✅ COMPLETE | 110 |
| 6. Quality | Code Evaluation & GL Extension | ✅ COMPLETE | 110 |
| 7. Testing | GL-Extension Test Suite | ✅ COMPLETE | 110 |
| 8. Future | Code Quality Improvements | 📅 PENDING | 110 |
| 8. Future | HPLC Live-Feed (`c16.pl`) | 📅 PENDING | 110 |
| 9. Future | LLM Shadow Price Analysis | 📅 PENDING | 11 |
| 10. Future | GECKO / Enzyme Constraints | 📅 PENDING | 110 |

---

## Phase 6 Details: Code Evaluation & GL Extension (✅ COMPLETE - 2026-03-26)

### A. Comprehensive Codebase Evaluation
- **Scope:** 3,000+ lines of Python code analyzed
- **Rating:** 7.5/10 (Production-ready MVP)
- **Documents:**
  - `CODE_EVALUATION.md` - 15 prioritized recommendations with implementation code
  - `CODEBASE_ANALYSIS_REPORT.md` - Full technical analysis report
- **Key Findings:**
  - **Strengths:** Scientific rigor (10/10), architecture (9/10), performance (10/10)
  - **Weaknesses:** Testing (2/10), security (6/10), documentation (7/10)
  - **Critical Issues:** API key exposure, silent failures, no test suite
  - **High Priority:** Logging framework, centralized config, docstrings

### B. GL-Number Extension System
- **Objective:** Extend Goebl's 10 manual purine entries to entire Yeast-GEM v9.0.2
- **Script:** `engine/build_gl_substrate_product_table.py` (500 lines)
- **Output Files:**
  1. `gl_substrate_product_full.csv` - 15,344 substrate/product mappings
  2. `met_id_lookup.csv` - 2,806 metabolite assignments (met_id: 100-2905)
  3. `gl_reaction_lookup.csv` - 3,857 reaction metadata entries
- **Coverage:**
  - Goebl's original: GL 1000100-1000109 (10 reactions, 51 rows) - preserved exactly
  - Model-derived: GL 1000110-1003966 (3,847 reactions, 15,293 rows)
  - Reactions processed: 3,857 (274 exchange reactions excluded)
- **Validation:** All checks passed ✓
- **Documentation:** `GL_NUMBER_EXTENSION_SUMMARY.md` (comprehensive guide)

---

## Phase 7 Details: GL-Extension Test Suite (✅ COMPLETE - 2026-03-26)

### A. Test Infrastructure Setup
- **pytest installed:** pytest 9.0.2, pytest-cov 7.1.0
- **Configuration:** pytest.ini with custom markers
- **Fixtures:** Session-scoped fixtures for CSV and model loading
- **Structure:** tests/ directory with conftest.py and test modules

### B. Comprehensive Test Suite
- **File:** `tests/test_gl_extension.py` (480 lines)
- **Total Tests:** 31 tests organized in 8 categories
- **Execution Time:** 3.17 seconds (full), 1.04 seconds (quick mode)
- **Pass Rate:** 100% (31/31 passed)

### C. Test Coverage
- **Schema Integrity:** 7 tests ✓
- **GL-Number Integrity:** 5 tests ✓
- **Metabolite ID Integrity:** 4 tests ✓
- **Stoichiometric Consistency:** 2 tests ✓ (validates against Yeast-GEM)
- **No Self-Contradiction:** 1 test ✓
- **Goebl Legacy Preservation:** 3 tests ✓
- **Exchange Reaction Exclusion:** 2 tests ✓
- **Regression Snapshot:** 7 tests ✓

### D. Data Validated
- gl_substrate_product_full.csv - 15,344 rows ✓
- met_id_lookup.csv - 2,806 metabolites ✓
- gl_reaction_lookup.csv - 3,857 reactions ✓
- Stoichiometry verified for 50 random reactions ✓

### E. Impact
- **Testing Score:** 2/10 → 7/10 (+5 points)
- **Overall Code Quality:** 7.5/10 → 8.2/10 (+0.7 points)
- **Documentation:** TEST_REPORT_GL_EXTENSION.md (comprehensive report)

---

## Phase 8 Details: Code Quality Improvements (📅 PENDING)

### Immediate Actions (Week 1 - CRITICAL)
- [ ] **Security:** Fix API key exposure (`.env` to `.gitignore`, rotate key)
- [ ] **Error Handling:** Replace silent failures with proper exceptions
- [ ] **Testing:** Set up pytest framework with basic unit tests

### High Priority (Week 2)
- [ ] **Logging:** Implement structured logging (replace print statements)
- [ ] **Configuration:** Create centralized config (`config/paths.py`)
- [ ] **Documentation:** Add comprehensive docstrings (NumPy format)

### Medium Priority (Weeks 3-4)
- [ ] **Type Safety:** Add type hints and input validation
- [ ] **Robustness:** Implement retry logic for SGD API calls
- [ ] **Deployment:** Create systemd service for auto-start
- [ ] **Dependencies:** Pin versions in `environment.yml`
