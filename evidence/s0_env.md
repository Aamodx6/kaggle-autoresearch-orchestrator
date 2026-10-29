# Stage 0: Environment Verification Evidence

**Generated:** 2026-10-29 18:21:30 (Local Time)  
**Host OS:** Windows (Microsoft Windows 11)  
**Project Workspace:** `c:\Users\aamod\OneDrive\Desktop\Orch`

---

## 1. Python Environment

- **Python Binary:** `.venv/Scripts/python.exe` (CPython 3.12.15)
- **Environment Manager:** `uv` (v0.6+)
- **Core Dependencies:**
  - `kaggle`: 2.2.5 (kagglesdk 0.1.38)
  - `pandas`: 3.1.0
  - `numpy`: 2.5.4
  - `scikit-learn`: 1.9.1
  - `lightgbm`: 4.7.0
  - `pyyaml`: 6.0.3
  - `pytest`: 9.2.0

---

## 2. Kaggle CLI & Authentication

- **Kaggle CLI Version:** `Kaggle CLI 2.2.5`
- **Credential Source:** `~/.kaggle/access_token` (Kaggle OAuth / API Bearer Token, never logged or committed)
- **Live Authentication Verification (`kaggle competitions list --group entered`):**

```text
ref                                                                                          deadline             category                reward  teamCount  userHasEntered  userRank  
-------------------------------------------------------------------------------------------  -------------------  ---------------  -------------  ---------  --------------  --------  
https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3                                 2026-11-02 23:59:00  Featured           850,000 Usd       4968            True      1675  
https://www.kaggle.com/competitions/vesuvius-challenge-surface-detection                     2026-02-27 23:59:00  Research           200,000 Usd       1391            True       636  
https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation            2027-01-20 23:59:00  Featured           150,000 Usd       1539            True      1367  
https://www.kaggle.com/competitions/rsna-knee-abnormality-detection                          2026-10-22 23:59:00  Research            77,000 Usd       6299            True      1464  
https://www.kaggle.com/competitions/biohub-cell-tracking-during-development                  2026-09-29 23:59:00  Research            60,000 Usd       3947            True       725  
https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra                  2026-12-14 23:59:00  Featured            50,000 Usd       4312            True      1175  
https://www.kaggle.com/competitions/squares-in-squares                                       2027-07-18 23:59:00  Playground          50,000 Usd       1200            True       166  
https://www.kaggle.com/competitions/playground-series-s6e2                                   2026-02-28 23:59:00  Playground                Swag       4370            True       413  
https://www.kaggle.com/competitions/playground-series-s5e12                                  2025-12-31 23:59:00  Playground                Swag       4206            True       144  
https://www.kaggle.com/competitions/playground-series-s6e9                                   2026-09-30 23:59:00  Playground                Swag       3575            True       434  
https://www.kaggle.com/competitions/playground-series-s6e8                                   2026-08-31 23:59:00  Playground                Swag       3531            True       199  
https://www.kaggle.com/competitions/playground-series-s6e7                                   2026-07-31 23:59:00  Playground                Swag       3355            True        13  
https://www.kaggle.com/competitions/the-pokemon-company-ptcg-ai-battle-challenge-playground  2027-01-08 23:59:59  Playground                Swag        571            True         0  
https://www.kaggle.com/competitions/autonomous-agent-prediction-beta                         2026-08-06 23:59:00  Playground                Swag        570            True       469  
https://www.kaggle.com/competitions/connectx                                                 2030-01-01 00:00:00  Getting Started      Knowledge        271            True        53  
https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3                2026-04-15 23:59:00  Featured         2,207,152 Usd       4138            True      2994  
https://www.kaggle.com/competitions/hull-tactical-market-prediction                          2026-06-25 23:59:00  Featured           100,000 Usd       3677            True         0  
https://www.kaggle.com/competitions/kaggriculture                                            2026-10-14 23:59:00  Featured            50,000 Usd      10148            True      3075  
```

---

## 3. GPU Hardware & Acceleration

- **GPU:** NVIDIA GeForce RTX 4050 Laptop GPU
- **VRAM Total:** 6141 MiB (6.0 GB)
- **Driver Version:** 617.14
- **CUDA Version:** 13.4
- **Status:** Operational, 0% compute utilization at baseline.

---

## 4. Disk Storage

- **Drive `C:\`:**
  - Used: 152.06 GB
  - Free: 324.77 GB
  - Ample storage for competition datasets, artifacts, and model checkpoints.

---

## 5. Security & Isolation

- `.gitignore` configured to strictly prevent committing credentials (`~/.kaggle`, `access_token`, `kaggle.json`), `.env`, data files, and virtual environments.
- Default execution mode strictly enforces `--dry-run`.
