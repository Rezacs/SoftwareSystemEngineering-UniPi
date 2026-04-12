"""
This is a script to launch the orchestrator, this must me used outside the preparation folder since, the system is built like a module
the command to launch the system should be : pyhton preparation_launcher.py [--testing_mode=True] [--config_file_path=="example/example"]
 
"""

import argparse
from preparation.orchestrator import PreparationSystemOrchestrator

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="A script that initialize the Preparation system orchestrator")

    parser.add_argument("--testing_mode", type=bool, default=False, help="Launch the orchestartor in testing mode to generate logs (optional)")
    parser.add_argument("--config_file_path", type=str, default=None, help="path of the configuration file (optional)")

    args = parser.parse_args()

    orchestrator = PreparationSystemOrchestrator(args.config_file_path,args.testing_mode)
    orchestrator.start()