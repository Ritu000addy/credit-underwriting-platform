from sqlalchemy.orm import Session

from backend.app.models.customer import Customer


class CustomerService:

    def create_customer(
        self,
        db: Session,
        customer_id: str,
        kyc_status: str | None = None,
        pan: str | None = None,
        aadhaar_reference: str | None = None,
        aadhaar_kyc_status: str | None = None,
        dob=None,
        address: str | None = None,
    ):
        existing_customer = db.get(
            Customer,
            customer_id,
        )

        if existing_customer is not None:
            raise ValueError(
                "Customer already exists."
            )

        customer = Customer(
            customer_id=customer_id,
            kyc_status=kyc_status,
            pan=pan,
            aadhaar_reference=aadhaar_reference,
            aadhaar_kyc_status=aadhaar_kyc_status,
            dob=dob,
            address=address,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        return customer


customer_service = CustomerService()