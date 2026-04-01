# Segregation System

Questo sistema:
- riceve `preparedSession` via REST
- salva le sessioni in SQLite
- genera `balancing_report` e `coverage_report`
- produce un `calibration_set` finale

## Simulazione locale

Per simulare il sistema in locale servono 4 terminali:
- `mock_upstream_system.py`: simula il sistema precedente su `127.0.0.1:5001`
- `api.py`: avvia il Segregation System su `127.0.0.1:5002`
- `mock_downstream_system.py`: simula il sistema successivo su `127.0.0.1:5003`
- un terminale operativo per `curl`, `main.py` e decisioni manuali

## Ambiente Python

Va bene qualsiasi ambiente Python, purché tutti i terminali usino lo stesso interprete e abbiano le dipendenze installate.

Con `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r 4-segregation/requirements.txt
```

Con `conda`:

```bash
conda create -n segregation-test python=3.11
conda activate segregation-test
pip install -r 4-segregation/requirements.txt
```

## Config

In [config.json](4-segregation/config/config.json) imposta:

```json
"developmentSystemEndpoint": "http://127.0.0.1:5003/calibration-set"
```

## Workflow rapido

Apri 4 terminali nella cartella [4-segregation](4-segregation) e attiva in tutti lo stesso ambiente Python.

**Terminale 2**

```bash
python3 mock_upstream_system.py
```

**Terminale 3**

```bash
python3 api.py
```

**Terminale 4**

```bash
python3 mock_downstream_system.py
```

**Terminale 1 (operativo)**

```bash
python3 -m src.utils.reset_runtime_state
```

Poi, nello stesso terminale:

```bash
curl http://127.0.0.1:5001/health
curl http://127.0.0.1:5002/health
curl http://127.0.0.1:5003/health
```

Invia il batch di input:

```bash
curl -X POST http://127.0.0.1:5001/prepared-sessions/send \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 1.0}'
```

Avanza il workflow:

```bash
python3 main.py
python3 manual_set_balancing_decision.py true
python3 main.py
python3 manual_set_coverage_decision.py true
python3 main.py
```

Verifica output finale:

```bash
curl http://127.0.0.1:5003/last-calibration-set/status
```

## Decisioni manuali

Le decisioni umane non passano via API. Vengono lette da questi file:
- [balancing_decision.json](4-segregation/data/input/balancing_decision.json)
- [coverage_decision.json](4-segregation/data/input/coverage_decision.json)

Puoi scriverli a mano oppure usare:

```bash
python3 manual_set_balancing_decision.py true
python3 manual_set_coverage_decision.py true
```

## Input e output utili

Input di test:
- [4-segregation/data/input](4-segregation/data/input)

Output principali:
- [balancing_report.json](4-segregation/data/output/balancing_report.json)
- [coverage_report.json](4-segregation/data/output/coverage_report.json)
- [calibration_set.json](4-segregation/data/output/calibration_set.json)
- [segregation_workflow_state.json](4-segregation/data/output/segregation_workflow_state.json)
- [segregationDB.db](4-segregation/data/output/segregationDB.db)
