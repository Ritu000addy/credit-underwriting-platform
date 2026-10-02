import os
import requests

from dotenv import load_dotenv

from backend.app.schemas.aadhaar_kyc import AadhaarKYCResponse


load_dotenv()


class AadhaarKYCService:

    def __init__(self):
        self.base_url = os.getenv(
            "IDTO_BASE_URL",
            "",
        ).rstrip("/")

        self.client_id = os.getenv(
            "IDTO_CLIENT_ID",
            "",
        )

        self.api_key = os.getenv(
            "IDTO_API_KEY",
            "",
        )

        self.timeout_seconds = int(
            os.getenv(
                "IDTO_TIMEOUT_SECONDS",
                "30",
            )
        )

    def _headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "x-client-id": self.client_id,
            "x-api-key": self.api_key,
        }

    def send_otp(
        self,
        aadhaar_number: str,
        user_consent: bool,
        user_id: str | None = None,
        workflow_session_token: str | None = None,
    ) -> AadhaarKYCResponse:
        
        if not self.base_url:
            raise RuntimeError(
                "IDTO_BASE_URL is not configured."
            )

        if not self.client_id:
            raise RuntimeError(
                "IDTO_CLIENT_ID is not configured."
            )

        if not self.api_key:
            raise RuntimeError(
                "IDTO_API_KEY is not configured."
            )

        if len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            raise ValueError(
                "Aadhaar number must contain exactly 12 digits."
            )

        url = (
            f"{self.base_url}"
            "/v2/verify/okyc_generate_otp"
        )

        payload = {
            "aadhaar_number": aadhaar_number,
            "user_consent": user_consent,
            #"user_id": user_id,
            #"workflow_session_token": workflow_session_token,
        }

        if user_id is not None:
            payload["user_id"] = user_id

        if workflow_session_token is not None:
            payload["workflow_session_token"] = workflow_session_token

        response = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )

        try:
            response_data = response.json()
        except ValueError:
            response_data = {}

        if response.status_code >= 400:
            error_code = response_data.get(
                "error_code"
            )

            raise RuntimeError(
                f"idto.ai Send OTP failed "
                f"with HTTP {response.status_code}: "
                f"{error_code or response.text}"
            )

        error_code = response_data.get("error_code")
        data = response_data.get("data") or {}

        if error_code is None:
            kyc_status = "OTP_SENT"
        else:
            kyc_status = "FAILED"

        return AadhaarKYCResponse(
            status=response_data.get(
                "status",
                "UNKNOWN",
            ),
            transaction_id=response_data.get(
                "tranx_id"
            ),
            kyc_status=kyc_status,
            session_id=data.get(
                "session_id"
            ),
            masked_aadhaar=(
                f"XXXX-XXXX-{aadhaar_number[-4:]}"
            ),
            error_code=error_code,
            error_message=response_data.get(
                "message"
            ),
        )

    def verify_otp(
        self,
        session_id: str,
        otp: str,
        user_id: str | None = None,
        workflow_session_token: str | None = None,
    ) -> AadhaarKYCResponse:

        if not self.base_url:
            raise RuntimeError(
                "IDTO_BASE_URL is not configured."
            )

        if not self.client_id:
            raise RuntimeError(
                "IDTO_CLIENT_ID is not configured."
            )

        if not self.api_key:
            raise RuntimeError(
                "IDTO_API_KEY is not configured."
            )

        if not session_id:
            raise ValueError(
                "Session ID is required."
            )

        if not otp:
            raise ValueError(
                "OTP is required."
            )

        url = (
            f"{self.base_url}"
            "/v2/verify/okyc_get_result"
        )

        payload = {
            "session_id": session_id,
            "otp": otp,
            "user_id": user_id,
            "workflow_session_token": workflow_session_token,
        }

        response = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )

        try:
            response_data = response.json()
        except ValueError:
            response_data = {}

        if response.status_code >= 400:
            error_code = response_data.get(
                "error_code"
            )
            raise RuntimeError(
                f"idto.ai Verify OTP failed "
                f"with HTTP {response.status_code}: "
                f"{error_code or response.text}"
            )

        error_code = response_data.get("error_code")
        data = response_data.get("data")

        if (
            response_data.get("status") == "success"
            and error_code is None
            and data
        ):
            kyc_status = "VERIFIED"
        else:
            kyc_status = "FAILED"

        data = data or {}

        return AadhaarKYCResponse(
            status=response_data.get(
                "status",
                "UNKNOWN",
            ),
            transaction_id=response_data.get(
                "tranx_id"
            ),
            kyc_status=kyc_status,
            session_id=session_id,

            name=data.get("name"),
            dob=data.get("dob"),
            gender=data.get("gender"),

            address=data.get("address"),

            care_of=data.get("care_of"),
            house=data.get("house"),
            street=data.get("street"),
            landmark=data.get("landmark"),
            locality=data.get("locality"),
            district=data.get("district"),
            sub_district=data.get("sub-district"),
            state=data.get("state"),
            pincode=data.get("pincode"),
            post_office=data.get("post_office"),

            has_photo=data.get("has_photo"),
            photo=data.get("photo"),

            error_code=(
                str(error_code) if error_code is not None else None
            ),
            error_message=response_data.get(
                "message"
            ),
        )

aadhaar_kyc_service = AadhaarKYCService()