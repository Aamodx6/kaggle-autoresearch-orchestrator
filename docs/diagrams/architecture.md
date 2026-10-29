# System Architecture & State Machine Diagrams

This document outlines the end-to-end architecture and operational state flows of the **Kaggle AutoResearch Orchestrator**. Generated under the gstack `/diagram` specialist specifications.

---

## 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend & Developer Layer"]
        UI["React 19 SPA (Tailwind CSS)"]
        CLI["Orchestrator CLI (uv run orch)"]
    end

    subgraph ServerLayer["Backend & Orchestration (FastAPI)"]
        API["FastAPI REST Endpoints (/api/*)"]
        Queue["Execution Queue Manager (Thread-safe)"]
        Worker["Autonomous Task Worker"]
    end

    subgraph ResearchEngine["AutoResearch Core Engine"]
        Discovery["Discovery Service (Kaggle Connector)"]
        Miner["Public Researcher & Notebook Analyzer"]
        Loop["AutoResearch Loop (Iterative Search)"]
        Sandbox["Git Worktree Sandbox (Isolated Experiments)"]
        Validator["Submission Validator (6-Point Gate)"]
        Submitter["Submission Manager (Safety / Quota Guard)"]
    end

    subgraph StorageLayer["Data & Persistence"]
        DB[("SQLite Registry (registry.db)")]
        Workspaces[("Workspace Directories (/workspaces)")]
        ResearchDir[("Research Playbooks (/research)")]
    end

    subgraph External["External Services"]
        Kaggle["Kaggle Platform (CLI / Web SDK)"]
    end

    UI -->|HTTP / JSON| API
    CLI --> Discovery
    CLI --> Loop
    API --> Queue
    Queue --> Worker
    Worker --> Discovery
    Worker --> Miner
    Worker --> Loop
    Worker --> Submitter

    Discovery -->|Query API| Kaggle
    Miner -->|Pull Kernels| Kaggle
    Submitter -->|Safe Dry-Run / Live Submit| Kaggle

    Loop -->|Branch / Commit / Revert| Sandbox
    Loop -->|Validate Output| Validator
    
    Discovery --> DB
    Miner --> DB
    Miner --> ResearchDir
    Loop --> DB
    Loop --> Workspaces
```

---

## 2. AutoResearch Iteration Loop State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> BaselineSetup: Setup Baseline Triggered
    BaselineSetup --> BaselineEvaluated: 5-Fold Stratified CV
    BaselineEvaluated --> HypothesisGeneration: Compute Baseline Score & Noise Floor (σ)
    
    HypothesisGeneration --> CodeModification: Propose Targeted Hypothesis
    CodeModification --> Execution: Mutate train.py in Git Worktree
    
    Execution --> FailedExecution: Exception / Crash
    FailedExecution --> RevertCode: Discard Change
    
    Execution --> EvaluateScore: 5-Fold CV Completed
    EvaluateScore --> StatisticalNoiseGate: Calculate Δ = Score - Baseline
    
    StatisticalNoiseGate --> KeepCandidate: Δ > σ_CV (Statistically Significant)
    StatisticalNoiseGate --> RevertCode: Δ <= σ_CV (Noise Floor Failed)
    
    KeepCandidate --> CommitGit: Commit & Update Verified Checkpoint
    RevertCode --> DiscardGit: git reset --hard HEAD~1
    
    CommitGit --> CheckBudget: Increment Keep Count
    DiscardGit --> CheckBudget: Increment Discard Count
    
    CheckBudget --> HypothesisGeneration: Iterations Remaining
    CheckBudget --> FinalArtifact: Budget Exhausted
    FinalArtifact --> Idle: Artifact Saved in artifacts/
```

---

## 3. Pre-Flight 6-Point Schema Verification Gate

```mermaid
flowchart LR
    Candidate["Candidate CSV"] --> Gate1{"1. File Exists & Non-Empty?"}
    Gate1 -- No --> Fail["Reject Submission (400)"]
    Gate1 -- Yes --> Gate2{"2. Row Count Matches Sample?"}
    Gate2 -- No --> Fail
    Gate2 -- Yes --> Gate3{"3. Exact Column Names & Order?"}
    Gate3 -- No --> Fail
    Gate3 -- Yes --> Gate4{"4. ID Alignment Matches 1:1?"}
    Gate4 -- No --> Fail
    Gate4 -- Yes --> Gate5{"5. Zero NaN / Null / Inf?"}
    Gate5 -- No --> Fail
    Gate5 -- Yes --> Gate6{"6. Values within Valid Range?"}
    Gate6 -- No --> Fail
    Gate6 -- Yes --> DryRun["Generate Dry-Run Command"]
    
    DryRun --> UserApproval{"Explicit Checkbox Approval?"}
    UserApproval -- No --> Hold["Hold (Safe Dry-Run Mode)"]
    UserApproval -- Yes --> LiveSubmit["Execute Live Kaggle CLI Submit"]
```
