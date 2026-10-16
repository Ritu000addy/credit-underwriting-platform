
import json

import pytest
from pydantic import ValidationError

from backend.app.services.document_intelligence_service import (
    document_intelligence_service,
)


SOURCE_TEXT = """
Bank Statement
Statement Period: January 2026
Closing Balance: INR 25,000
Monthly Credits: INR 80,000
Monthly Debits: INR 45,000
"""


def make_response(fields):
    return json.dumps({"fields": fields})


def test_valid_evidence_is_preserved():
    raw_response = make_response(
        {
            "closing_balance": {
                "value": "25000",
                "confidence": 0.95,
                "evidence": "Closing Balance: INR 25,000",
            }
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )
    )

    assert fields["closing_balance"].value == "25000"
    assert fields["closing_balance"].evidence == (
        "Closing Balance: INR 25,000"
    )
    assert "closing_balance" not in missing
    assert not any(
        conflict.field_name == "closing_balance"
        and conflict.conflict_type == "EVIDENCE_NOT_FOUND"
        for conflict in conflicts
    )


def test_evidence_not_present_in_source_is_rejected():
    raw_response = make_response(
        {
            "closing_balance": {
                "value": "999999",
                "confidence": 0.95,
                "evidence": "Closing Balance: INR 999999",
            }
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )
    )

    assert fields["closing_balance"].value is None
    assert any(
        conflict.field_name == "closing_balance"
        and conflict.conflict_type == "EVIDENCE_NOT_FOUND"
        for conflict in conflicts
    )


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_out_of_range_confidence_is_rejected(confidence):
    raw_response = make_response(
        {
            "closing_balance": {
                "value": "25000",
                "confidence": confidence,
                "evidence": "Closing Balance: INR 25,000",
            }
        }
    )

    with pytest.raises(
        RuntimeError,
	match = "DOCUMENT_EXTRACTION_INVALID_FIELD_SCHEMA",
    ):
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )


def test_malformed_json_is_not_silently_accepted():
    with pytest.raises(
	RuntimeError,
        match="DOCUMENT_EXTRACTION_INVALID_JSON",
    ):
        document_intelligence_service._parse_response(
            '{"fields": ', "BANK_STATEMENT", SOURCE_TEXT
        )


def test_missing_required_fields_are_reported():
    raw_response = make_response(
        {
            "closing_balance": {
                "value": "25000",
                "confidence": 0.95,
                "evidence": "Closing Balance: INR 25,000",
            }
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )
    )

    assert "statement_period" in missing
    assert "monthly_credits" in missing
    assert "monthly_debits" in missing
    assert "closing_balance" not in missing


def test_unexpected_fields_generate_a_warning():
    raw_response = make_response(
        {
            "closing_balance": {
                "value": "25000",
                "confidence": 0.95,
                "evidence": "Closing Balance: INR 25,000",
            },
            "credit_decision": {
                "value": "APPROVE",
                "confidence": 1.0,
                "evidence": "Closing Balance: INR 25,000",
            },
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )
    )

    assert "credit_decision" not in fields
    assert warnings



def test_invalid_field_structure_is_rejected():
    raw_response = make_response(
        {
            "closing_balance": "25000"
        }
    )

    with pytest.raises(
        RuntimeError,
        match="DOCUMENT_EXTRACTION_INVALID_FIELD_SCHEMA",
    ):
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )


def test_non_object_fields_payload_is_rejected():
    raw_response = json.dumps({"fields": []})

    with pytest.raises(
        RuntimeError,
        match="DOCUMENT_EXTRACTION_INVALID_SCHEMA",
    ):
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", SOURCE_TEXT
        )


def test_duplicate_contradictory_values_are_not_silently_assumed():
    contradictory_source = """
    Bank Statement
    Closing Balance: INR 25,000
    Closing Balance: INR 35,000
    Statement Period: January 2026
    Monthly Credits: INR 80,000
    Monthly Debits: INR 45,000
    """

    raw_response = make_response(
        {
            "closing_balance": {
                "value": "25000",
                "confidence": 0.95,
                "evidence": "Closing Balance: INR 25,000",
            },
            "statement_period": {
                "value": "January 2026",
                "confidence": 0.95,
                "evidence": "Statement Period: January 2026",
            },
            "monthly_credits": {
                "value": "80000",
                "confidence": 0.95,
                "evidence": "Monthly Credits: INR 80,000",
            },
            "monthly_debits": {
                "value": "45000",
                "confidence": 0.95,
                "evidence": "Monthly Debits: INR 45,000",
            },
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", contradictory_source
        )
    )

    # This test documents the current behavior. If the parser does not
    # detect contradictory source values, it exposes a validation gap.
    assert (
        fields["closing_balance"].value is None
        or any(
            conflict.field_name == "closing_balance"
            for conflict in conflicts
        )
    )


