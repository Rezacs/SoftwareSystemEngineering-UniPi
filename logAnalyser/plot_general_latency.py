from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO8601 timestamps, including those ending with 'Z'."""
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def compute_latency_points(data: dict) -> list[tuple[int, float]]:
    """Return (session_count, latency_seconds) for each experiment in the series."""
    points: list[tuple[int, float]] = []

    for experiment in data.get("experiment_series", []):
        session_count = int(experiment["session_count"])
        start_ts = parse_iso_timestamp(experiment["initial_experiment_timestamp"])
        end_ts = parse_iso_timestamp(experiment["milestones"]["last_instance"]["timestamp"])

        latency_seconds = (end_ts - start_ts).total_seconds()
        points.append((session_count, latency_seconds))

    points.sort(key=lambda item: item[0])
    return points


def build_plot(points: list[tuple[int, float]], output_file: Path) -> None:
    sessions = [point[0] for point in points]
    latencies = [point[1] for point in points]

    plt.figure(figsize=(10, 6))
    plt.plot(sessions, latencies, marker="o", linewidth=2)
    plt.title("General Latency by Session Count")
    plt.xlabel("Number of Sessions")
    plt.ylabel("Latency (seconds)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.xticks(sessions)
    plt.tight_layout()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150)
    plt.close()


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    parser = argparse.ArgumentParser(
        description=(
            "Create a latency plot where y is the difference in seconds between "
            "initial_experiment_timestamp and milestones.last_instance.timestamp."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=project_root
        / "Non Elasticity Test - Production Phase"
        / "general_latency.json",
        help="Path to general_latency.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=script_dir / "output" / "general_latency_plot.png",
        help="Path for the output plot image",
    )
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as file:
        data = json.load(file)

    points = compute_latency_points(data)
    if not points:
        raise ValueError("No experiment points found in JSON file.")

    build_plot(points, args.output)
    print(f"Plot created successfully: {args.output}")


if __name__ == "__main__":
    main()