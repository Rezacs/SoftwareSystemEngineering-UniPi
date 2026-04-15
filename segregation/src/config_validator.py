"""Validates runtime parameters loaded from segregationConfig.json."""


def validate_runtime_parameters(config: dict) -> dict:
    """Validate and normalize runtime parameters used by the segregation workflow.

    Rules:
    - sufficientSessionNumber must be coercible to int and strictly greater than 0.
    - balancingTolerance must be coercible to float and strictly between 0 and 1.
    """
    if not isinstance(config, dict):
        raise ValueError("Invalid segregation config: configuration must be a JSON object")

    if "sufficientSessionNumber" not in config:
        raise ValueError("Invalid segregation config: missing 'sufficientSessionNumber'")
    if "balancingTolerance" not in config:
        raise ValueError("Invalid segregation config: missing 'balancingTolerance'")

    try:
        sufficient_sessions = int(config["sufficientSessionNumber"])
    except (TypeError, ValueError):
        raise ValueError(
            "Invalid segregation config: 'sufficientSessionNumber' must be an integer > 0"
        )

    if sufficient_sessions <= 0:
        raise ValueError(
            "Invalid segregation config: 'sufficientSessionNumber' must be > 0"
        )

    try:
        balancing_tolerance = float(config["balancingTolerance"])
    except (TypeError, ValueError):
        raise ValueError(
            "Invalid segregation config: 'balancingTolerance' must be a float between 0 and 1 (excluded)"
        )

    if not (0.0 < balancing_tolerance < 1.0):
        raise ValueError(
            "Invalid segregation config: 'balancingTolerance' must be > 0 and < 1"
        )

    config["sufficientSessionNumber"] = sufficient_sessions
    config["balancingTolerance"] = balancing_tolerance
    return config