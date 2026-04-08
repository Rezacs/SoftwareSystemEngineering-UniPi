"""
Quick test to verify the workflow implementation.
This script tests the orchestrator initialization and basic state management.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.orchestrator import SegregationSystemOrchestrator
from src.utils.json_io import JsonIO

def test_orchestrator_init():
    """Test that orchestrator initializes correctly in both modes."""
    print("=" * 60)
    print("Testing Orchestrator Initialization")
    print("=" * 60)
    
    # Test Stop&Go mode
    print("\n1. Testing Stop & Go mode...")
    try:
        orch_stop_go = SegregationSystemOrchestrator(testing_mode=False)
        print("   ✓ Stop & Go orchestrator created")
        print(f"   ✓ Testing mode: {orch_stop_go.testing_mode}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test Testing mode
    print("\n2. Testing Testing mode...")
    try:
        orch_testing = SegregationSystemOrchestrator(testing_mode=True)
        print("   ✓ Testing orchestrator created")
        print(f"   ✓ Testing mode: {orch_testing.testing_mode}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test state management
    print("\n3. Testing state management...")
    try:
        test_state_path = "data/output/test_state.json"
        orch_testing.save_state("test_phase", test_state_path, test_data="test_value")
        loaded = orch_testing.load_state(test_state_path)
        assert loaded["phase"] == "test_phase"
        assert loaded["test_data"] == "test_value"
        print("   ✓ State save/load works")
        
        # Clean up
        if os.path.exists(test_state_path):
            os.remove(test_state_path)
            print("   ✓ Test file cleaned up")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test decision simulation
    print("\n4. Testing decision simulation...")
    try:
        decision = orch_testing._simulate_decision("balancing")
        assert "approved" in decision
        assert "simulated" in decision
        assert decision["simulated"] == True
        print(f"   ✓ Simulated decision: approved={decision['approved']}")
        
        decision2 = orch_testing._simulate_decision("coverage")
        print(f"   ✓ Simulated decision: approved={decision2['approved']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_orchestrator_init()
    sys.exit(0 if success else 1)
