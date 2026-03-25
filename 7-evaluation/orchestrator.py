# evaluation/orchestrator.py
from label_manager import LabelManager
from report_generator import ReportGenerator
from models import EvaluationConfiguration, EvaluationReport
from common.json_io import JsonIO
from typing import Optional

class EvaluationSystemOrchestrator:
    def __init__(self, buffer_path="data/outputs/evaluation_buffer.json"):
        # Initialize our two streamlined Managers
        self.label_manager = LabelManager(buffer_path=buffer_path)
        self.report_generator = ReportGenerator()
        
        # In a fully integrated system, this configuration would be loaded from 
        # the Configuration System. For now, we mock the active rules here.
        self.active_config = EvaluationConfiguration(
            required_label_count=5, # System waits for 5 labels before evaluating
            error_threshold_th1=5,
            max_consecutive_errors_th2=3
        )

    # ==========================================
    # PHASE 1: Automated Label Processing
    # ==========================================
    def receiveLabel(self, json_payload: dict) -> Optional[EvaluationReport]:
        """
        Processes an incoming label from Ingestion/Classification.
        Returns an EvaluationReport ONLY if the buffer has reached the required count.
        """
        # 1. Parse and Store the Label
        label_pair = self.label_manager.parse_incoming_json(json_payload)
        self.label_manager.storeLabel(label_pair)

        # 2. Check if we have enough labels to run an evaluation
        required_count = self.active_config.getRequiredLabelCount()
        is_sufficient = self.label_manager.checkSufficientLabels(required_count)

        # 3. The "opt" block from our Sequence Diagram
        if is_sufficient:
            # Fetch data
            pairs = self.label_manager.getMatchedPairs()
            
            # Generate Report
            report = self.report_generator.generateEvaluationReport(
                pairs=pairs, 
                config=self.active_config
            )
            
            # Clear the buffer for the next batch of incoming labels
            self.label_manager.removeLabels()
            
            # Return the report (This alerts the UI that a report is ready to view)
            return report
        
        # Not enough labels yet, return None to keep waiting
        return None

    # ==========================================
    # PHASE 2: Manual Evaluation via UI
    # ==========================================
    def submitEvaluationDecision(self, report: EvaluationReport, is_approved: bool) -> None:
        """
        Triggered when the ML Engineer clicks 'Approve' or 'Discard' in the UI.
        Outputs the final JSON so the human can share it on MS Teams.
        """
        # Update the entity
        report.setApprovalStatus(is_approved)
        
        # Output the final decision using JsonIO
        status_text = "approved" if is_approved else "discarded"
        output_path = f"data/outputs/pipeline_{status_text}_{report.report_id[:8]}.json"
        
        # Convert the dataclass to a dictionary for saving via JsonIO
        output_data = {
            "report_id": report.report_id,
            "timestamp": report.generation_timestamp.isoformat(),
            "total_labels_evaluated": report.total_labels_evaluated,
            "total_errors": report.total_errors,
            "max_consecutive_errors": report.max_consecutive_errors,
            "is_approved": report.is_approved
        }
        
        JsonIO.save(output_path, output_data)
        print(f"Final decision saved to {output_path}. Ready to share.")