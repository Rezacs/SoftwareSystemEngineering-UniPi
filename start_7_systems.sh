#!/bin/bash

# Get the directory where the script is located
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Calculate the venv path (2 folders up from ROOT, then venv/bin/activate)
VENV_ACTIVATE="$(dirname "$(dirname "$ROOT")")/venv/bin/activate"

echo ""
read -p "Do you want to activate the virtual environment? (Y/N): " USE_VENV
echo ""

# Function to open a new Terminal window and run a command
run_in_new_tab() {
    local title=$1
    local cmd=$2
    # This uses AppleScript to tell Terminal to open a new window and execute the command
    osascript -e "tell application \"Terminal\" to do script \"echo -n -e '\\033]0;$title\\007'; $cmd\""
}

if [[ "$USE_VENV" =~ ^[Yy]$ ]]; then
    # Commands WITH Virtual Environment
    ACTIVATE_CMD="source \"$VENV_ACTIVATE\""
    
    run_in_new_tab "Client Side System" "cd \"$ROOT/client_side\" && $ACTIVATE_CMD && python3 main.py"
    sleep 2
    run_in_new_tab "Ingestion Launcher" "cd \"$ROOT\" && $ACTIVATE_CMD && python3 ingestion_launcher.py"
    sleep 2
    run_in_new_tab "Preparation Launcher" "cd \"$ROOT\" && $ACTIVATE_CMD && python3 preparation_launcher.py"
    sleep 2
    run_in_new_tab "Segregation System" "cd \"$ROOT/segregation\" && $ACTIVATE_CMD && python3 main.py"
    sleep 2
    run_in_new_tab "Development System" "cd \"$ROOT/development\" && $ACTIVATE_CMD && python3 main.py"
    sleep 2
    run_in_new_tab "Production System" "cd \"$ROOT/production\" && $ACTIVATE_CMD && python3 main.py"
    sleep 2
    run_in_new_tab "Evaluation System" "cd \"$ROOT/evaluation\" && $ACTIVATE_CMD && python -m src.main"

else
    # Commands WITHOUT Virtual Environment
    run_in_new_tab "Client Side System" "cd \"$ROOT/client_side\" && python3 main.py"
    sleep 2
    run_in_new_tab "Ingestion Launcher" "cd \"$ROOT\" && python3 ingestion_launcher.py"
    sleep 2
    run_in_new_tab "Preparation Launcher" "cd \"$ROOT\" && python3 preparation_launcher.py"
    sleep 2
    run_in_new_tab "Ingestion System" "cd \"$ROOT/ingestion\" && python3 ingestion_launcher.py"
    sleep 2
    run_in_new_tab "Development System" "cd \"$ROOT/development\" && python3 main.py"
    sleep 2
    run_in_new_tab "Production System" "cd \"$ROOT/production\" && python3 main.py"
    sleep 2
    run_in_new_tab "Evaluation System" "cd \"$ROOT/evaluation/src\" && python -m src.main"
fi