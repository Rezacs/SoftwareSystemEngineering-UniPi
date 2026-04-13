from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def find_testing_log(logs_dir: Path) -> Path:
    """
    Search the logs directory for:
    - testing_log_development.csv
    - testing_log_production.csv

    Returns the first match found.
    """
    preferred_names = [
        "testing_log_development.csv",
        "testing_log_production.csv",
    ]

    for name in preferred_names:
        candidate = logs_dir / name
        if candidate.exists():
            return candidate

    matches = sorted(logs_dir.glob("testing_log_*.csv"))
    if matches:
        return matches[0]

    raise FileNotFoundError(
        f"No testing log file found in: {logs_dir}\n"
        f"Expected one of: {preferred_names} or any file matching testing_log_*.csv"
    )


def validate_columns(df: pd.DataFrame) -> None:
    required_columns = {"system", "process", "latency_s", "outcome"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}. "
            f"Found columns: {list(df.columns)}"
        )


def build_summary(df: pd.DataFrame, source_file: Path) -> dict[str, Any]:
    """
    Build a JSON-friendly summary:
    - unique process names
    - occurrence count for each process
    - average latency for each process
    - unique outcomes for each process with occurrence count
    """
    df = df.copy()
    df["latency_s"] = pd.to_numeric(df["latency_s"], errors="coerce")

    summary: dict[str, Any] = {
        "source_file": str(source_file),
        "systems_found": sorted(df["system"].dropna().astype(str).unique().tolist()),
        "total_rows": int(len(df)),
        "unique_processes_count": int(df["process"].nunique(dropna=True)),
        "processes": [],
    }

    grouped = df.groupby("process", dropna=True, sort=True)

    for process_name, group in grouped:
        outcome_counts = (
            group["outcome"]
            .fillna("NULL")
            .astype(str)
            .value_counts()
            .sort_index()
            .to_dict()
        )

        process_info = {
            "process": str(process_name),
            "occurrences": int(len(group)),
            "average_latency_s": round(float(group["latency_s"].mean()), 6)
            if group["latency_s"].notna().any()
            else None,
            "outcomes": [
                {
                    "outcome": outcome,
                    "occurrences": int(count),
                }
                for outcome, count in outcome_counts.items()
            ],
        }

        summary["processes"].append(process_info)

    return summary


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    logs_dir = project_root / "logs"
    output_dir = script_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = find_testing_log(logs_dir)
    df = pd.read_csv(log_file)
    validate_columns(df)

    summary = build_summary(df, log_file)

    output_path = output_dir / f"{log_file.stem}_analysis.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    print(f"Input file:  {log_file}")
    print(f"Output file: {output_path}")
    print("Analysis completed successfully.")


if __name__ == "__main__":
    main()