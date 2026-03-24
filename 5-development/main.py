from Inputs.learningSet import LearningSet, PreparedSession
from Inputs.hyperParameters import HyperParameters
from Orchestrators.developmentSystemOrchestrator import DevelopmentSystemOrchestrator

if __name__ == "__main__":
    # Build a small synthetic dataset
    sessions = [PreparedSession(data={"x": i}) for i in range(100)]
    learning_set = LearningSet(
        training_set=sessions[:70],
        validation_set=sessions[70:85],
        test_set=sessions[85:],
    )
 
    # Define hyper-parameter search space
    hp_configs = [
        HyperParameters(num_layers=2, num_neurons=32, num_iterations=50, classifier_id="clf_A"),
        HyperParameters(num_layers=3, num_neurons=64, num_iterations=100, classifier_id="clf_B"),
        HyperParameters(num_layers=4, num_neurons=128, num_iterations=150, classifier_id="clf_C"),
    ]
 
    orchestrator = DevelopmentSystemOrchestrator(
        learning_set=learning_set,
        hyper_param_configs=hp_configs,
        overfitting_threshold=0.1,
        generalization_threshold=0.15,
        max_outer_iterations=3,
    )
    orchestrator.run()