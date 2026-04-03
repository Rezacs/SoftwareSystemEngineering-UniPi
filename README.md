# ⚽ Football Social Club – DataOps Project

## 📌 Overview
This project is developed as part of the **Software System Engineering (SSE)** course (Academic Year 2025/2026).

It implements a **Data Factory (DataOps pipeline)** for statistical classification in the context of a football-based social platform.  
The system processes raw data, prepares it, trains machine learning models, performs predictions, and evaluates performance.

---

## 🧠 Project Architecture

The system is composed of **7 modular systems** that form a complete DataOps pipeline:

### Real Systems
1. **Client Side System** (`1-client_side/`) - Simulates client data collection
2. **Ingestion System** (`2-ingestion/`) - Ingests raw records from client
3. **Preparation System** (`3-preparation/`) - Prepares and normalizes sessions
4. **Segregation System** (`4-segregation/`) - Balances data and creates calibration sets
5. **Development System** (`5-development/`) - Trains, validates and tests ML models
6. **Production System** (`6-production/`) - Real-time classification with trained models
7. **Evaluation System** (`7-evaluation/`) - Evaluates classifier performance

Each system is implemented as a modular Python component and orchestrated through a **Flask application** (`app.py`).

### Mock Files (For Isolated Testing Only)
- `4-segregation/mock_upstream_system.py` - Simulates Preparation System
- `4-segregation/mock_downstream_system.py` - Simulates Development System

**Note**: Mock files are used ONLY for testing the Segregation System in isolation.

### Testing Tools (Utilities)
- `7-evaluation/service_class_tester.py` - Automated service testing tool
- `7-evaluation/stress_test.py` - Stress testing utility
- `7-evaluation/test_client.py` - Test client utility

---

## ⚙️ Technologies Used

- Python 3.12
- Flask 3.1.3
- NumPy & Pandas
- JSON-based communication
- SQLite (for Segregation System)
- CSV data processing
- Pyreverse (UML generation)
- Graphviz (diagram rendering)

---

## 🚀 Quick Start

### Prerequisites

**Conda Environment (Recommended)**
```bash
conda activate SSE_project
```

Or create it:
```bash
conda create -n SSE_project python=3.12
conda activate SSE_project
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Complete System

**Option 1: Start the Flask App**
```bash
# Set PYTHONPATH for module imports
export PYTHONPATH="1-client_side:2-ingestion:3-preparation:5-development:6-production:7-evaluation:$PYTHONPATH"
python app.py
```

Server starts at: `http://127.0.0.1:5000`

**Note**: The PYTHONPATH is needed because system directories use dashes (e.g., `1-client_side`) 
but Python imports use underscores (e.g., `from service import`).

**Option 2: Web Interface**

Open in browser: `http://127.0.0.1:5000`

You'll see the interface to run individual systems or the complete pipeline.

---

## 🧪 Testing the Systems

### Test Complete Pipeline

Execute all systems in sequence:

```bash
# With app.py running
curl -X POST http://127.0.0.1:5000/pipeline/run
```

Or use the web interface and click "Run Pipeline".

### Test Individual Systems

```bash
# Health check
curl http://127.0.0.1:5000/health

# Run individual systems
curl -X POST http://127.0.0.1:5000/client-side/run
curl -X POST http://127.0.0.1:5000/ingestion/run
curl -X POST http://127.0.0.1:5000/preparation/run
curl -X POST http://127.0.0.1:5000/segregation/run
curl -X POST http://127.0.0.1:5000/development/run
curl -X POST http://127.0.0.1:5000/production/run
curl -X POST http://127.0.0.1:5000/evaluation/run
```

### Test Segregation System in Isolation

The Segregation System can be tested independently with mock systems.

See detailed workflow in: [`4-segregation/README.md`](4-segregation/README.md)

**Quick test:**
```bash
cd 4-segregation

# Terminal 1: Reset state
python -m src.utils.reset_runtime_state

# Terminal 2: Mock upstream (simulates Preparation - port 5001)
python mock_upstream_system.py

# Terminal 3: Segregation System (port 5002)
python api.py

# Terminal 4: Mock downstream (simulates Development - port 5003)
python mock_downstream_system.py

# Terminal 1: Run workflow
curl -X POST http://127.0.0.1:5001/prepared-sessions/send \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 1.0}'

python main.py
python manual_set_balancing_decision.py true
python main.py
python manual_set_coverage_decision.py true
python main.py

# Verify output
curl http://127.0.0.1:5003/last-calibration-set/status
```

