"""Headless CLI agent shim for offline execution and headless verification."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Headless CLI Coding Agent Shim")
    parser.add_argument("-p", "--prompt", default="", help="Prompt instruction")
    parser.add_argument("--worktree", default="", help="Optional worktree branch")
    args, unknown = parser.parse_known_args()

    prompt_text = args.prompt
    if not prompt_text and not sys.stdin.isatty():
        prompt_text = sys.stdin.read()

    cwd = Path.cwd()
    train_file = cwd / "train.py"

    print(f"[orch.llm_cli] Received headless prompt: {prompt_text[:100]}...")

    if train_file.exists():
        content = train_file.read_text(encoding="utf-8")
        if "ratio_st_hr" not in content:
            new_feature = """    # Autonomous LLM Headless CLI Feature: ST depression / Max HR ratio
    df_train["ratio_st_hr"] = df_train["ST depression"] / (df_train["Max HR"] + 1e-5)
    df_test["ratio_st_hr"] = df_test["ST depression"] / (df_test["Max HR"] + 1e-5)
"""
            target_str = "    # Hypothesis / Feature additions:\n"
            if target_str in content:
                content = content.replace(target_str, target_str + new_feature, 1)
            else:
                content = content.replace(
                    "feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]",
                    new_feature + "\n    feature_cols = [c for c in df_train.columns if c not in [TARGET_COL, ID_COL]]",
                    1,
                )
            train_file.write_text(content, encoding="utf-8")
            print("[orch.llm_cli] Successfully edited train.py with feature ratio_st_hr.")
        else:
            print("[orch.llm_cli] Feature ratio_st_hr already present in train.py.")
    else:
        print(f"[orch.llm_cli] No train.py found in {cwd}.")


if __name__ == "__main__":
    main()
