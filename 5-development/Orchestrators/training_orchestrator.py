
from Data.classifier import Classifier
from Data.learningPlot import LearningPlot
from Data.validationReport import ValidationReport
from Inputs.hyperParameters import HyperParameters
from Inputs.learningSet import LearningSet
from typing import Optional
class TrainingOrchestrator:
    """Handles classifier training for a single hyper-parameter configuration."""
 
    def __init__(self) -> None:
        self._hyper_params: Optional[HyperParameters] = None
        self._training_set: Optional[LearningSet] = None
 
    def set_parameters(
        self,
        hyper_params: HyperParameters,
        training_set: LearningSet,
    ) -> None:
        print(f"[TrainingOrchestrator] Setting parameters: {hyper_params}")
        self._hyper_params = hyper_params
        self._training_set = training_set
 
    def train_classifier(self) -> Classifier:
        """Train a classifier using the configured hyper-parameters."""
        if self._hyper_params is None or self._training_set is None:
            raise RuntimeError("Parameters must be set before training.")
 
        print(
            f"[TrainingOrchestrator] Training classifier '{self._hyper_params.classifier_id}' "
            f"with {self._hyper_params.num_iterations} iterations …"
        )
 
        # --- Stub: replace with real ML training logic ---
        training_error = 0.05
        validation_error = 0.07
        model_bytes = b"<binary_model_placeholder>"
 
        classifier = Classifier(
            classifier_id=self._hyper_params.classifier_id,
            number_of_neurons=self._hyper_params.num_neurons,
            number_of_layers=self._hyper_params.num_layers,
            training_error=training_error,
            validation_error=validation_error,
            model=model_bytes,
        )
        print(
            f"[TrainingOrchestrator] Training complete. "
            f"Training error={training_error}, Validation error={validation_error}"
        )
        return classifier
 
    def generate_learning_plot(self, num_epochs: int = 10) -> LearningPlot:
        """Generate a learning (MSE vs epoch) plot for the last training run."""
        print("[TrainingOrchestrator] Generating learning plot …")
        # --- Stub: replace with actual epoch-level metrics ---
        mse = [1.0 / (i + 1) for i in range(num_epochs)]
        epochs = list(range(1, num_epochs + 1))
        return LearningPlot(mse=mse, number_of_epochs=epochs, approve=False, set_epochs=False)
 