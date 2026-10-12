from typing import Any

from backend.app.schemas.customer_communication import (
    AdditionalInformationRequestInput,
    CustomerCommunicationDraft,
    DecisionCommunicationInput,
    SanctionCommunicationInput,
    DisbursementCommunicationInput,
    RepaymentServicingCommunicationInput,
)


class CustomerCommunicationService:
    """Generate customer communication drafts for human review."""

    def generate_additional_information_request(
        self,
        request: AdditionalInformationRequestInput,
    ) -> CustomerCommunicationDraft:
        application_id = request.application_id.strip()
        customer_id = request.customer_id.strip()

        if not application_id:
            raise ValueError("APPLICATION_ID_REQUIRED")

        if not customer_id:
            raise ValueError("CUSTOMER_ID_REQUIRED")

        requested_items = [
            item.strip()
            for item in request.requested_items
            if item and item.strip()
        ]

        if not requested_items:
            raise ValueError("REQUESTED_ITEMS_REQUIRED")

        # Preserve order while removing duplicates.
        requested_items = list(dict.fromkeys(requested_items))

        recipient_name = (
            request.recipient_name.strip()
            if request.recipient_name
            else ""
        )

        greeting = (
            f"Dear {recipient_name},"
            if recipient_name
            else "Dear Customer,"
        )

        item_lines = "\n".join(
            f"{index}. {item}"
            for index, item in enumerate(requested_items, start=1)
        )

        body_parts = [
            greeting,
            "",
            (
                "To continue processing your loan application, "
                "we require the following additional information:"
            ),
            "",
            item_lines,
            "",
            (
                "Please provide the requested information through "
                "the approved and secure submission channel."
            ),
        ]

        contact_instructions = (
            request.contact_instructions.strip()
            if request.contact_instructions
            else ""
        )

        if contact_instructions:
            body_parts.extend(
                [
                    "",
                    contact_instructions,
                ]
            )

        body_parts.extend(
            [
                "",
                (
                    "If any requested item is unavailable or does not "
                    "apply to you, please let your loan officer know."
                ),
                "",
                (
                    "This request is for information-gathering purposes. "
                    "It does not represent a final credit decision or "
                    "a guarantee of loan approval."
                ),
                "",
                "Regards,",
                "Loan Operations Team",
            ]
        )

        return CustomerCommunicationDraft(
            communication_type="ADDITIONAL_INFORMATION_REQUEST",
            application_id=application_id,
            customer_id=customer_id,
            subject=(
                f"Additional Information Required — "
                f"Application {application_id}"
            ),
            body="\n".join(body_parts),
            status="DRAFT_REQUIRES_HUMAN_REVIEW",
            human_approval_required=True,
            sending_enabled=False,
            reviewer_notes=[
                (
                    "Confirm each requested item is supported by the "
                    "applicable underwriting or policy requirements."
                ),
                (
                    "Confirm the recipient, approved secure submission "
                    "channel, and any deadline before sending."
                ),
                (
                    "Obtain authorized human approval before external use."
                ),
            ],
        )

    def generate_decision_communication(
        self,
        request: DecisionCommunicationInput,
    ) -> CustomerCommunicationDraft:
        underwriting = request.underwriting

        # Fail closed if a final decision is unavailable.
        if underwriting.decision is None:
            raise ValueError("UNDERWRITING_DECISION_REQUIRED")

        decision = underwriting.decision.decision

        if decision not in {"APPROVE", "REJECT", "REFER"}:
            raise ValueError("UNDERWRITING_DECISION_REQUIRED")
            
        communication_type = request.communication_type

        # Do not allow a draft type to contradict the actual decision.
        if communication_type == "APPROVAL_COMMUNICATION":
            if decision != "APPROVE":
                raise ValueError(
                    "APPROVAL_DRAFT_REQUIRES_APPROVE_DECISION"
                )

        elif communication_type == "REJECTION_COMMUNICATION":
            if decision != "REJECT":
                raise ValueError(
                    "REJECTION_DRAFT_REQUIRES_REJECT_DECISION"
                )

        else:
            raise ValueError("UNSUPPORTED_COMMUNICATION_TYPE")

        if (
            underwriting.application_id
            != underwriting.decision.application_id
        ):
            raise ValueError("APPLICATION_ID_MISMATCH")

        recipient_name = (
            request.recipient_name.strip()
            if request.recipient_name
            else ""
        )
        greeting = (
            f"Dear {recipient_name},"
            if recipient_name
            else "Dear Customer,"
        )

        if communication_type == "APPROVAL_COMMUNICATION":
            subject = (
                f"Loan Application Update — "
                f"{underwriting.application_id}"
            )
            body = "\n".join(
                [
                    greeting,
                    "",
                    (
                        "We are writing to provide an update on your "
                        "loan application. The current underwriting "
                        "decision is recorded as APPROVE."
                    ),
                    "",
                    (
                        "This message is a draft requiring authorized "
                        "human review. It is not a sanction letter, "
                        "binding offer, or confirmation of disbursement. "
                        "Any applicable terms and next steps will be "
                        "communicated through official documentation."
                    ),
                    "",
                    "Regards,",
                    "Loan Operations Team",
                ]
            )
        else:
            subject = (
                f"Loan Application Update — "
                f"{underwriting.application_id}"
            )
            body = "\n".join(
                [
                    greeting,
                    "",
                    (
                        "We regret to inform you that the current "
                        "underwriting decision for your loan application "
                        "is recorded as REJECT."
                    ),
                    "",
                    (
                        "For information about this outcome or the "
                        "available review process, please contact your "
                        "authorized loan officer through the established "
                        "customer support channel."
                    ),
                    "",
                    (
                        "This message is a draft requiring authorized "
                        "human review and must not be sent before approval."
                    ),
                    "",
                    "Regards,",
                    "Loan Operations Team",
                ]
            )

        return CustomerCommunicationDraft(
            communication_type=communication_type,
            application_id=underwriting.application_id,
            customer_id=underwriting.customer_id,
            subject=subject,
            body=body,
            status="DRAFT_REQUIRES_HUMAN_REVIEW",
            human_approval_required=True,
            sending_enabled=False,
            reviewer_notes=[
                (
                    "Verify the recorded underwriting decision and "
                    "application identifiers before approval."
                ),
                (
                    "Review the wording against applicable customer "
                    "communication and regulatory requirements."
                ),
                (
                    "Obtain authorized human approval before any "
                    "external use."
                ),
            ],
        )

    
    def generate_sanction_communication(
        self,
        request: SanctionCommunicationInput,
        sanction: Any,
    ) -> CustomerCommunicationDraft:
        if sanction is None:
            raise ValueError("SANCTION_NOT_FOUND")

        if sanction.application_id != request.application_id:
            raise ValueError("APPLICATION_ID_MISMATCH")

        if sanction.sanction_status != "APPROVED":
            raise ValueError("SANCTION_NOT_APPROVED")

        recipient = (
            request.recipient_name.strip()
            if request.recipient_name
            else ""
        )
        greeting = f"Dear {recipient}," if recipient else "Dear Customer,"

        terms = [
            f"Approved sanction amount: INR {sanction.sanctioned_amount:,.2f}",
            f"Sanctioned tenure: {sanction.sanctioned_tenure} months",
        ]

        if sanction.sanctioned_emi is not None:
            terms.append(
                f"Recorded monthly installment: INR "
                f"{sanction.sanctioned_emi:,.2f}"
            )

        if sanction.interest_rate is not None:
            terms.append(
                f"Recorded interest rate: {sanction.interest_rate:.2f}%"
            )

        if sanction.expires_at is not None:
            terms.append(
                f"Recorded offer expiry: {sanction.expires_at:%d %B %Y}"
            )

        if sanction.terms_and_conditions:
            terms.extend([
                "",
                "Recorded terms and conditions:",
                sanction.terms_and_conditions,
            ])

        body = "\n".join([
            greeting,
            "",
            "Our records show that a sanction has been approved "
            f"for your loan application {request.application_id}.",
            "",
            *terms,
            "",
            "Please refer to the official sanction documentation "
            "for the complete terms and applicable conditions.",
            "",
            "This is a draft for authorized review and is not a "
            "substitute for the official sanction letter.",
            "",
            "Regards,",
            "Loan Operations Team",
        ])

        return CustomerCommunicationDraft(
            communication_type="SANCTION_COMMUNICATION",
            application_id=request.application_id,
            customer_id=request.customer_id,
            subject=f"Loan Sanction Update — {request.application_id}",
            body=body,
            status="DRAFT_REQUIRES_HUMAN_REVIEW",
            human_approval_required=True,
            sending_enabled=False,
            reviewer_notes=[
                "Verify every term against the persisted approved sanction.",
                "Confirm the official sanction document and recipient.",
                "Obtain authorized human approval before external use.",
            ],
        )

    def generate_disbursement_communication(
        self,
        request: DisbursementCommunicationInput,
        disbursement: Any,
    ) -> CustomerCommunicationDraft:
        if disbursement is None:
            raise ValueError("DISBURSEMENT_NOT_FOUND")

        if disbursement.application_id != request.application_id:
            raise ValueError("APPLICATION_ID_MISMATCH")

        # Only confirm a disbursement with a recorded processed status.
        if disbursement.status != "PROCESSED":
            raise ValueError("DISBURSEMENT_NOT_CONFIRMED")

        recipient = (
            request.recipient_name.strip()
            if request.recipient_name
            else ""
        )
        greeting = f"Dear {recipient}," if recipient else "Dear Customer,"

        processed_date = (
            disbursement.processed_at.strftime("%d %B %Y")
            if disbursement.processed_at
            else None
        )

        body_parts = [
            greeting,
            "",
            "Our records indicate that the disbursement for your "
            f"loan application {request.application_id} has been processed.",
            "",
            f"Recorded disbursement amount: INR "
            f"{disbursement.disbursement_amount:,.2f}",
        ]

        if processed_date:
            body_parts.append(f"Recorded processing date: {processed_date}")

        body_parts.extend([
            "",
            "Please check your designated bank account. If the funds "
            "are not reflected, contact the authorized loan operations "
            "team through the established support channel.",
            "",
            "This is a draft for authorized human review.",
            "",
            "Regards,",
            "Loan Operations Team",
        ])

        return CustomerCommunicationDraft(
            communication_type="DISBURSEMENT_COMMUNICATION",
            application_id=request.application_id,
            customer_id=request.customer_id,
            subject=f"Disbursement Update — {request.application_id}",
            body="\n".join(body_parts),
            status="DRAFT_REQUIRES_HUMAN_REVIEW",
            human_approval_required=True,
            sending_enabled=False,
            reviewer_notes=[
                "Verify the recorded disbursement status and amount.",
                "Confirm the destination and authorized recipient.",
                "Obtain authorized human approval before external use.",
            ],
        )

    def generate_repayment_servicing_communication(
        self,
        request: RepaymentServicingCommunicationInput,
        schedule: Any,
        repayment: Any = None,
    ) -> CustomerCommunicationDraft:
        if schedule is None:
            raise ValueError("REPAYMENT_SCHEDULE_NOT_FOUND")

        if schedule.application_id != request.application_id:
            raise ValueError("APPLICATION_ID_MISMATCH")

        if schedule.repayment_schedule_id != request.repayment_schedule_id:
            raise ValueError("REPAYMENT_SCHEDULE_ID_MISMATCH")

        recipient = (
            request.recipient_name.strip()
            if request.recipient_name
            else ""
        )
        greeting = f"Dear {recipient}," if recipient else "Dear Customer,"

        if schedule.status == "PENDING":
            subject = f"Repayment Schedule Update — {request.application_id}"

            body_parts = [
                greeting,
                "",
                "Our records show that the following installment "
                "is currently marked as pending.",
                "",
                f"Installment number: {schedule.installment_number}",
                f"Recorded due date: {schedule.due_date:%d %B %Y}",
                f"Recorded installment amount: INR {schedule.total_due:,.2f}",
                "",
                "Please use the approved repayment channel and refer "
                "to your official repayment schedule. If you have "
                "already paid, please contact the loan servicing team "
                "to verify the payment.",
            ]

        elif schedule.status == "PAID":
            if repayment is None or repayment.status != "SUCCESS":
                raise ValueError("REPAYMENT_CONFIRMATION_EVIDENCE_MISSING")

            if repayment.repayment_schedule_id != schedule.repayment_schedule_id:
                raise ValueError("REPAYMENT_SCHEDULE_ID_MISMATCH")

            paid_date = (
                repayment.paid_at.strftime("%d %B %Y")
                if repayment.paid_at
                else None
            )

            subject = f"Repayment Confirmation — {request.application_id}"

            body_parts = [
                greeting,
                "",
                "Our records show that payment for the following "
                "repayment schedule has been recorded successfully.",
                "",
                f"Installment number: {schedule.installment_number}",
                f"Recorded payment amount: INR {repayment.repayment_amount:,.2f}",
            ]

            if paid_date:
                body_parts.append(f"Recorded payment date: {paid_date}")

            body_parts.extend([
                "",
                "Please retain this communication for your records. "
                "Contact the loan servicing team if the recorded "
                "payment details appear incorrect.",
            ])

        else:
            raise ValueError("UNSUPPORTED_REPAYMENT_SCHEDULE_STATUS")

        body_parts.extend([
            "",
            "This is a draft for authorized human review.",
            "",
            "Regards,",
            "Loan Servicing Team",
        ])

        return CustomerCommunicationDraft(
            communication_type="REPAYMENT_SERVICING_COMMUNICATION",
            application_id=request.application_id,
            customer_id=request.customer_id,
            subject=subject,
            body="\n".join(body_parts),
            status="DRAFT_REQUIRES_HUMAN_REVIEW",
            human_approval_required=True,
            sending_enabled=False,
            reviewer_notes=[
                "Verify the repayment schedule and persisted payment status.",
                "Confirm the due date or payment record before approval.",
                "Obtain authorized human approval before external use.",
            ],
        )


customer_communication_service = CustomerCommunicationService()