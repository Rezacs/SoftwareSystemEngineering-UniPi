#!/bin/bash
# Quick Start Demo - mostra l'uso completo del sistema

cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║         SEGREGATION SYSTEM - QUICK START DEMO             ║
╔════════════════════════════════════════════════════════════╗

Questo demo mostra come usare il sistema con gli script launcher.

STEP 1: Avvia tutti i servizi (una volta sola)
-----------------------------------------------
  ./launcher.sh

  Questo script:
  - Controlla se i mock systems sono già attivi
  - Li avvia se necessario (in background)
  - Invia le prepared sessions

STEP 2: Lancia il sistema principale
-------------------------------------
  python3 main.py

  - Scegli modalità [1] Stop&Go o [2] Testing
  - Il sistema processa le sessioni

MODALITÀ STOP & GO:
-------------------
Il sistema si ferma ad ogni checkpoint.

Dopo balancing report:
  1. Controlla: data/output/balancing_report.json
  2. Decidi: python3 manual_set_balancing_decision.py true
  3. Continua: python3 main.py

Dopo coverage report:
  1. Controlla: data/output/coverage_report.json
  2. Decidi: python3 manual_set_coverage_decision.py true
  3. Finalizza: python3 main.py

MODALITÀ TESTING:
-----------------
Il sistema processa tutto automaticamente.
Le decisioni sono simulate (70% approve, 30% reject).

COMANDI UTILI:
--------------
  ./check_status.sh    # Verifica stato servizi
  ./stop_launcher.sh   # Ferma tutti i servizi
  ./reset_all.sh       # Reset completo

NOTA IMPORTANTE:
----------------
Lancia launcher.sh solo UNA VOLTA all'inizio!
I servizi restano attivi in background.
Puoi lanciare main.py tutte le volte che vuoi.

EOF

echo ""
read -p "Vuoi avviare il launcher ora? (y/n): " choice

if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    echo ""
    ./launcher.sh
else
    echo ""
    echo "Ok, quando sei pronto lancia: ./launcher.sh"
fi
