from types import SimpleNamespace

import pytest

from backend.app.services.disbursement_service import (
    disbursement_service,
)


@pytest.mark.parametrize(
    ("method_name", "status", "expected_error"),
    [
        (
            "initiate_disbursement",
            "PROCESSED",
            "DISBURSEMENT_NOT_ELIGIBLE_FOR_INITIATION",
        ),
        (
            "mark_processing",
            "CREATED",
            "DISBURSEMENT_NOT_INITIATED",
        ),
        (
            "process_disbursement",
            "INITIATED",
            "DISBURSEMENT_NOT_READY_FOR_PROCESSING",
        ),
        (
            "fail_disbursement",
            "PROCESSED",
            "DISBURSEMENT_NOT_ELIGIBLE_FOR_FAILURE",
        ),
    ],
)
def test_invalid_disbursement_state_transition(
    method_name,
    status,
    expected_error,
):
    disbursement = SimpleNamespace(
        status=status,
    )

    method = getattr(
        disbursement_service,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match=expected_error,
    ):
        if method_name == "fail_disbursement":
            method(
                db=None,
                disbursement=disbursement,
                failure_reason="TEST_FAILURE",
            )
        else:
            method(
                db=None,
                disbursement=disbursement,
            )


def test_disbursement_status_is_unchanged_after_rejected_transition():
    disbursement = SimpleNamespace(
        status="PROCESSED",
    )

    with pytest.raises(
        ValueError,
        match="DISBURSEMENT_NOT_ELIGIBLE_FOR_INITIATION",
    ):
        disbursement_service.initiate_disbursement(
            db=None,
            disbursement=disbursement,
        )

    assert disbursement.status == "PROCESSED"