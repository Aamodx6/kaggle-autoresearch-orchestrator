# Prior Art & Architecture Reuse Analysis

**Target:** Kaggle AutoResearch Orchestrator (`orch`)  
**Context:** Design of the autonomous LLM Driver layer (built before Stage S3 research & Stage S4 autoresearch loop).

---

## 1. Analyzed Frameworks & Prior Art

We audited three foundational frameworks in autonomous competitive data science:
1. **microsoft/RD-Agent** (Kaggle Scenario)
2. **openai/mle-bench** (Offline Grading & Sandbox Hygiene)
3. **AIDE (AI Data Engineer)** (Iterative Tree Search & Keep/Revert Optimization)

---

## 2. Adoption vs. Skip Matrix

| Framework | Core Concept | Adopted Components | Skipped Components | Rationale / Architectural Fit |
|---|---|---|---|---|
| **microsoft/RD-Agent** | Multi-role competitive R&D loop | • Explicit role separation: `proposer` (hypotheses), `editor` (code mutation), `reviewer` (leakage check), and `researcher` (notebook synthesis).<br>• Structured hypothesis formulation with explicit rationale before editing. | • Heavy DAG workflow orchestrator.<br>• Complex multi-agent communication buses.<br>• Global code regeneration. | Karpathy's autoresearch paradigm requires simplicity: a single mutable script (`train.py`) and a fixed evaluation contract (`prepare.py`). Lightweight roles avoid multi-agent orchestration thrashing. |
| **openai/mle-bench** | Offline grading & competition hygiene | • Strict pre-flight submission validation against `sample_submission.csv` (exact rows, IDs, columns, null/inf checks, range sanity).<br>• Hermetic data boundaries (prompt hygiene: never send raw labels or test targets).<br>• Hard daily budget & quota gating. | • Heavy Docker-in-Docker container runtime.<br>• Multi-node cluster grading. | Git worktree sandboxing and filesystem read-only permissions provide instant, low-overhead isolation without requiring Docker daemon on the local workstation. |
| **AIDE** | Solution space search & keep/revert | • Strict keep/revert cycle: execute under timeout, compare against best metric, keep on verified gain, discard on regression or crash.<br>• Error feedback forwarding: runtime tracebacks routed back to proposer/editor.<br>• Standardized machine-readable stdout logging (`CV_MEAN=`, `CV_STD=`, `STATUS=`). | • Monte Carlo Tree Search (MCTS) branch exploration with multiple simultaneous speculative branches. | A linear keep/revert chain with a statistical noise floor gate ($\Delta > \sigma_{\text{CV}}$) prevents leaderboard overfitting and maintains a clean git history. |

---

## 3. Concrete Design Decisions for `llm/driver.py`

1. **Role Specialization:**
   - `researcher`: Mined notebook parsing and summary extraction.
   - `proposer`: Hypothesis generation based on metric progress and backlog.
   - `editor`: Mutates exclusively `train.py` within an isolated git worktree sandbox.
   - `reviewer`: Audits diffs for data leakage, synthetic lookahead, target column corruption, or prohibited modifications to `prepare.py`.

2. **Backend Diversity & Fallback Chains:**
   - Primary: `headless_cli` (`claude -p`, `freebuff`, `gemini -p`) in worktree capturing git diffs.
   - Secondary / Summarization: `openai_compat` (`gemini_api`, `groq`, `openrouter_free`) for JSON/text generation.
   - Testing & CI: `mock` backend providing deterministic canned diffs.
   - Per-role fallback chains (`chain: [backend_1, backend_2, ...]`) with automatic escalation on 429 rate limits, network timeouts, or process crashes.

3. **Prompt Hygiene & Compliance:**
   - Whitelist: code diffs, `results.tsv` summary lines, metric values, feature schemas, summary statistics, error tracebacks.
   - Blacklist: raw dataset rows, label vectors, API credentials, bearer tokens.
   - TOS safety: no unauthorized proxies; any third-party proxy backend requires explicit opt-in in `config.yaml` with a loud startup warning.
