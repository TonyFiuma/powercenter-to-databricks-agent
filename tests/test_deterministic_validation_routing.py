from src.agent.graph import route_after_deterministic_validation


def test_valid_routes_to_deterministic_end():
    state = {
        "validation_status": "VALID",
    }

    route = route_after_deterministic_validation(state)

    assert route == "valid"


def test_requires_review_routes_to_ai_fallback():
    state = {
        "validation_status": "REQUIRES_REVIEW",
    }

    route = route_after_deterministic_validation(state)

    assert route == "review"


def test_unsupported_routes_to_stop():
    state = {
        "validation_status": "UNSUPPORTED",
    }

    route = route_after_deterministic_validation(state)

    assert route == "unsupported"