---

## 📂 Project Structure

```
SoftwareSystemEngineering-UniPi/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── 1-client_side/           # Client Side System
│   ├── service.py
│   └── timestamp_log_controller.py
│
├── 2-ingestion/             # Ingestion System
│   ├── orchestrator.py
│   ├── raw_session_creator.py
│   └── record_receiver.py
│
├── 3-preparation/           # Preparation System
│   ├── orchestrator.py
│   ├── prepared_session_creator.py
│   ├── prepared_session_sender.py
│   └── raw_session_receiver.py
│
├── 4-segregation/           # Segregation System
│   ├── README.md            # Detailed documentation
│   ├── api.py               # REST API
│   ├── main.py              # Main workflow
│   ├── src/                 # Core system
│   ├── config/              # Configuration
│   ├── data/                # Input/Output data
│   ├── mock_upstream_system.py    # Mock for testing
│   └── mock_downstream_system.py  # Mock for testing
│
├── 5-development/           # Development System (ML Training)
│   ├── orchestrator.py
│   ├── training_orchestrator.py
│   ├── validation_orchestrator.py
│   └── testing_orchestrator.py
│
├── 6-production/            # Production System
│   ├── main.py
│   ├── src/
│   └── Data/
│       └── configs/
│           └── config.json
│
├── 7-evaluation/            # Evaluation System
│   ├── evaluate_classifier.py
│   ├── service_class_tester.py    # Testing tool
│   ├── stress_test.py             # Testing tool
│   └── test_client.py             # Testing tool
│
├── data/                    # Global data directory
│   ├── inputs/
│   └── outputs/
│
└── templates/               # Flask HTML templates
```

---

## 🔧 System Details

### 1. Client Side System
Simulates client-side data collection with timestamps.

**Entry point**: `service.py`

### 2. Ingestion System
Receives raw records and creates raw sessions.

**Entry point**: `orchestrator.py`

### 3. Preparation System
Processes raw sessions and prepares them for segregation.

**Entry point**: `orchestrator.py`

### 4. Segregation System
Performs data balancing and creates calibration sets (training, validation, test).

**Entry point**: `api.py` (REST API) or `main.py` (workflow)
**Configuration**: `config/config.json`

Features:
- Class balancing verification
- Feature coverage analysis
- Manual approval workflow
- SQLite database storage
- Visual reports (PNG)

### 5. Development System
Trains and validates machine learning models.

**Entry point**: `orchestrator.py`

Phases:
1. Training (`training_orchestrator.py`)
2. Validation (`validation_orchestrator.py`)
3. Testing (`testing_orchestrator.py`)

### 6. Production System
Applies trained classifier for real-time predictions.

**Entry point**: `main.py`
**Configuration**: `Data/configs/config.json`

### 7. Evaluation System
Evaluates classifier performance against expert ratings.

**Entry point**: `evaluate_classifier.py`

---

## 📊 Data Flow

```
Client Side → Ingestion → Preparation → Segregation → Development → Production → Evaluation
                                            ↓
                                    Calibration Sets
                                    (train/val/test)
```

1. **Client Side** generates player data
2. **Ingestion** creates raw sessions
3. **Preparation** normalizes and prepares sessions
4. **Segregation** balances data and creates calibration sets
5. **Development** trains ML classifier
6. **Production** uses classifier for predictions
7. **Evaluation** compares predictions with expert ratings

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check which process is using a port
lsof -i :5000
lsof -i :5001

# Kill the process
kill <PID>
```

### Import Errors
Make sure you're in the correct directory and conda environment is activated:
```bash
which python
python --version
conda activate SSE_project
```

### Missing Dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 📝 Notes

- The Segregation System has the most detailed documentation in its [own README](4-segregation/README.md)
- Mock files are ONLY for isolated testing - not part of the real pipeline
- All systems can be run individually via `app.py` or as a complete pipeline
- The Production System requires configuration in `Data/configs/config.json`

---

## 👥 Authors

Software System Engineering Course - University of Pisa (2025/2026)

---

## 📄 License

This project is developed for educational purposes as part of the SSE course
