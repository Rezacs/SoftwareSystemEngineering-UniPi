from Data.classifier import Classifier
from Inputs.hyperParameters import HyperParameters
class CommunicationController:
    """Sends the trained classifier and its configuration to an external system."""
 
    def send_classifier(self, classifier: Classifier) -> None:
        print(
            f"[CommunicationController] Sending classifier '{classifier.classifier_id}' "
            f"(model size={len(classifier.model or b'')} bytes) …"
        )
        # --- Stub: implement actual transport (HTTP, message queue, etc.) ---
 
    def send_configuration(self, hyper_params: HyperParameters) -> None:
        print(
            f"[CommunicationController] Sending configuration for "
            f"classifier '{hyper_params.classifier_id}' "
            f"(layers={hyper_params.num_layers}, neurons={hyper_params.num_neurons}) …"
        )
        # --- Stub: implement actual transport ---