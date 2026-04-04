# Test End-to-End - Segregation → Development System

## Panoramica

Questa guida spiega come testare l'intero flusso usando il **vero Development System** invece dei mock.

## Prerequisiti

### Configurazione

**Segregation System** (`4-segregation/config/config.json`):
- `sufficientSessionNumber`: 8 (servono almeno 8 sessioni)
- `developmentSystemEndpoint`: "http://127.0.0.1:5003/calibration-set"

**Development System** (`5-development/Data/configs/config.json`):
- `listen_port`: 5003
- Deve essere configurato correttamente

### Sessioni Disponibili

Il Segregation System ha **9 prepared sessions** in `data/input/`:
- `prepared_session_01.json` through `prepared_session_09.json`
- Servono almeno **8 sessioni** per procedere

## Metodo 1: Script Automatico test_e2e.sh

### Uso Rapido

```bash
./test_e2e.sh
```

### Cosa fa lo script:

1. ✅ Avvia Mock Upstream System (porta 5001)
2. ✅ Avvia Segregation REST API (porta 5002)
3. ✅ Avvia **VERO Development System** (porta 5003) in modalità Testing
4. ✅ Invia tutte le 9 prepared sessions
5. ✅ Ti lascia il controllo per testare manualmente

### Dopo l'esecuzione:

```bash
# Lancia il Segregation System
python3 main.py

# Scegli modalità:
# [1] Stop & Go - per controllo manuale
# [2] Testing - per test automatico
```

### Stop Servizi:

```bash
./stop_e2e.sh
```

## Metodo 2: Launcher Enhanced

### Con Development System Reale

```bash
./launcher_with_dev.sh --real-dev
```

### Con Mock (default)

```bash
./launcher_with_dev.sh
```

## Metodo 3: Setup Manuale Completo

### Terminal 1: Mock Upstream
```bash
cd 4-segregation
python3 3-prepSys_simulation.py
```

### Terminal 2: Segregation API
```bash
cd 4-segregation
python3 api.py
```

### Terminal 3: Development System (REALE)
```bash
cd 5-development
python3 main.py
# Scegli [2] Testing per test automatico
```

### Terminal 4: Invio Sessioni + Test
```bash
cd 4-segregation

# Invia sessioni
curl -X POST http://127.0.0.1:5001/prepared-sessions/send \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 0.5}'

# Verifica stato
./check_status.sh

# Lancia Segregation System
python3 main.py
```

## Flusso Completo di Test

### 1. Preparazione

```bash
# Reset tutto
./reset_all.sh

# Avvia servizi (con Development System reale)
./test_e2e.sh
```

### 2. Test in Modalità Testing (Automatico)

```bash
# Lancia Segregation in Testing mode
python3 main.py
# Scegli [2]

# Il sistema:
# - Genera balancing report
# - Simula decisione (70% approve)
# - Genera coverage report
# - Simula decisione (70% approve)
# - Invia calibration set al Development System
# - Il Development System lo processa automaticamente
```

### 3. Test in Modalità Stop & Go (Manuale)

```bash
# Lancia Segregation in Stop&Go mode
python3 main.py
# Scegli [1]

# Sistema genera balancing report e si ferma
# Tu decidi:
python3 manual_set_balancing_decision.py true

# Rilancia
python3 main.py

# Sistema genera coverage report e si ferma
# Tu decidi:
python3 manual_set_coverage_decision.py true

# Rilancia per finalizzare
python3 main.py

# Il calibration set viene inviato al Development System
# Controlla i log del Development System per vedere il processing
```

## Verifica Risultati

### Segregation System Output

```bash
# Verifica stato workflow
cat data/output/segregation_workflow_state.json

# Verifica calibration set inviato
cat data/output/calibration_set.json

# Verifica reports
cat data/output/balancing_report.json
cat data/output/coverage_report.json
```

### Development System Output

```bash
cd ../5-development

# Verifica dati ricevuti
cat Data/internal/received_data.json

# Verifica learning sets
cat Data/internal/learning_sets.json

# Verifica stato
cat Data/internal/status.json

# Verifica reports generati
ls -la Data/reports/
```

## Troubleshooting

### Development System non si avvia

Se il Development System non parte automaticamente:

```bash
# Avvialo manualmente in un terminale separato
cd ../5-development
python3 main.py
# Scegli [2] Testing
```

### Porte occupate

```bash
# Verifica porte in uso
lsof -i :5001
lsof -i :5002
lsof -i :5003

# Ferma tutti i servizi
./stop_e2e.sh
./stop_launcher.sh
```

### Reset Completo

```bash
# Segregation System
cd 4-segregation
./reset_all.sh

# Development System
cd ../5-development
rm -f Data/internal/status.json
rm -f Data/internal/received_data.json
rm -f Data/internal/learning_sets.json
```

## Monitoraggio in Tempo Reale

### Tail logs in terminali separati:

```bash
# Terminal A: Segregation System
cd 4-segregation
python3 main.py

# Terminal B: Development System logs
cd 5-development
# (il sistema stampa già i log in console)

# Terminal C: Monitoring
cd 4-segregation
watch -n 2 './check_status.sh'
```

## Test con Batch Multipli

Per testare l'invio di batch multipli:

```bash
# Primo batch
curl -X POST http://127.0.0.1:5001/prepared-sessions/send \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 0.5}'

# Aspetta che il workflow completi...

# Secondo batch (dopo reset)
./reset_all.sh
./test_e2e.sh
python3 main.py
```

## Note Importanti

⚠️ **Development System in Testing Mode**: Lo script avvia automaticamente il Development System in modalità Testing (scelta automatica [2]). Questo permette il processing automatico del calibration set.

⚠️ **Numero Sessioni**: Servono almeno 8 sessioni. Il sistema ha 9 sessioni disponibili, quindi va bene per il test.

⚠️ **Auto-Reset**: Entrambi i sistemi supportano auto-reset, quindi possono processare batch multipli consecutivamente.

✅ **Raccomandazione**: Usa `test_e2e.sh` per test rapidi, o setup manuale per debugging dettagliato.
