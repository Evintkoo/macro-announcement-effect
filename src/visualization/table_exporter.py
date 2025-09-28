"""Tabular export helpers replacing legacy chart rendering.

The analysis pipeline previously relied on a plotting-oriented
``PlotGenerator``. The research workflow has shifted to produce only
structured tabular outputs, so this module provides a drop-in
replacement that keeps the public API compatible while persisting
results purely as CSV files.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Optional, Sequence

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class _DirectoryManager:
    base_tables_dir: Path

    def resolve(self, *parts: str) -> Path:
        target = self.base_tables_dir.joinpath(*parts)
        target.mkdir(parents=True, exist_ok=True)
        return target


class PlotGenerator:
    """Backwards compatible name that now only exports tables."""

    def __init__(self, style: Optional[str] = None, figures_dir: Optional[str] = None, tables_dir: str = "results/tables") -> None:
        self.logger = logging.getLogger(f"{__name__}.PlotGenerator")
        self.directories = _DirectoryManager(Path(tables_dir))
        self.directories.base_tables_dir.mkdir(parents=True, exist_ok=True)
        if figures_dir:
            logger.info("Figure directory %s will remain unused; charts are no longer generated.", figures_dir)

    # ------------------------------------------------------------------
    # Public interface (matching the old plotting class)
    # ------------------------------------------------------------------
    def plot_data_overview(self, aligned_data: pd.DataFrame, save_dir: Optional[Path] = None) -> None:
        if aligned_data is None or aligned_data.empty:
            self.logger.warning("No aligned data available for overview export")
            return
        target_dir = self._target(save_dir, "overview")
        self._export_frame(aligned_data, target_dir / "aligned_data.csv")
        try:
            summary = aligned_data.describe(include="all").transpose()
        except ValueError:
            summary = aligned_data.describe().transpose()
        self._export_frame(summary, target_dir / "summary_statistics.csv")

    def plot_event_study_results(self, event_results: Mapping[str, object], save_dir: Optional[Path] = None) -> None:
        if not event_results:
            self.logger.info("No event study results to export")
            return
        base_dir = self._target(save_dir, "event_study")
        self._export_frame(event_results.get("average_abnormal_returns"), base_dir / "average_abnormal_returns.csv")
        self._export_frame(event_results.get("average_cumulative_abnormal_returns"), base_dir / "average_cumulative_abnormal_returns.csv")
        self._export_mapping_of_frames(event_results.get("abnormal_returns"), base_dir / "abnormal_returns")
        self._export_mapping_of_frames(event_results.get("cumulative_abnormal_returns"), base_dir / "cumulative_abnormal_returns")
        self._export_model_parameters(event_results.get("model_parameters"), base_dir / "model_parameters.csv")
        self._export_summary(event_results.get("summary_statistics"), base_dir / "summary_statistics.csv")
        self._export_significance(event_results.get("significance_tests"), base_dir / "significance_tests.csv")

    def plot_regression_results(self, regression_results: Mapping[str, object], save_dir: Optional[Path] = None) -> None:
        if not regression_results:
            self.logger.info("No regression results to export")
            return
        base_dir = self._target(save_dir, "regression")
        self._export_regression_section(regression_results, base_dir)

    def plot_summary_statistics(self, data_dict: Mapping[str, pd.DataFrame], save_dir: Optional[Path] = None) -> None:
        if not data_dict:
            self.logger.info("No datasets supplied for summary export")
            return
        base_dir = self._target(save_dir, "summary")
        for name, frame in data_dict.items():
            if frame is None or frame.empty:
                continue
            self._export_frame(frame, base_dir / f"{name}_raw.csv")
            try:
                stats = frame.describe(include="all").transpose()
            except ValueError:
                stats = frame.describe().transpose()
            self._export_frame(stats, base_dir / f"{name}_summary.csv")

    # ------------------------------------------------------------------
    # Helper routines
    # ------------------------------------------------------------------
    def _target(self, save_dir: Optional[Path], *parts: str) -> Path:
        if save_dir:
            resolved = Path(save_dir)
            resolved.mkdir(parents=True, exist_ok=True)
            return resolved
        return self.directories.resolve(*parts)

    def _export_frame(self, data: object, path: Path) -> None:
        if data is None:
            return
        if isinstance(data, pd.Series):
            data = data.to_frame()
        if isinstance(data, pd.DataFrame):
            if data.empty:
                self.logger.info("Skipping export of empty DataFrame at %s", path)
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            data.to_csv(path)
            self.logger.info("Saved table: %s", path)
            return
        self.logger.debug("Unsupported object for tabular export at %s: %s", path, type(data).__name__)

    def _export_mapping_of_frames(self, mapping: Optional[Mapping[str, object]], target_dir: Path) -> None:
        if not mapping:
            return
        target_dir.mkdir(parents=True, exist_ok=True)
        for key, value in mapping.items():
            self._export_frame(value, target_dir / f"{key}.csv")

    def _export_model_parameters(self, params: Optional[Mapping[str, Mapping[str, float]]], path: Path) -> None:
        if not params:
            return
        df = pd.DataFrame(params).transpose()
        self._export_frame(df, path)

    def _export_summary(self, summary: Optional[Mapping[str, Mapping[str, float]]], path: Path) -> None:
        if not summary:
            return
        df = pd.DataFrame(summary).transpose()
        self._export_frame(df, path)

    def _export_significance(self, tests: Optional[Mapping[str, Mapping[str, MutableMapping[str, object]]]], path: Path) -> None:
        if not tests:
            return
        records = []
        for event_name, asset_tests in tests.items():
            for asset_name, metrics in asset_tests.items():
                flattened = {"event": event_name, "asset": asset_name}
                for key, value in metrics.items():
                    if isinstance(value, Mapping):
                        for inner_key, inner_val in value.items():
                            flattened[f"{key}.{inner_key}"] = inner_val
                    else:
                        flattened[key] = value
                records.append(flattened)
        if records:
            df = pd.DataFrame(records)
            ordered_cols = ["event", "asset"] + [c for c in df.columns if c not in {"event", "asset"}]
            df = df[ordered_cols]
            self._export_frame(df, path)

    def _export_regression_section(self, section: Mapping[str, object], base_dir: Path) -> None:
        for key, value in section.items():
            if isinstance(value, Mapping):
                self._export_regression_section(value, base_dir / key)
            elif isinstance(value, pd.DataFrame):
                self._export_frame(value, base_dir / f"{key}.csv")
            elif hasattr(value, "params") and hasattr(value, "pvalues"):
                df = pd.DataFrame({
                    "parameter": value.params.index,
                    "coef": value.params.values,
                    "p_value": value.pvalues.values,
                })
                if hasattr(value, "bse"):
                    df["std_err"] = value.bse.values
                if hasattr(value, "rsquared"):
                    df.attrs["rsquared"] = getattr(value, "rsquared")
                self._export_frame(df, base_dir / f"{key}_coefficients.csv")
            else:
                self.logger.debug("Unhandled regression artefact for key '%s': %s", key, type(value).__name__)


__all__: Sequence[str] = ("PlotGenerator",)
