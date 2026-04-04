# Segregation System

Questo sistema:
- riceve `preparedSession` via REST
- salva le sessioni in SQLite
- genera `balancing_report` e `coverage_report`
- produce un `calibration_set` finale

## Modalità di Esecuzione

Il sistema supporta due modalità:

1. **Stop & Go**: Modalità interattiva per revisione manuale dei report
2. **Testing**: Modalità automatica con decisioni simulate (70% accettazione, 30% rifiuto)

## Setup

### Ambiente Python

Configurare l'ambiente Python con le dipendenze necessarie.

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

### Configurazione

In [config.json](4-segregation/config/config.json) imposta:

```json
"developmentSystemEndpoint": "http://127.0.0.1:5003/calibration-set"
```

## Workflow di Esecuzione

### 🚀 Metodo Rapido (Consigliato)

Usa gli script launcher per avviare tutto automaticamente:

```bash
# 1. Prima volta - avvia tutti i servizi
./launcher.sh

# 2. Lancia il sistema principale
python3 main.py

# 3. Scegli modalità [1] Stop&Go o [2] Testing
```

**Vantaggi:**
- ✅ Avvia automaticamente tutti i mock systems
- ✅ Controlla se sono già attivi
- ✅ Invia le prepared sessions
- ✅ Un solo comando invece di 4 terminali

Per maggiori dettagli vedi [LAUNCHER_GUIDE.md](LAUNCHER_GUIDE.md)

### 📋 Metodo Manuale (4 Terminali)

Se preferisci il controllo completo, puoi avviare ogni servizio manualmente.

### Setup Iniziale (una volta)

Apri 3 terminali nella cartella [4-segregation](4-segregation) e attiva in tutti lo stesso ambiente Python.

**Terminale 1 - Mock Upstream (Preparation System)**

```bash
python3 mock_upstream_system.py
```

**Terminale 2 - REST API (riceve sessioni)**

```bash
python3 api.py
```

**Terminale 3 - Mock Downstream (Development System)**

```bash
python3 mock_downstream_system.py
```

### Lancio del Sistema

Apri un 4° terminale (operativo) e:

```bash
# Reset stato (solo se necessario)
python3 -m src.utils.reset_runtime_state

# Verifica health dei sistemi
curl http://127.0.0.1:5001/health
curl http://127.0.0.1:5002/health
curl http://127.0.0.1:5003/health

# Avvia il sistema principale
python3 main.py
```

**Importante**: La modalità viene chiesta **una sola volta all'avvio**. Il sistema manterrà la modalità selezionata per l'intero workflow fino al ritorno in idle.

Il sistema ti chiederà di scegliere la modalità:
- `[1]` Stop & Go: modalità interattiva (si ferma ad ogni checkpoint)
- `[2]` Testing: modalità automatica (prosegue fino alla fine del workflow)

### Invio Dati

Una volta avviato il sistema, invia le sessioni:

```bash
curl -X POST http://127.0.0.1:5001/prepared-sessions/send \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 1.0}'
```

## Modalità Stop & Go (Interattiva)

In questa modalità, il sistema **processa l'intero workflow** fermandosi ai checkpoint di decisione. La modalità viene selezionata all'avvio e mantenuta fino al completamento o rifiuto del workflow.

### Workflow:

1. **Avvio iniziale**: Scegli modalità [1] Stop & Go
2. **Sistema genera balancing report** → si ferma
3. **Tu decidi** (modifica JSON o usa script helper)
4. **Rilancia** `python3 main.py` → il sistema riprende in modalità Stop & Go
5. **Sistema genera coverage report** (se balancing approvato) → si ferma
6. **Tu decidi** (modifica JSON o usa script helper)
7. **Rilancia** `python3 main.py` → il sistema finalizza
8. **Completamento** → sistema torna in idle

### Checkpoint e Decisioni:

1. **Dopo Balancing Report**: 
   - Esamina `data/output/balancing_report.json` e `balancing_plot.png`
   - Modifica `data/input/balancing_decision.json`:
     ```json
     {"approved": true}
     ```
     oppure
     ```json
     {"approved": false}
     ```
   - Rilancia `python3 main.py` per continuare

2. **Dopo Coverage Report** (se balancing approvato):
   - Esamina `data/output/coverage_report.json` e `coverage_plot.png`
   - Modifica `data/input/coverage_decision.json`:
     ```json
     {"approved": true}
     ```
     oppure
     ```json
     {"approved": false}
     ```
   - Rilancia `python3 main.py` per finalizzare

### Script Helper per Decisioni Manuali

Puoi usare gli script helper invece di modificare manualmente i JSON:

```bash
# Approva balancing
python3 manual_set_balancing_decision.py true

# Rifiuta balancing
python3 manual_set_balancing_decision.py false

# Approva coverage
python3 manual_set_coverage_decision.py true

# Rifiuta coverage
python3 manual_set_coverage_decision.py false
```

## Modalità Testing (Automatica)

In questa modalità:
- Il sistema elabora automaticamente le sessioni in arrivo
- Le decisioni sono simulate con:
  - **70% probabilità di accettazione**
  - **30% probabilità di rifiuto**
- Il ciclo si ripete continuamente
- Non richiede intervento manuale

Ideale per:
- Test automatici
- Simulazione di carico
- Validazione del workflow completo

## Flusso Completo

1. Le sessioni arrivano via REST API (`api.py` in ascolto)
2. Quando ci sono abbastanza sessioni (`sufficientSessionNumber` da config)
3. Il sistema genera il `balancing_report`
4. **CHECKPOINT 1**: Decisione su bilanciamento classi
   - ✅ Approvato → genera `coverage_report`
   - ❌ Rifiutato → reset, attende nuove sessioni
5. **CHECKPOINT 2**: Decisione su copertura features
   - ✅ Approvato → genera e invia `calibration_set` al Development System
   - ❌ Rifiutato → reset, attende nuove sessioni
6. Il sistema si resetta automaticamente e torna in attesa

## File di Output

- **Reports**: `data/output/balancing_report.json`, `coverage_report.json`
- **Plots**: `data/output/balancing_plot.png`, `coverage_plot.png`
- **Calibration Set**: `data/output/calibration_set.json`
- **Stato Workflow**: `data/output/segregation_workflow_state.json`
- **Database**: `data/output/segregationDB.db`

## File di Input (Decisioni)

- **Balancing Decision**: `data/input/balancing_decision.json`
- **Coverage Decision**: `data/input/coverage_decision.json`

Questi file sono usati solo in modalità Stop & Go. In modalità Testing vengono generati automaticamente dal sistema.
