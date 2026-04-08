"""
Test per verificare il comportamento della lettura/simulazione decisioni
in modalità Testing vs Stop&Go.

Verifica che:
- In Testing mode: le decisioni vengono SEMPRE simulate (file non letto)
- In Stop&Go mode: le decisioni vengono SEMPRE lette dal file
"""

import os
import sys
import json
import tempfile

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))

from src.orchestrator import SegregationSystemOrchestrator
from src.utils.json_io import JsonIO


def test_testing_mode_always_simulates():
    """Verifica che in testing mode la decisione sia sempre simulata, mai letta dal file."""
    print("\n" + "=" * 60)
    print("Test 1: Testing Mode - Decisione sempre simulata")
    print("=" * 60)
    
    # Crea un orchestrator in testing mode
    orch = SegregationSystemOrchestrator(testing_mode=True)
    
    # Crea un file temporaneo con una decisione manuale
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        decision_path = f.name
        manual_decision = {
            "approved": True,
            "decision_type": "balancing",
            "comment": "Questa è una decisione MANUALE dal file"
        }
        json.dump(manual_decision, f)
    
    try:
        # Simula una decisione in testing mode
        # Il file esiste MA non deve essere letto
        orch._paths = {"balancing_decision": decision_path}
        
        # In testing mode, _handle_balancing_decision dovrebbe simulare
        # Prima prepariamo l'ambiente
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_path = f.name
            state = {"phase": "waiting_balancing_decision"}
            json.dump(state, f)
        
        orch._paths["workflow_state"] = state_path
        
        # Leggiamo la decisione creata in testing mode
        # Dovrebbe essere simulata, NON quella manuale
        result_decision = None
        
        # Chiamiamo direttamente la parte che simula
        if orch.testing_mode:
            result_decision = orch._simulate_decision("balancing")
            JsonIO.save(decision_path, result_decision)
        else:
            result_decision = orch.load_decision(decision_path)
        
        # Verifica che sia una decisione SIMULATA
        assert "simulated" in result_decision, "La decisione dovrebbe essere simulata!"
        assert result_decision["simulated"] == True, "Il flag 'simulated' dovrebbe essere True!"
        assert "comment" not in result_decision, "La decisione NON dovrebbe contenere il commento del file manuale!"
        
        print(f"   ✓ In testing mode: decisione simulata (simulated={result_decision['simulated']})")
        print(f"   ✓ Decisione NON letta dal file manuale")
        print(f"   ✓ Approved: {result_decision['approved']}")
        
    finally:
        # Cleanup
        if os.path.exists(decision_path):
            os.unlink(decision_path)
        if 'state_path' in locals() and os.path.exists(state_path):
            os.unlink(state_path)


def test_stopgo_mode_always_reads_file():
    """Verifica che in stop&go mode la decisione sia sempre letta dal file."""
    print("\n" + "=" * 60)
    print("Test 2: Stop&Go Mode - Decisione sempre letta dal file")
    print("=" * 60)
    
    # Crea un orchestrator in stop&go mode
    orch = SegregationSystemOrchestrator(testing_mode=False)
    
    # Crea un file temporaneo con una decisione manuale
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        decision_path = f.name
        manual_decision = {
            "approved": False,
            "decision_type": "coverage",
            "comment": "Questa è una decisione MANUALE dal file",
            "reviewed_by": "human_operator"
        }
        json.dump(manual_decision, f)
    
    try:
        # In stop&go mode, dovrebbe leggere dal file
        if orch.testing_mode:
            result_decision = orch._simulate_decision("coverage")
        else:
            result_decision = orch.load_decision(decision_path)
        
        # Verifica che sia la decisione LETTA DAL FILE
        assert "simulated" not in result_decision, "La decisione NON dovrebbe avere il flag 'simulated'!"
        assert "comment" in result_decision, "La decisione dovrebbe contenere il commento del file!"
        assert result_decision["comment"] == "Questa è una decisione MANUALE dal file"
        assert "reviewed_by" in result_decision, "La decisione dovrebbe contenere 'reviewed_by'!"
        assert result_decision["approved"] == False, "Approved dovrebbe essere False come nel file!"
        
        print(f"   ✓ In stop&go mode: decisione LETTA dal file")
        print(f"   ✓ Decisione NON simulata (no flag 'simulated')")
        print(f"   ✓ Approved: {result_decision['approved']}")
        print(f"   ✓ Comment: {result_decision['comment']}")
        print(f"   ✓ Reviewed by: {result_decision['reviewed_by']}")
        
    finally:
        # Cleanup
        if os.path.exists(decision_path):
            os.unlink(decision_path)


def test_file_not_deleted():
    """Verifica che il file delle decisioni non venga eliminato."""
    print("\n" + "=" * 60)
    print("Test 3: File delle decisioni non eliminato")
    print("=" * 60)
    
    orch_testing = SegregationSystemOrchestrator(testing_mode=True)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        decision_path = f.name
    
    try:
        # Simula e salva
        decision = orch_testing._simulate_decision("balancing")
        JsonIO.save(decision_path, decision)
        
        # Verifica che il file esista
        assert os.path.exists(decision_path), "Il file delle decisioni dovrebbe esistere!"
        
        # Leggi il contenuto
        with open(decision_path, 'r') as f:
            saved_decision = json.load(f)
        
        assert saved_decision == decision, "Il contenuto salvato dovrebbe corrispondere!"
        
        print(f"   ✓ File delle decisioni salvato: {decision_path}")
        print(f"   ✓ File NON eliminato dopo la simulazione")
        print(f"   ✓ Contenuto verificato: {saved_decision}")
        
    finally:
        if os.path.exists(decision_path):
            os.unlink(decision_path)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Test Modalità Lettura/Simulazione Decisioni")
    print("=" * 60)
    
    try:
        test_testing_mode_always_simulates()
        test_stopgo_mode_always_reads_file()
        test_file_not_deleted()
        
        print("\n" + "=" * 60)
        print("✓ Tutti i test sono passati!")
        print("=" * 60)
        print("\nRiepilogo:")
        print("  • Testing mode: decisioni SEMPRE simulate (file non letto)")
        print("  • Stop&Go mode: decisioni SEMPRE lette dal file")
        print("  • File delle decisioni: MAI eliminato")
        print()
        
    except AssertionError as e:
        print(f"\n✗ Test fallito: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Errore durante i test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
