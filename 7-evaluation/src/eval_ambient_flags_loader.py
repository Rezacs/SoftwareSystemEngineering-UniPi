"""
    Module for testing state configuration acquisition
"""
import json
import os
from src.utility.json_validation import validate_json_file_file
from src.utility import data_folder

"""
    Ambient flags for the Evaluation System
"""
DEBUGGING = True

TESTING_CONFIG_PATH_RELATIVE = "configs/eval_ambient_flags.json"
TESTING_CONFIG_SCHEMA_PATH_RELATIVE = "schema/eval_ambient_flags_schema.json"

TESTING_VALIDITY = \
    validate_json_file_file(TESTING_CONFIG_PATH_RELATIVE, TESTING_CONFIG_SCHEMA_PATH_RELATIVE)

testing_conf_location = os.path.join(data_folder, TESTING_CONFIG_PATH_RELATIVE)

with open(testing_conf_location, "r", encoding="UTF-8") as jsonTestingFile:
    testing_config_content = json.load(jsonTestingFile)

# This forces the SQLite database to be created inside the data/ folder!
raw_db_name = testing_config_content["db_name"]
DB_NAME = os.path.join(data_folder, raw_db_name)

DEBUGGING = testing_config_content["testing"] == "True"
TIMING = testing_config_content["timing"] == "True"
DELETE_DB_ON_LOAD = testing_config_content["delete_db_on_load"] == "True"
PRINT_LABELS_DF = testing_config_content["print_labels"] == "True"

if DEBUGGING:
    print(f'DB_NAME : {DB_NAME}')
    print(f'DELETE_DB_ON_LOAD : {DELETE_DB_ON_LOAD}')