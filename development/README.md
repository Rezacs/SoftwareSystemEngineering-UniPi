# 1. Setup & Configuration
Before launching, ensure your configuration is defined in the only hardcoded path in the system:

* **File Path:** `Data/configs/config.json`
* **Contents:** Define your network settings, file paths, model feature columns, and hyperparameter search space here.

---

# 2. Launching the System
Open your terminal and run the main entry point:

```bash
python main.py
```

---

# 3. Select your Mode
1. Stop & Go : The system pauses at key milestones for you to inspect plots and provide input via `Data\configs\user_input.json`
2. Manual Mode : Decisions are simulated based on report data. No manual intervention required

---

# 4. Triggering the Workflow
If you are running the system in a simulation environment, after starting main.py, launch the data provider in a separate terminal:

```bash
python src/segregation_system_simulation.py
```

---

# 5. The 6-Phase Pipeline
Phase 1: Initialization (Starting → Ready)

The system loads `Data\configs\config.json`, initializes the CommunicationController, and prepares the environment.

- BPMN Task: SET AVERAGE HYPERPARAMS

- Action: Calculates baseline hyperparameter averages from your configuration.

- Transition: Automatically moves to Phase 2.

---

Phase 2: Calibration (LearningCurve)

- BPMN Task: CALIBRATE & GENERATE CALIBRATION REPORT

- System Activity: Trains a model using average parameters and generates learning_curve.png.

- # Human Intervention: Inspect the plot.

If the curve hasn't flattened: Update `max_iter` in `Data\configs\user_input.json`.
If satisfied: Set `good_max_iter`: true in `Data\configs\user_input.json`.

---

Phase 3: Validation (Validation)

- BPMN Task: GENERATE VALIDATION REPORT

- System Activity: Performs a grid search on all defined hyperparameter configurations.

- Output: Saves trained models as .sav files and generates a detailed `Data\reports\validation_report.json`.

---

Phase 4: Model Selection (ValidationReport)

- BPMN Gateway: IS THERE A VALID CLASSIFIER?

- # Human Intervention: Review validation_report.json.

- To Proceed: Enter the index of your chosen model in `Data\config\user_input.json`.

- To Retry: Enter 0 to loop back to Phase 1 (subject to max_outer_iterations).

---

Phase 5: Testing (Testing)

- BPMN Task: GENERATE TEST REPORT

- System Activity: Loads the selected model and evaluates it against the Test Set.

- Goal: Check for Generalization (ensuring test performance matches validation performance).

---

Phase 6: Deployment (Results)

- BPMN Gateway: TEST PASSED?

- # Human Intervention: Review testing_report.json.

- Approve: Set "approved": true. The system sends the model to the Production System via HTTP.

- Reject: Set "approved": false. The system logs a `Data\reports\rejected_report` and resets to IDLE.

---

# 6. Persistence Note

The system state is saved in `Data\internal\status.json`. If the process is interrupted, re-running main.py will resume the orchestrator exactly where it left off.