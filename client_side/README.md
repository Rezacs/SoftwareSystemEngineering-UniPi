# Client-Side System

## 1. Setup & Configuration
The system behavior is governed by a central configuration file. Ensure this file exists at the following path relative to the project root.

- File path: `../config/clientsideConfig.json`
- Contents: Define network ports for the Ingestion and Evaluation systems, local listener settings, and the relative paths for your CSV datasets.

## 2. Launching the System
Open your terminal in the project directory and execute:

```bash
python client_system.py
```

## 3. Initialization & Logging
Upon launch, the system automatically performs the following:

- Log registration: Appends a "launch" event with a high-precision timestamp to `../logs/clientsideLogs.json`.
- API startup: Spins up a background Flask server to listen for incoming labels from the Evaluation system.
- User input: Prompts you to select the operational mode (Phase) and the volume of data to be streamed.

## 4. Phase Selection
Choose the data source context for the current session:

- Phase 0 (Development)
  - Source: Merges three separate files (`raws_football_db.csv`, `raws_medical_db.csv`, `raws_social_db.csv`).
  - Logic: Standardizes different ID formats (for example, `id_player` to `player_id`) and shuffles the combined pool.
- Phase 1 (Production)
  - Source: Loads the `unified_players_db_missing.csv` dataset.
  - Logic: Shuffles the dataset for sequential, randomized delivery.

## 5. The Execution Pipeline

### Step 1: Data Pooling & Shuffling
The system creates a "shuffled sequence" and calculates the total number of available rows to manage the stream limit.

### Step 2: Sequential Streaming
Records are sent one-by-one to the Ingestion System (`127.0.0.1:5001`).

- Interval: Uniformly distributed random delay (2–5 seconds) to simulate real-world arrival.
- Circular logic: If the requested stream limit exceeds the total rows, the system restarts from the beginning of the shuffled pool.

### Step 3: Label Reception
While streaming, the system's HTTP endpoint remains active. When the Evaluation System sends a classification:

- Approval logic: Labels `>= 4` are marked as APPROVED; others are REJECTED.
- Storage: Results are stored in volatile memory for the duration of the session.

## 6. Performance & Testing Logs
Once the streaming sequence is finished, the console will prompt you:

```
Are you ready to plot the logs? (y/n)
```

If `y` is selected, the system runs the Log Aggregator. It scans the `../logs/` directory for files relevant to your current Phase.

- Phase 0 logs: Client, Ingestion, Preparation, Segregation, and Development.
- Phase 1 logs: Client, Ingestion, Preparation, Production, and Evaluation.

Output:
- A unified `testing_log.csv` containing correlated timestamps for every `player_id`.
- This file is optimized for spreadsheet software to generate Responsiveness and Elasticity plots.

## 7. Continuous Operation
After log generation is complete (or skipped), the system does not terminate. It clears the current session state and returns to Section 3, allowing you to start a new stream or switch phases immediately.