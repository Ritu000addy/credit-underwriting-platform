import uuid

from fastapi import Request


def get_request_id(request: Request) -> str:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id:
        return request_id

    request_id = (
        f"REQ-{uuid.uuid4().hex[:12].upper()}"
    )

    request.state.request_id = request_id

    return request_id