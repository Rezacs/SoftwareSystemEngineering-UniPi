"""Interactive upstream simulator that sends batches of prepared sessions via REST."""

import json
from pathlib import Path

import requests

from src import CONFIG_PATH, PREPARED_SESSIONS_ENDPOINT


PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "data" / "input"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
SEND_STATUS_PATH = OUTPUT_DIR / "sent_prepared_sessions_status.json"
BATCH_SIZE = 4


def load_config() -> dict:
    with Path(CONFIG_PATH).open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def load_prepared_sessions() -> list[tuple[str, dict]]:
    json_files = sorted(
        path
        for path in INPUT_DIR.glob("prepared_session*.json")
        if path.name != "prepared_session.json"
    )
    if not json_files:
        raise FileNotFoundError(f"No prepared-session JSON files found in {INPUT_DIR}")

    prepared_sessions = []
    for json_filename in json_files:
        with json_filename.open("r", encoding="utf-8") as file:
            prepared_sessions.append((json_filename.name, json.load(file)))
    return prepared_sessions


def build_target_url(config: dict) -> str:
    return (
        f"http://{config['segregationSystemIpAddress']}:"
        f"{config['segregationSystemPort']}"
        f"{PREPARED_SESSIONS_ENDPOINT}"
    )


def send_prepared_sessions_batch(
    target_url: str,
    prepared_sessions: list[tuple[str, dict]],
    start_index: int,
    batch_size: int = BATCH_SIZE,
) -> tuple[dict, int]:
    total = len(prepared_sessions)
    selected = [
        prepared_sessions[(start_index + offset) % total] for offset in range(batch_size)
    ]

    results = []
    for filename, payload in selected:
        response = requests.post(target_url, json=payload, timeout=5)
        response_text = response.text
        try:
            response_body = response.json()
        except ValueError:
            response_body = response_text

        results.append(
            {
                "file": filename,
                "status_code": response.status_code,
                "ok": response.ok,
                "response": response_body,
            }
        )

    next_index = (start_index + batch_size) % total
    overall_status = {
        "status": "prepared_sessions_batch_sent",
        "target_url": target_url,
        "sent_count": len(results),
        "all_succeeded": all(result["ok"] for result in results),
        "results": results,
    }
    save_json(SEND_STATUS_PATH, overall_status)
    return overall_status, next_index


def run_interactive_sender():
    config = load_config()
    target_url = build_target_url(config)
    prepared_sessions = load_prepared_sessions()
    cursor = 0

    print("=" * 60)
    print("Prepared Sessions Interactive Sender")
    print("=" * 60)
    print(f"Target endpoint: {target_url}")
    print(f"Loaded sessions : {len(prepared_sessions)} files")
    print(f"Batch size      : {BATCH_SIZE}")
    print("Press Enter to send one batch, type 'q' to quit.")
    print("=" * 60)

    while True:
        command = input("> ").strip().lower()
        if command in {"q", "quit", "exit"}:
            print("[PrepSim] Stopped by user.")
            break
        if command != "":
            print("[PrepSim] Unknown command. Press Enter to send, or 'q' to quit.")
            continue

        try:
            status, cursor = send_prepared_sessions_batch(
                target_url=target_url,
                prepared_sessions=prepared_sessions,
                start_index=cursor,
                batch_size=BATCH_SIZE,
            )
        except requests.RequestException as exc:
            print(f"[PrepSim] Send failed: {exc}")
            continue

        print(
            f"[PrepSim] Batch sent: {status['sent_count']} sessions "
            f"({'OK' if status['all_succeeded'] else 'PARTIAL/FAILED'})"
        )
        for result in status["results"]:
            print(
                f"  - {result['file']}: HTTP {result['status_code']} "
                f"{'OK' if result['ok'] else 'FAIL'}"
            )


if __name__ == "__main__":
    run_interactive_sender()
