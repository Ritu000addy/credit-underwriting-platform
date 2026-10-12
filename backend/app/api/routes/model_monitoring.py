from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session 

from backend.app.core.responses import success_response 

from backend.app.database import get_db 

from backend.app.models.credit_decision import CreditDecision

router = APIRouter(
    prefix= "/model-monitoring",
    tags= ["Model Monitoring"],
)

@router.get("/summary")
def get_model_monitoring_summary(
    api_request: Request,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            CreditDecision.model_version.label("model_version"),
            CreditDecision.decision.label("decision"),
            CreditDecision.risk_segment.label("risk_segment"),
            CreditDecision.execution_environment.label(
                "execution_environment"
            ),
            CreditDecision.record_source.label("record_source"),
            func.count(CreditDecision.decision_id).label("count"),
            func.avg(
                CreditDecision.probability_of_default
            ).label("average_pd"),
            func.count(
                CreditDecision.probability_of_default
            ).label("pd_available"),
            func.avg(
                CreditDecision.confidence
            ).label("average_confidence"),
            func.count(
                CreditDecision.confidence
            ).label("confidence_available"),
        )
        .group_by(
            CreditDecision.model_version,
            CreditDecision.decision,
            CreditDecision.risk_segment,
            CreditDecision.execution_environment,
            CreditDecision.record_source,
        )
        .order_by(
            CreditDecision.model_version,
            CreditDecision.decision,
            CreditDecision.risk_segment,
            CreditDecision.execution_environment,
            CreditDecision.record_source,
        )
        .all()
    )

    summary = {}

    for row in rows:
        model_version = row.model_version or "UNKNOWN"

        if model_version not in summary:
            summary[model_version] = {
                "total_decisions": 0,
                "decision_counts": {},
                "risk_segment_counts": {},
                "execution_environment_counts": {},
                "record_source_counts": {},
                "average_probability_of_default": None,
                "average_confidence": None,
                "confidence_available": 0,
                "confidence_missing": 0,
                "confidence_coverage_percentage": 0.0,
                "_pd_weighted_sum": 0.0,
                "_pd_count": 0,
                "_confidence_weighted_sum": 0.0,
            }

        item = summary[model_version]
        count = row.count

        item["total_decisions"] += count
        item["decision_counts"][row.decision] = (
            item["decision_counts"].get(row.decision, 0) + count
        )

        segment = row.risk_segment or "UNKNOWN"
        item["risk_segment_counts"][segment] = (
            item["risk_segment_counts"].get(segment, 0) + count
        )

        environment = (
            row.execution_environment or "NOT_RECORDED"
        )
        item["execution_environment_counts"][environment] = (
            item["execution_environment_counts"].get(environment, 0)
            + count
        )

        source = row.record_source or "NOT_RECORDED"
        item["record_source_counts"][source] = (
            item["record_source_counts"].get(source, 0) + count
        )

        if row.average_pd is not None:
            item["_pd_weighted_sum"] += float(row.average_pd) * row.pd_available
            item["_pd_count"] += row.pd_available

        if row.average_confidence is not None:
            item["_confidence_weighted_sum"] += (
                float(row.average_confidence) * row.confidence_available
            )
            item["confidence_available"] += row.confidence_available
        
        item["confidence_missing"] += (
            count - row.confidence_available
        )
    
    
    for item in summary.values():
        if item["_pd_count"]:
            item["average_probability_of_default"] = round(
                item["_pd_weighted_sum"] / item["_pd_count"], 
                6,
            )

        if item["confidence_available"]:
            item["average_confidence"] = round(
                item["_confidence_weighted_sum"] 
                / item["confidence_available"],
                6,
            )
        
        if item["total_decisions"]:
            item["confidence_coverage_percentage"] = round(
                item["confidence_available"]
                / item["total_decisions"]
                * 100,
                2,
            )

        del item["_pd_weighted_sum"]
        del item["_pd_count"]
        del item["_confidence_weighted_sum"]

    return success_response(
        request=api_request,
        data={"models": summary},
        message="Model monitoring summary retrieved successfully.",
    )