"""
Reza - edit
"""

import argparse
from orchestrator import PreparationSystemOrchestrator

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="A script that initialize the Preparation system orchestrator")

    parser.add_argument("--testing_mode", type=bool, default=False, help="Launch the orchestartor in testing mode to generate logs (optional)")
    parser.add_argument("--config_file_path", type=str, default=None, help="path of the configuration file (optional)")

    args = parser.parse_args()

    orchestrator = PreparationSystemOrchestrator(args.config_file_path)
    orchestrator.start()