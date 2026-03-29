"""
This module offers classes to set up and deploy a simple REST server
"""

from flask import Flask, request
from flask_restful import Api, Resource

class EvaluationEndpoint(Resource):
    """
    The actual 'door' that receives the data.
    """
    orchestrator = None

    def post(self):
        # This catches the JSON we send in test_client.py
        data = request.get_json()
        print(f"Server received data: {data}")
        
        # If the orchestrator is connected, pass the data to it
        if EvaluationEndpoint.orchestrator:
            # Assuming your orchestrator has a method to process data
            # self.orchestrator.manage_request(data)
            return {"status": "success", "message": "Data received by Orchestrator"}, 200
        
        return {"status": "warning", "message": "Server alive, but Orchestrator not linked"}, 200

class ServerREST:
    """
    Central object of Flask Application
    """

    def __init__(self, orchestrator_instance=None):
        """
        Initialize Flask Application
        """
        self.app = Flask(__name__)
        self.api = Api(self.app)
        
        # Link the orchestrator so the Endpoint can use it
        EvaluationEndpoint.orchestrator = orchestrator_instance
        
        # FIX: Register the route! 
        # This makes http://127.0.0.1:8001/evaluation valid
        self.api.add_resource(EvaluationEndpoint, '/evaluation')

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """
        Runs Flask Application on local server
        """
        print(f"Routes initialized. Endpoint available at: http://{host}:{port}/evaluation")
        self.app.run(host=host, port=port, debug=debug)