@pytest.mark.parametrize(
    ("field_name", "label", "first_value", "second_value"),
    [
        (
            "closing_balance",
            "Closing Balance",
            "INR 25,000",
            "INR 35,000",
        ),
        (
            "monthly_credits",
            "Monthly Credits",
            "INR 80,000",
            "INR 90,000",
        ),
        (
            "monthly_debits",
            "Monthly Debits",
            "INR 45,000",
            "INR 55,000",
        ),
        (
            "average_balance",
            "Average Balance",
            "INR 20,000",
            "INR 30,000",
        ),
    ],
)
def test_contradictory_financial_summary_values_require_review(
    field_name, label, first_value, second_value
):
    source_text = f"""
    Bank Statement
    {label}: {first_value}
    {label}: {second_value}
    Statement Period: January 2026
    Monthly Credits: INR 80,000
    Monthly Debits: INR 45,000
    """

    raw_response = make_response(
        {
            field_name: {
                "value": first_value,
                "confidence": 0.95,
                "evidence": f"{label}: {first_value}",
            },
            "statement_period": {
                "value": "January 2026",
                "confidence": 0.95,
                "evidence": "Statement Period: January 2026",
            },
            "monthly_credits": {
                "value": "80000",
                "confidence": 0.95,
                "evidence": "Monthly Credits: INR 80,000",
            },
            "monthly_debits": {
                "value": "45000",
                "confidence": 0.95,
                "evidence": "Monthly Debits: INR 45,000",
            },
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", source_text
        )
    )

    assert fields[field_name].value is None

    assert any(
        conflict.field_name == field_name
        and conflict.conflict_type == "CONTRADICTORY_SOURCE_VALUES"
        for conflict in conflicts
    )


@pytest.mark.parametrize(
    ("field_name", "label"),
    [
        ("closing_balance", "Closing Balance"),
        ("monthly_credits", "Monthly Credits"),
        ("monthly_debits", "Monthly Debits"),
        ("average_balance", "Average Balance"),
    ],
)

def test_equivalent_numeric_summary_values_are_not_contradictory(
    field_name, label
):
    values = {
        "closing_balance": "25000",
        "monthly_credits": "80000",
        "monthly_debits": "45000",
        "average_balance": "25000",
    }
    numeric_value = int(values[field_name])

    source_text = f"""
    Bank Statement
    {label}: INR {numeric_value:,}
    {label}: {numeric_value}
    Statement Period: January 2026
    Monthly Credits: INR 80,000
    Monthly Debits: INR 45,000
    """

    values = {
        "closing_balance": "25000",
        "monthly_credits": "80000",
        "monthly_debits": "45000",
        "average_balance": "25000",
    }

    raw_response = make_response(
        {
            field_name: {
                "value": values[field_name],
                "confidence": 0.95,
                "evidence": f"{label}: INR 25,000",
            },
            "statement_period": {
                "value": "January 2026",
                "confidence": 0.95,
                "evidence": "Statement Period: January 2026",
            },
            "monthly_credits": {
                "value": "80000",
                "confidence": 0.95,
                "evidence": "Monthly Credits: INR 80,000",
            },
            "monthly_debits": {
                "value": "45000",
                "confidence": 0.95,
                "evidence": "Monthly Debits: INR 45,000",
            },
        }
    )

    fields, missing, conflicts, warnings = (
        document_intelligence_service._parse_response(
            raw_response, "BANK_STATEMENT", source_text
        )
    )

    assert fields[field_name].value is not None
    assert not any(
        conflict.field_name == field_name
        and conflict.conflict_type == "CONTRADICTORY_SOURCE_VALUES"
        for conflict in conflicts
    )