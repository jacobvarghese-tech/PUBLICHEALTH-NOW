


from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

VOTE_STEP = 0.01
ZERO_PERCENTILE = 99


class OptimizedRankModel:



    def __init__(
        self,
        primary_model,
        primary_columns: list[str],
        secondary_model,
        secondary_columns: list[str],
        fit_years: list[int],
        n_estimators: int,
        max_depth: int,
        min_samples_leaf: int,
        class_weight: str,
        clean_per_fraud: int,
        fraud_rows: int,
        clean_rows: int,
    ) -> None:
        self.primary_model = primary_model
        self.primary_columns = list(primary_columns)
        self.secondary_model = secondary_model
        self.secondary_columns = list(secondary_columns)
        self.columns = list(secondary_columns)
        self.model = secondary_model
        self.fit_years = list(fit_years)
        self.n_estimators = int(n_estimators)
        self.max_depth = int(max_depth)
        self.min_samples_leaf = int(min_samples_leaf)
        self.class_weight = class_weight
        self.clean_per_fraud = int(clean_per_fraud)
        self.fraud_rows = int(fraud_rows)
        self.clean_rows = int(clean_rows)
        self.vote_step = VOTE_STEP
        self.zero_percentile = ZERO_PERCENTILE
        self.primary_model_name = "embedded page forest"

    def parameter_summary(self) -> str:
        years = ",".join(str(year) for year in self.fit_years)
        primary_trees = getattr(self.primary_model, "n_estimators", None)
        return (
            f"type=OptimizedRankModel "
            f"primary=RandomForestClassifier n_estimators={primary_trees} "
            f"secondary=RandomForestClassifier "
            f"n_estimators={self.n_estimators} max_depth={self.max_depth} "
            f"min_samples_leaf={self.min_samples_leaf} "
            f"class_weight={self.class_weight} random_state=0 n_jobs=2 "
            f"clean_per_fraud={self.clean_per_fraud} fit_years={years} "
            f"fraud_rows={self.fraud_rows} clean_rows={self.clean_rows} "
            f"rank=zero_tie_break vote_step={self.vote_step} "
            f"zero_percentile={self.zero_percentile}"
        )

    def score_frame(self, frame: pd.DataFrame, chunk: int = 40_000) -> np.ndarray:
        
        from scripts.paper_forest import score_year

        primary = score_year(self.primary_model, self.primary_columns, frame, chunk=chunk)
        secondary = score_year(
            self.secondary_model, self.secondary_columns, frame, chunk=chunk
        )
        return self.rank(primary, secondary)

    def score_year(self, path: Path, chunk: int = 40_000) -> np.ndarray:
        
        from scripts.paper_forest import load_year

        frame = load_year(Path(path))
        return self.score_frame(frame, chunk=chunk)

    def rank(self, primary_scores: np.ndarray, secondary_scores: np.ndarray) -> np.ndarray:
        return zero_tie_break(
            primary_scores,
            secondary_scores,
            vote_step=self.vote_step,
            percentile=self.zero_percentile,
        )


def zero_tie_break(
    primary: np.ndarray,
    secondary: np.ndarray,
    vote_step: float = VOTE_STEP,
    percentile: float = ZERO_PERCENTILE,
) -> np.ndarray:


    primary = np.asarray(primary, dtype=float)
    secondary = np.asarray(secondary, dtype=float)
    if len(primary) != len(secondary):
        raise ValueError("primary and secondary scores must have the same length")
    out = primary.copy()
    zeros = primary == 0
    if not np.any(zeros):
        return out
    zero_scores = secondary[zeros]
    if len(np.unique(np.round(zero_scores, 6))) < 2:
        return out
    cutoff = float(np.percentile(zero_scores, percentile))
    promote = zeros & (secondary >= cutoff)
    if not np.any(promote):
        return out
    trial = primary.copy()
    trial[promote] = vote_step

    if float(np.percentile(trial, 95)) > 0.0:
        return out
    out[promote] = vote_step
    return out
