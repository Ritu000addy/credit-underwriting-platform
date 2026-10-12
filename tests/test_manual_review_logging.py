import logging
from types import SimpleNamespace

import pytest

from backend.app.api.routes.manual_review import (
    log_manual_review_event,
)


@pytest.mark.parametrize(
    ("level", "event"),
    [
        (logging.INFO, "started"),
        (logging.INFO, "completed"),
        (logging.WARNING, "failed"),
    ],
)
def test_manual_review_logs_include_request_correlation(
    caplog,
    level,
    event,
):
    request = SimpleNamespace(
        state=SimpleNamespace(request_id="REQ-SYNTHETIC-001")
    )

    with caplog.at_level(logging.INFO, logger="backend.workflow"):
        log_manual_review_event(
            level=level,
            event=event,
            request=request,
            application_id="SYN-APP-001",
            action="recommendation",
            review_id="SYN-REV-001",
            status="IN_PROGRESS",
            error_code="SYNTHETIC_TEST_ERROR" if event == "failed" else None,
        )

    assert f"manual_review_{event}" in caplog.text
    assert "request_id=REQ-SYNTHETIC-001" in caplog.text
    assert "application_id=SYN-APP-001" in caplog.text
    assert "action=recommendation" in caplog.text
    assert "review_id=SYN-REV-001" in caplog.text

    if event == "failed":
        assert "error_code=SYNTHETIC_TEST_ERROR" in caplog.text
    else:
        assert "error_code=-" in caplog.text