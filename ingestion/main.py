"""
Reza edit
"""


import argparse
from ingestion.orchestrator import IngestionSystemOrchestrator

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="A script that initialize the Ingestion system orchestrator")

    parser.add_argument("--testing_mode", type=bool, default=False, help="Launch the orchestrator in testing mode to generate logs (optional)")
    parser.add_argument("--config_file_path", type=str, default=None, help="path of the configuration file (optional)")

    args = parser.parse_args()

    orchestrator = IngestionSystemOrchestrator(args.config_file_path,args.testing_mode)
    orchestrator.start()