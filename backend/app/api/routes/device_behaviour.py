from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.device_behaviour import (
    DeviceBehaviourCreate,
    DeviceBehaviourResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.device_behaviour_service import (
    device_behaviour_service,
)


router = APIRouter(
    prefix="/device-behaviour",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[DeviceBehaviourResponse],
)
def create_device_behaviour(
    device_behaviour: DeviceBehaviourCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    result = device_behaviour_service.create_device_behaviour(
        db=db,
        device_behaviour=device_behaviour,
    )

    response_data = DeviceBehaviourResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Device / behaviour data created successfully.",
    )