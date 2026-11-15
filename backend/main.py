
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .models import Applicant

app = FastAPI(
    title="Loan Risk Assessment System",
    description="An AI-powered personal loan risk assessment API",
    version="1.0.0"
)


class LoanApplicant(BaseModel):
    annual_income: float = Field(gt=0)
    loan_amount: float = Field(gt=0)
    loan_term_months: int = Field(gt=0)
    employment_years: float = Field(ge=0)
    existing_monthly_debt: float = Field(ge=0)
    credit_history_years: float = Field(ge=0)
    previous_defaults: int = Field(ge=0)
    previous_loan_count: int = Field(ge=0)


@app.get("/")
def home():
    return {
        "message": "Welcome to the Loan Risk Assessment System!",
        "status": "Backend is running successfully"
    }

# CRUD Operation

# CREATE
@app.post("/api/v1/applicants/validate")
def validate_applicant(
    applicant: LoanApplicant,
    db: Session = Depends(get_db)
):
    try:
        # Convert validated data into database model
        new_applicant = Applicant(**applicant.model_dump())

        # Save applicant to PostgreSQL
        db.add(new_applicant)
        db.commit()
        db.refresh(new_applicant)

        return {
            "message": "Applicant information saved successfully!",
            "applicant_id": new_applicant.id,
            "applicant_data": applicant.model_dump()
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save applicant information."
        )

# READ
@app.get("/api/v1/applicants")
def get_applicants(db: Session = Depends(get_db)):
    applicants = db.query(Applicant).all()

    return {
        "total_applicants": len(applicants),
        "applicants": [
            {
                "id": applicant.id,
                "annual_income": applicant.annual_income,
                "loan_amount": applicant.loan_amount,
                "loan_term_months": applicant.loan_term_months,
                "employment_years": applicant.employment_years,
                "existing_monthly_debt": applicant.existing_monthly_debt,
                "credit_history_years": applicant.credit_history_years,
                "previous_defaults": applicant.previous_defaults,
                "previous_loan_count": applicant.previous_loan_count
            }
            for applicant in applicants
        ]
    }



@app.get("/api/v1/applicants/{applicant_id}")
def get_applicant(
    applicant_id: int,
    db: Session = Depends(get_db)
):
    applicant = db.query(Applicant).filter(
        Applicant.id == applicant_id
    ).first()

    if not applicant:
        raise HTTPException(
            status_code=404,
            detail="Applicant not found."
        )

    return {
        "id": applicant.id,
        "annual_income": applicant.annual_income,
        "loan_amount": applicant.loan_amount,
        "loan_term_months": applicant.loan_term_months,
        "employment_years": applicant.employment_years,
        "existing_monthly_debt": applicant.existing_monthly_debt,
        "credit_history_years": applicant.credit_history_years,
        "previous_defaults": applicant.previous_defaults,
        "previous_loan_count": applicant.previous_loan_count
    }

# UPDATE
@app.put("/api/v1/applicants/{applicant_id}")
def update_applicant(
    applicant_id: int,
    applicant_data: LoanApplicant,
    db: Session = Depends(get_db)
):
    applicant = db.query(Applicant).filter(
        Applicant.id == applicant_id
    ).first()

    if not applicant:
        raise HTTPException(
            status_code=404,
            detail="Applicant not found."
        )

    for key, value in applicant_data.model_dump().items():
        setattr(applicant, key, value)

    db.commit()
    db.refresh(applicant)

    return {
        "message": "Applicant updated successfully!",
        "applicant_id": applicant.id
    }


# DELETE
@app.delete("/api/v1/applicants/{applicant_id}")
def delete_applicant(
    applicant_id: int,
    db: Session = Depends(get_db)
):
    applicant = db.query(Applicant).filter(
        Applicant.id == applicant_id
    ).first()

    if not applicant:
        raise HTTPException(
            status_code=404,
            detail="Applicant not found."
        )

    db.delete(applicant)
    db.commit()

    return {
        "message": "Applicant deleted successfully!",
        "applicant_id": applicant_id
    }

