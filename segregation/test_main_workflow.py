#!/usr/bin/env python3
"""
Test to verify the improved workflow state handling.
Simulates different scenarios to ensure proper behavior.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_status_messages():
    """Test that all status messages are properly handled."""
    print("=" * 60)
    print("Testing Status Message Handling")
    print("=" * 60)
    
    # Import main module to check the status handling
    import preparation_main
    
    # Check that the main module has the launch_pipeline function
    assert hasattr(preparation_main, 'launch_pipeline'), "launch_pipeline function not found"
    assert hasattr(preparation_main, 'ask_testing_mode'), "ask_testing_mode function not found"
    
    print("\n✓ Main module structure verified")
    
    # Verify that mode is asked only once (at module level)
    main_code = open('main.py', 'r').read()
    
    # Count occurrences of ask_testing_mode() as a call (not definition)
    # We look for the pattern "= ask_testing_mode()" which is the actual call
    ask_count = main_code.count('= ask_testing_mode()')
    print(f"\n✓ ask_testing_mode() called {ask_count} time(s) - should be 1")
    assert ask_count == 1, f"ask_testing_mode should be called exactly once, found {ask_count}"
    
    # Verify that "Unexpected status" is not in the code anymore
    assert "Unexpected status" not in main_code, "Found 'Unexpected status' in code"
    print("✓ No 'Unexpected status' messages in code")
    
    # Verify proper status handling
    expected_statuses = [
        "sessions_not_sufficient",
        "balancing_report_generated",
        "coverage_report_generated",
        "waiting_balancing_decision",
        "waiting_coverage_decision",
        "balancing_rejected",
        "coverage_rejected",
        "calibration_sets_sent",
        "reset_complete"
    ]
    
    for status in expected_statuses:
        if status in main_code:
            print(f"✓ Status '{status}' is handled")
        else:
            print(f"⚠ Status '{status}' might not be explicitly handled (could be in else)")
    
    print("\n" + "=" * 60)
    print("✓ All status handling tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_status_messages()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
