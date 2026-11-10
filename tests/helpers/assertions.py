from helpers.protocol import ERROR_STATUS, SUCCESS_STATUS


def assert_succeeded(response: dict, expected_operation: str) -> None:
    assert response["status"] == SUCCESS_STATUS, f"expected success, received {response}"
    assert response["operation"] == expected_operation


def assert_refused(response: dict, expected_error_code: str) -> None:
    assert response["status"] == ERROR_STATUS, f"expected refusal, received {response}"
    assert response["payload"]["error_code"] == expected_error_code
    assert response["payload"]["error_description"]


def setup_succeeded(response: dict, scenario_step: str) -> dict:
    assert response["status"] == SUCCESS_STATUS, f"scenario step '{scenario_step}' failed: {response}"
    return response
