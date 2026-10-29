"""Submission validator against Kaggle sample_submission schemas."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import numpy as np
import pandas as pd

from orch.logging_util import get_logger

logger = get_logger("orch.validator")


@dataclass
class ValidationResult:
    is_valid: bool
    row_count: int
    column_count: int
    columns: List[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"Validation Status: {status}",
            f"Rows: {self.row_count}, Columns: {self.column_count} ({', '.join(self.columns)})",
        ]
        if self.errors:
            lines.append("Errors:")
            for e in self.errors:
                lines.append(f"  - [ERROR] {e}")
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - [WARN] {w}")
        return "\n".join(lines)


class SubmissionValidator:
    """Validates candidate submission files against competition sample_submission schemas."""

    def __init__(self, sample_path: Path):
        self.sample_path = Path(sample_path)
        if not self.sample_path.is_file():
            raise FileNotFoundError(f"Sample submission file not found: {self.sample_path}")
        self.sample_df = pd.read_csv(self.sample_path)

    def validate(self, candidate_path: Path) -> ValidationResult:
        candidate_path = Path(candidate_path)
        errors: List[str] = []
        warnings: List[str] = []

        if not candidate_path.is_file():
            return ValidationResult(
                is_valid=False,
                row_count=0,
                column_count=0,
                columns=[],
                errors=[f"Candidate file does not exist: {candidate_path}"],
            )

        if candidate_path.stat().st_size == 0:
            return ValidationResult(
                is_valid=False,
                row_count=0,
                column_count=0,
                columns=[],
                errors=["Candidate file is empty (0 bytes)"],
            )

        try:
            cand_df = pd.read_csv(candidate_path)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                row_count=0,
                column_count=0,
                columns=[],
                errors=[f"Failed to parse CSV: {e}"],
            )

        row_count, col_count = cand_df.shape
        columns = list(cand_df.columns)
        expected_cols = list(self.sample_df.columns)

        # 1. Exact Column Names & Order Check
        if columns != expected_cols:
            errors.append(f"Columns mismatch: expected {expected_cols}, got {columns}")

        # 2. Exact Row Count Check
        if len(cand_df) != len(self.sample_df):
            errors.append(f"Row count mismatch: expected {len(self.sample_df)}, got {len(cand_df)}")

        # 3. ID Alignment Check (First Column)
        if len(expected_cols) > 0 and len(columns) > 0 and columns[0] == expected_cols[0]:
            id_col = expected_cols[0]
            if not cand_df[id_col].equals(self.sample_df[id_col]):
                diff_count = (cand_df[id_col] != self.sample_df[id_col]).sum()
                errors.append(f"ID column '{id_col}' values/order do not match sample_submission ({diff_count} discrepancies)")

        # 4. Null / NaN / Inf Check
        nan_counts = cand_df.isna().sum().to_dict()
        for col, count in nan_counts.items():
            if count > 0:
                errors.append(f"Column '{col}' contains {count} NaN/null values")

        for col in cand_df.select_dtypes(include=[np.number]).columns:
            inf_count = np.isinf(cand_df[col]).sum()
            if inf_count > 0:
                errors.append(f"Column '{col}' contains {inf_count} infinite values")

        # 5. Prediction Column Range / Bounds Check
        if len(columns) > 1:
            pred_col = columns[1]
            if pd.api.types.is_numeric_dtype(cand_df[pred_col]):
                val_min = cand_df[pred_col].min()
                val_max = cand_df[pred_col].max()
                # Check for constant predictions
                if val_min == val_max:
                    warnings.append(f"Prediction column '{pred_col}' has constant value: {val_min}")

                # If sample submission has values between 0 and 1, check probability ranges
                sample_pred_col = expected_cols[1] if len(expected_cols) > 1 else None
                if sample_pred_col and pd.api.types.is_numeric_dtype(self.sample_df[sample_pred_col]):
                    sample_max = self.sample_df[sample_pred_col].max()
                    sample_min = self.sample_df[sample_pred_col].min()
                    if 0.0 <= sample_min and sample_max <= 1.0:
                        if val_min < -0.05 or val_max > 1.05:
                            warnings.append(f"Probabilities out of standard [0, 1] range: min={val_min:.4f}, max={val_max:.4f}")

        is_valid = len(errors) == 0
        result = ValidationResult(
            is_valid=is_valid,
            row_count=row_count,
            column_count=col_count,
            columns=columns,
            errors=errors,
            warnings=warnings,
        )

        if is_valid:
            logger.info(f"Submission validation passed for {candidate_path} ({row_count} rows)")
        else:
            logger.error(f"Submission validation failed with {len(errors)} errors")

        return result
