import pickle
from Data.classifier import Classifier
from Inputs.hyperParameters import HyperParameters


class CommunicationController:
    """Sends the final classifier or configuration to an external consumer."""

    def send_classifier(self, classifier: Classifier) -> None:
        print(
            f"[CommunicationController] Sending classifier "
            f"'{classifier.classifier_id}' "
            f"(model size: {len(classifier.model)} bytes)"
        )
        # TODO: serialize / transmit classifier.model over transport layer

    def send_configuration(self, hyper_params: HyperParameters) -> None:
        print(
            f"[CommunicationController] Sending configuration: {hyper_params}"
        )
        # TODO: transmit hyper_params to the requesting system