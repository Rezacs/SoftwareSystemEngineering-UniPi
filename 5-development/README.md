1. Setup
Before launching, ensure your configuration is defined in the only hardcoded path:

File: Data/configs/config.json

Check: Verify listen_port (e.g., 8080) and ensure the folders for reports/models exist.

2. Launch the System
Open your terminal and run the main entry point:

Bash
python main.py
Select Mode:

Enter 1 for Stop & Go: Manual mode. The system pauses for you to inspect plots and choose models.

Enter 2 for Testing: Automated mode. Decisions are simulated from existing reports.

3. Trigger the Workflow
The system will enter an IDLE state. To start the pipeline, send a JSON payload to the system's listener via HTTP POST

4. Interactive Usage (Stop & Go)
If you are in mode 1, the script will pause at specific BPMN tasks.

Check Console: The system will display the current phase (e.g., LearningCurve).

Inspect Output: Open the generated files (e.g., Data/reports/learning_curve.png).

Edit JSON: Open Data/config/user_input.json and update the values (e.g., set "good_max_iter": true or "best_model": 3).

Confirm: Return to the terminal and type y when prompted: Decisions saved in Data/user_input.json? (y/n).

5. Completion & Persistent Listening
The system is designed to stay alive regardless of the outcome:

Test Passed: The model is sent to the Production System.

Test Failed: A rejected report is saved locally (Data/reports/testing_report.json).

Auto-Reset: In both cases, the orchestrator calls _reset_status(). The terminal will return to the IDLE state, waiting for the next POST /data payload without needing a restart.

If you're testing the system, launch, after main.py, the file in .../src/segregation_system_simulation.py