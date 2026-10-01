from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.fraud_features import FraudFeatures


class FraudFeatureEngineeringService:

    def build_features(
        self,
        borrower: Borrower360,
    ) -> FraudFeatures:

        features = FraudFeatures()

        # --------------------------------------------------
        # Identity
        # --------------------------------------------------

        if borrower.kyc is not None:
            features.identity_data_available = 1

            # Development placeholder:
            # No identity mismatch source is currently available.
            features.identity_mismatch_flag = 0

        else:
            features.identity_data_available = 0
            features.identity_mismatch_flag = None

        # --------------------------------------------------
        # Device
        # --------------------------------------------------

        if borrower.device_behaviour is not None:

            features.device_data_available = 1

            velocity = borrower.device_behaviour.velocity

            if velocity is not None:

                applications_24h = velocity.get(
                    "applications_last_24h"
                )

                if applications_24h is not None:
                    features.device_velocity = applications_24h

            session_patterns = (
                borrower.device_behaviour.session_patterns
            )

            if session_patterns is not None:

                multiple_devices = session_patterns.get(
                    "multiple_devices"
                )

                if multiple_devices is not None:
                    features.multiple_device_flag = (
                        1 if multiple_devices else 0
                    )

        else:

            features.device_data_available = 0
            features.multiple_device_flag = None
            features.device_velocity = None

        # --------------------------------------------------
        # Transaction
        # --------------------------------------------------

        if borrower.bank_cash_flow is not None:

            transaction_count = (
                borrower.bank_cash_flow.transaction_count
            )

            if transaction_count is not None:
                features.transaction_data_available = 1

                # Development placeholder.
                # Actual transaction velocity requires
                # a defined observation window.
                features.transaction_velocity = None

            else:
                features.transaction_data_available = 0

        else:

            features.transaction_data_available = 0

        features.transaction_anomaly_flag = 0

        # --------------------------------------------------
        # Documents
        # --------------------------------------------------

        if borrower.documents is not None:

            features.document_data_available = 1

            # No document anomaly detector implemented yet.
            features.document_anomaly_flag = 0

        else:

            features.document_data_available = 0
            features.document_anomaly_flag = None

        # --------------------------------------------------
        # Behaviour
        # --------------------------------------------------

        if borrower.device_behaviour is not None:

            session_patterns = (
                borrower.device_behaviour.session_patterns
            )

            if session_patterns is not None:

                features.behavioural_data_available = 1

                # No session anomaly model implemented yet.
                features.session_anomaly_flag = 0

            else:

                features.behavioural_data_available = 0
                features.session_anomaly_flag = None

        else:

            features.behavioural_data_available = 0
            features.session_anomaly_flag = None

        return features


fraud_feature_engineering_service = FraudFeatureEngineeringService()