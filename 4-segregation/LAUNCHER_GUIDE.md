# Script Launcher - Guida Rapida

## Panoramica

Gli script launcher semplificano l'avvio del Segregation System avviando automaticamente tutti i servizi mock necessari.

## Script Disponibili

### 🚀 `launcher.sh` - Avvio Sistema

**Cosa fa:**
1. Controlla se i mock systems sono già attivi
2. Se non lo sono, li avvia in background
3. Invia le prepared sessions
4. Ti lascia il controllo per lanciare `main.py` manualmente

**Uso:**
```bash
./launcher.sh
```

**Output:**
- ✓ Mock Upstream System avviato
- ✓ REST API avviata
- ✓ Mock Downstream System avviato
- ✓ Prepared sessions inviate

**Poi tu lanci:**
```bash
python3 main.py
```

### 📊 `check_status.sh` - Verifica Stato

**Cosa fa:**
Controlla se tutti i servizi sono attivi e funzionanti.

**Uso:**
```bash
./check_status.sh
```

**Output:**
```
✓ Mock Upstream System is running on port 5001
✓ Segregation REST API is running on port 5002
✓ Mock Downstream System is running on port 5003
```

### 🛑 `stop_launcher.sh` - Stop Servizi

**Cosa fa:**
Ferma tutti i servizi avviati dal launcher (creato automaticamente da `launcher.sh`).

**Uso:**
```bash
./stop_launcher.sh
```

### 🔄 `reset_all.sh` - Reset Completo

**Cosa fa:**
1. Ferma tutti i servizi
2. Resetta lo stato del runtime
3. Pulisce il database e i file di stato

**Uso:**
```bash
./reset_all.sh
```

## Workflow Tipico

### Prima Volta

```bash
# 1. Avvia tutto in un colpo
./launcher.sh

# 2. Lancia il sistema principale
python3 main.py

# 3. Scegli modalità [1] Stop&Go o [2] Testing
```

### Volte Successive (Stop&Go)

Se sei in modalità Stop & Go e devi fornire una decisione:

```bash
# 1. Modifica decisione (manualmente o con script helper)
python3 manual_set_balancing_decision.py true

# 2. Rilancia main
python3 main.py
```

**NON serve rilanciare launcher.sh** - i servizi sono già attivi!

### Controllo Stato

```bash
# Verifica che tutto sia attivo
./check_status.sh
```

### Reset Completo

```bash
# Ferma tutto e resetta
./reset_all.sh

# Poi riparti da capo
./launcher.sh
python3 main.py
```

## Domande Frequenti

### Devo lanciare launcher.sh ogni volta che avvio main.py?

**NO!** Lancia `launcher.sh` solo **una volta all'inizio**. I servizi restano attivi in background. Poi puoi lanciare `main.py` tutte le volte che vuoi.

### Come faccio a sapere se i servizi sono attivi?

```bash
./check_status.sh
```

### I servizi si fermano quando chiudo il terminale?

No, girano in background come daemon. Per fermarli usa:
```bash
./stop_launcher.sh
```

### Posso inviare più batch di sessioni?

Sì, puoi rilanciare il curl manualmente:
```bash
curl -X POST http://127.0.0.1:5001/prepared-sessions/send \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 1.0}'
```

### Cosa fa test_workflow.py?

È un **test unitario** che verifica solo il codice dell'orchestrator, NON avvia nessun servizio. È per sviluppatori che vogliono testare la logica interna.

## Confronto: Prima vs Ora

### ❌ Prima (4 terminali manuali)

```
Terminal 1: python3 mock_upstream_system.py
Terminal 2: python3 api.py  
Terminal 3: python3 mock_downstream_system.py
Terminal 4: curl ... && python3 main.py
```

### ✅ Ora (1 terminale)

```
./launcher.sh    # Una volta sola
python3 main.py  # Ogni volta che serve
```

## File Creati dal Launcher

- `.launcher_pids` - PID dei processi avviati
- `stop_launcher.sh` - Script per fermare i servizi

Questi file sono automatici, non modificarli manualmente.
