from flask import Flask, jsonify, render_template

from client_side.service import ClientSideService
from ingestion.orchestrator import IngestionSystemOrchestrator
from preparation.orchestrator import PreparationSystemOrchestrator
from segregation.orchestrator import SegregationSystemOrchestrator
from development.orchestrator import DevelopmentSystemOrchestrator
from production.orchestrator import ProductionSystemOrchestrator
from evaluation.orchestrator import EvaluationSystemOrchestrator

app = Flask(__name__)

client_service = ClientSideService()
ingestion_orchestrator = IngestionSystemOrchestrator()
preparation_orchestrator = PreparationSystemOrchestrator()
segregation_orchestrator = SegregationSystemOrchestrator()
development_orchestrator = DevelopmentSystemOrchestrator()
production_orchestrator = ProductionSystemOrchestrator()
evaluation_orchestrator = EvaluationSystemOrchestrator()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/client-side/run")
def run_client_side():
    result = client_service.save_json_message()
    return jsonify(result)


@app.post("/ingestion/run")
def run_ingestion():
    result = ingestion_orchestrator.run()
    return jsonify(result)


@app.post("/preparation/run")
def run_preparation():
    result = preparation_orchestrator.run()
    return jsonify(result)


@app.post("/segregation/run")
def run_segregation():
    result = segregation_orchestrator.run()
    return jsonify(result)


@app.post("/development/run")
def run_development():
    result = development_orchestrator.run()
    return jsonify(result)


@app.post("/production/run")
def run_production():
    result = production_orchestrator.run()
    return jsonify(result)


@app.post("/evaluation/run")
def run_evaluation():
    result = evaluation_orchestrator.run()
    return jsonify(result)


@app.post("/pipeline/run")
def run_pipeline():
    client_result = client_service.save_json_message()
    ingestion_result = ingestion_orchestrator.run()
    preparation_result = preparation_orchestrator.run()
    segregation_result = segregation_orchestrator.run()
    development_result = development_orchestrator.run()
    production_result = production_orchestrator.run()
    evaluation_result = evaluation_orchestrator.run()

    return jsonify({
        "client_side": client_result,
        "ingestion": ingestion_result,
        "preparation": preparation_result,
        "segregation": segregation_result,
        "development": development_result,
        "production": production_result,
        "evaluation": evaluation_result
    })


if __name__ == "__main__":
    app.run(debug=True)