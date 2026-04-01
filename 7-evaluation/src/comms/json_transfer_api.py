"""
This module contains API classes which handle json reception and sending.
In order to use the API, add them as resources to your Flask application.
"""
from typing import Callable

from flask import request
from flask_restful import Resource

from src.utility.json_validation import validate_json_data_file


# see : https://www.askpython.com/python-modules/flask/semd-json-data-flask-app
class ReceiveJsonApi(Resource):
    """
    This API allows other nodes to send json to the Flask application.
    """
    def __init__(self,
                 json_schema_path: str = None,
                 handler: Callable[[dict], None] = None):
        """
        Initialize the API.
        :param json_schema_path !!! <relative to the data folder>
        :param handler: optional function to call after the json has been saved in the filesystem.
                        The handler function should not take too much time to return (consider threading)
        """
        self.json_schema_path = json_schema_path
        self.handle_request = handler

    def post(self):
        #  --- print("inside jsonAPI post")
        """
        Handle a POST request.
        Other nodes should send a POST request when they want to send a json to this endpoint.
        The json must be inserted in the ``json['json_file']`` field of the request.
        :return: status code 201 on success, 400 if the file does not exist
        """
        received_json = request.get_json()
        #  --- print("gotten the json")
        # Validate received json (must exist, and be valid)
        if self.json_schema_path is not None \
                and not validate_json_data_file(received_json, self.json_schema_path):
            print(f'testing object :{received_json}\n\n against path :{self.json_schema_path}')
            return 'JSON validation failed', 400
        # Execute the handler function if it was specified
        if self.handle_request is not None:
            self.handle_request(received_json)
        #  --- print("about to return 201")
        return 'JSON correctly received', 201  # request success -> resources created.


class HumanDecisionApi(Resource):
    """
    REST API endpoint for the Human Manager to submit their decision
    based on the generated Evaluation Report.
    """
    def __init__(self, handler):
        self.handler = handler

    def post(self):
        try:
            received_json = request.get_json()
            if not received_json:
                return {"message": "Invalid JSON"}, 400
                
            # Expecting format: {"batch_id": "Batch_123", "accept": true}
            if "accept" not in received_json:
                return {"message": "Missing 'accept' key in JSON payload"}, 400

            # Pass the decision back to the Orchestrator
            self.handler(received_json)
            
            return {"message": "Human decision successfully processed"}, 201
            
        except Exception as e:
            return {"message": f"Server error: {str(e)}"}, 500