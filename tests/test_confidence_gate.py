import os
from unittest.mock import patch

os.environ["MOCK_MODE"] = "true"

from incident_pipeline import trigger_rundeck


INCIDENT_NUMBER = "INC0042183"
LOW_RISK_JOB_UUID = "a1b2c3d4-0001-0001-0001-000000000001"
DRAIN_NODE_JOB_UUID = "a1b2c3d4-0008-0001-0001-000000000008"
ROTATE_CREDENTIALS_JOB_UUID = "a1b2c3d4-0009-0001-0001-000000000009"
FULFILMENT_RETRY_JOB_UUID = "a1b2c3d4-0010-0001-0001-000000000010"
UNKNOWN_JOB_UUID = "a1b2c3d4-9999-0001-0001-000000000999"


def call_trigger(job_uuid: str, confidence: float) -> dict:
    trigger_rundeck.MOCK_MODE = True
    with (
        patch.object(trigger_rundeck.time, "sleep", return_value=None),
        patch.object(
            trigger_rundeck.requests,
            "post",
            side_effect=AssertionError("Rundeck HTTP call should not run in mock mode"),
        ),
    ):
        return trigger_rundeck.trigger_job(job_uuid, confidence, INCIDENT_NUMBER)


def assert_executed(result: dict) -> None:
    assert result["status"] == "executed"
    assert result["requires_approval"] is False
    assert result["execution_id"].startswith("mock-")


def assert_pending_approval(result: dict) -> None:
    assert result["status"] == "pending_approval"
    assert result["requires_approval"] is True
    assert result["execution_id"] == ""


def test_above_global_floor_executes() -> None:
    result = call_trigger(LOW_RISK_JOB_UUID, 0.75)

    assert_executed(result)


def test_exactly_at_global_floor_executes() -> None:
    result = call_trigger(LOW_RISK_JOB_UUID, 0.70)

    assert_executed(result)


def test_below_global_floor_pending() -> None:
    result = call_trigger(LOW_RISK_JOB_UUID, 0.69)

    assert_pending_approval(result)


def test_well_below_floor_pending() -> None:
    result = call_trigger(LOW_RISK_JOB_UUID, 0.50)

    assert_pending_approval(result)


def test_drain_node_requires_0_90() -> None:
    result = call_trigger(DRAIN_NODE_JOB_UUID, 0.89)

    assert_pending_approval(result)


def test_drain_node_at_0_90_executes() -> None:
    result = call_trigger(DRAIN_NODE_JOB_UUID, 0.90)

    assert_executed(result)


def test_rotate_credentials_requires_0_85() -> None:
    result = call_trigger(ROTATE_CREDENTIALS_JOB_UUID, 0.84)

    assert_pending_approval(result)


def test_rotate_credentials_at_0_85_executes() -> None:
    result = call_trigger(ROTATE_CREDENTIALS_JOB_UUID, 0.85)

    assert_executed(result)


def test_fulfilment_retry_never_executes_low() -> None:
    result = call_trigger(FULFILMENT_RETRY_JOB_UUID, 0.50)

    assert_pending_approval(result)


def test_fulfilment_retry_never_executes_high() -> None:
    result = call_trigger(FULFILMENT_RETRY_JOB_UUID, 0.99)

    assert_pending_approval(result)


def test_fulfilment_retry_never_executes_1_0() -> None:
    result = call_trigger(FULFILMENT_RETRY_JOB_UUID, 1.00)

    assert_pending_approval(result)


def test_confidence_exactly_0() -> None:
    result = call_trigger(LOW_RISK_JOB_UUID, 0.00)

    assert_pending_approval(result)


def test_confidence_exactly_1() -> None:
    result = call_trigger(LOW_RISK_JOB_UUID, 1.00)

    assert_executed(result)


def test_unknown_job_uses_global_floor() -> None:
    result = call_trigger(UNKNOWN_JOB_UUID, 0.70)

    assert_executed(result)
