from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler
import uuid

from Data.preparedSession import PreparedSession
from Data.learningSet import LearningSet
from Data.hyperParameters import HyperParameters
from src.developmentSystemOrchestrator import DevelopmentSystemOrchestrator


def build_learning_set(n_samples: int = 300) -> LearningSet:
    X, y = make_classification(
        n_samples=n_samples,
        n_features=3,        # exactly skillOverall, socialInfluence, injuriesImpact
        n_informative=3,
        n_redundant=0,
        random_state=42,
    )
    X = StandardScaler().fit_transform(X)

    sessions = [
        PreparedSession(
            UUID=str(uuid.uuid4()),
            idPlayer=f"player_{i}",
            skillOverall=float(X[i, 0]),
            socialInfluence=float(X[i, 1]),
            injuriesImpact=float(X[i, 2]),
            label=int(y[i]),
        )
        for i in range(n_samples)
    ]

    train_end = int(n_samples * 0.70)
    val_end   = int(n_samples * 0.85)
    return LearningSet(
        training_set=sessions[:train_end],
        validation_set=sessions[train_end:val_end],
        test_set=sessions[val_end:],
    )


if __name__ == "__main__":
    learning_set = build_learning_set(n_samples=300)

    hp_configs = [
        HyperParameters(num_layers=2, num_neurons=32,  num_iterations=200, classifier_id="clf_A"),
        HyperParameters(num_layers=3, num_neurons=64,  num_iterations=300, classifier_id="clf_B"),
        HyperParameters(num_layers=4, num_neurons=128, num_iterations=400, classifier_id="clf_C"),
    ]

    orchestrator = DevelopmentSystemOrchestrator(
        learning_set=learning_set,
        hyper_param_configs=hp_configs,
        overfitting_threshold=0.1,
        generalization_threshold=0.15,
        max_outer_iterations=3,
        testing_mode=True,
    )
    orchestrator.run()