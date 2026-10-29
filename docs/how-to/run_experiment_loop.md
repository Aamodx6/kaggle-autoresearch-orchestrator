# How-To: Configure and Run Custom AutoResearch Loops

This guide explains how to customize search budgets, set cross-validation strategies, configure hardware boundaries, and run autonomous experimentation loops on new or custom competitions.

---

## 1. Setting Up a New Target Competition

To configure a new competition for autonomous research:

1. Add the competition slug to `config.yaml`:
   ```yaml
   competition:
     target: "playground-series-s6e10"
     format: "csv_tabular"
     target_column: "satisfaction"
     id_column: "id"
     metric: "roc_auc"
     direction: "maximize"
   ```

2. Prepare the local workspace:
   ```bash
   uv run python -c "
   from orch.workspace import WorkspaceManager
   from orch.config import load_config
   from orch.connector import KaggleConnector
   from orch.registry import Registry

   cfg = load_config('config.yaml')
   ws = WorkspaceManager('playground-series-s6e10', KaggleConnector(), Registry(cfg.paths.registry_db), cfg)
   ws.download_data()
   ws.inspect_schema()
   "
   ```

---

## 2. Configuring AutoResearch Budget & Noise Thresholds

Edit the `autoresearch` section in `config.yaml`:

```yaml
autoresearch:
  budget:
    max_experiments: 20          # Total candidate hypotheses to evaluate
    timeout_sec: 180             # Maximum wall-clock time per experiment
    patience: 5                  # Early stopping patience if no improvement
  hardware:
    max_workers: 1               # Sequential execution prevents GPU memory thrashing
    gpu_memory_limit_mb: 6144    # 6GB VRAM limit for RTX 4050
  validation:
    folds: 5                     # 5-fold stratified cross-validation
    noise_gate: true             # Strictly enforce Δ > σ_CV
```

---

## 3. Running Background Iterations via the Web UI

1. Open `http://127.0.0.1:8000/`.
2. In the top target switcher, select your competition.
3. Click **Setup Baseline** to establish the 5-fold anchor score.
4. Click **Run Experiments** to queue iterations into the background worker.
5. Navigate to **Execution Queue** to watch real-time stdout logs and GPU utilization.

---

## 4. Customizing Candidate Hypotheses

Hypotheses can be defined programmatically or synthesized automatically by the LLM driver. To customize manual candidate branches in `orch/loop.py`:

```python
HYPOTHESIS_EXPERIMENTS.append({
    "desc": "Add frequency encoding for high-cardinality categorical features",
    "feature_patch": "freq_encoding",
    "params": {"learning_rate": 0.03, "colsample_bytree": 0.8},
})
```

When the loop runs, each hypothesis creates an isolated Git commit. If the validation score beats the noise floor, it is promoted to `workspaces/<slug>/best/train.py`.
