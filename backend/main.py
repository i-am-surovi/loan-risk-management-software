
import json
import pandas as pd

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from catboost import CatBoostClassifier

from .database import Base, engine, get_db
from .models import Applicant, LoanPrediction, LoanProduct


# Create database tables
Base.metadata.create_all(bind=engine)


# Initialize FastAPI
app = FastAPI(
    title="Loan Risk Assessment System",
    description="An AI-powered personal loan risk assessment API",
    version="1.0.0"
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load trained CatBoost model
BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml" / "models" / "catboost_model.cbm"

model = CatBoostClassifier()
model.load_model(str(MODEL_PATH))


# Load selected threshold
THRESHOLD_PATH = BASE_DIR / "ml" / "models" / "threshold.json"

with open(THRESHOLD_PATH, "r") as file:
    threshold_data = json.load(file)

BEST_THRESHOLD = threshold_data["threshold"]


# Model features in training order
MODEL_FEATURES = [
    "Age",
    "Income",
    "LoanAmount",
    "CreditScore",
    "MonthsEmployed",
    "NumCreditLines",
    "InterestRate",
    "LoanTerm",
    "Education",
    "EmploymentType",
    "MaritalStatus",
    "HasMortgage",
    "HasDependents",
    "LoanPurpose",
    "HasCoSigner"
]


# =========================
# PYDANTIC SCHEMAS
# =========================

class LoanApplicant(BaseModel):
    annual_income: float = Field(gt=0)
    loan_amount: float = Field(gt=0)
    loan_term_months: int = Field(gt=0)
    employment_years: float = Field(ge=0)
    existing_monthly_debt: float = Field(ge=0)
    credit_history_years: float = Field(ge=0)
    previous_defaults: int = Field(ge=0)
    previous_loan_count: int = Field(ge=0)


class LoanPredictionInput(BaseModel):
    Age: int
    Income: int
    LoanAmount: int
    CreditScore: int
    MonthsEmployed: int
    NumCreditLines: int
    InterestRate: float
    LoanTerm: int

    Education: Literal["Bachelor's", "High School", "Master's", "PhD"]
    EmploymentType: Literal["Full-time", "Part-time", "Self-employed", "Unemployed"]
    MaritalStatus: Literal["Divorced", "Married", "Single"]
    HasMortgage: Literal["No", "Yes"]
    HasDependents: Literal["No", "Yes"]
    LoanPurpose: Literal["Auto", "Business", "Education", "Home", "Other"]
    HasCoSigner: Literal["No", "Yes"]


class LoanProductCreate(BaseModel):
    product_name: str
    annual_interest_rate: float


class LoanProductUpdate(BaseModel):
    annual_interest_rate: float


class LoanCalculationInput(BaseModel):
    product_id: int
    annual_income: float = Field(gt=0)
    loan_amount: float = Field(gt=0)
    loan_term_months: int = Field(gt=0)
    existing_monthly_debt: float = Field(ge=0)


# =========================
# HOME API
# =========================

@app.get("/")
def home():
    return {
        "message": "Welcome to the Loan Risk Assessment System!",
        "status": "Backend is running successfully"
    }


# =========================
# APPLICANT CRUD
# =========================

# CREATE
@app.post("/api/v1/applicants/validate")
def validate_applicant(
    applicant: LoanApplicant,
    db: Session = Depends(get_db)
):
    try:
        new_applicant = Applicant(**applicant.model_dump())

        db.add(new_applicant)
        db.commit()
        db.refresh(new_applicant)

        return {
            "message": "Applicant information saved successfully!",
            "applicant_id": new_applicant.id,
            "applicant_data": applicant.model_dump()
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save applicant information."
        )


# READ ALL
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


# READ SINGLE
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


# =========================
# AI LOAN PREDICTION
# =========================

@app.post("/api/v1/predict")
def predict_loan(
    data: LoanPredictionInput,
    db: Session = Depends(get_db)
):

    # Prepare model input in training feature order
    input_data = pd.DataFrame(
        [data.model_dump()],
        columns=MODEL_FEATURES
    )

    # Predict default probability
    probability = float(
        model.predict_proba(input_data)[0][1]
    )

    # Apply selected threshold
    prediction = int(probability >= BEST_THRESHOLD)

    risk = "High Risk" if prediction == 1 else "Low Risk"

    # Save prediction to database
    new_prediction = LoanPrediction(
        age=data.Age,
        income=data.Income,
        loan_amount=data.LoanAmount,
        credit_score=data.CreditScore,
        default_probability=probability,
        threshold=BEST_THRESHOLD,
        prediction=prediction,
        risk=risk
    )

    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)

    return {
        "id": new_prediction.id,
        "default_probability": round(probability, 4),
        "threshold": BEST_THRESHOLD,
        "prediction": prediction,
        "risk": risk,
        "message": "Prediction saved successfully"
    }



# =========================
# PREDICTION HISTORY
# =========================

@app.get("/api/v1/predictions")
def get_predictions(db: Session = Depends(get_db)):

    predictions = (
        db.query(LoanPrediction)
        .order_by(LoanPrediction.created_at.desc())
        .all()
    )

    return {
        "total_predictions": len(predictions),
        "predictions": [
            {
                "id": item.id,
                "age": item.age,
                "income": item.income,
                "loan_amount": item.loan_amount,
                "credit_score": item.credit_score,
                "default_probability": item.default_probability,
                "threshold": item.threshold,
                "prediction": item.prediction,
                "risk": item.risk,
                "created_at": item.created_at.isoformat()
                if item.created_at else None
            }
            for item in predictions
        ]
    }


@app.get("/api/v1/predictions/{prediction_id}")
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):

    prediction = db.query(LoanPrediction).filter(
        LoanPrediction.id == prediction_id
    ).first()

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found"
        )

    return {
        "id": prediction.id,
        "age": prediction.age,
        "income": prediction.income,
        "loan_amount": prediction.loan_amount,
        "credit_score": prediction.credit_score,
        "default_probability": prediction.default_probability,
        "threshold": prediction.threshold,
        "prediction": prediction.prediction,
        "risk": prediction.risk,
        "created_at": prediction.created_at.isoformat()
        if prediction.created_at else None
    }


@app.delete("/api/v1/predictions/{prediction_id}")
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db)
):

    prediction = db.query(LoanPrediction).filter(
        LoanPrediction.id == prediction_id
    ).first()

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found"
        )

    db.delete(prediction)
    db.commit()

    return {
        "message": "Prediction deleted successfully",
        "id": prediction_id
    }


# =========================
# LOAN PRODUCT MANAGEMENT
# =========================

# CREATE PRODUCT
@app.post("/api/v1/products")
def create_loan_product(
    data: LoanProductCreate,
    db: Session = Depends(get_db)
):

    existing_product = db.query(LoanProduct).filter(
        LoanProduct.product_name == data.product_name
    ).first()

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Loan product already exists"
        )

    new_product = LoanProduct(
        product_name=data.product_name,
        annual_interest_rate=data.annual_interest_rate,
        is_active=True
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "message": "Loan product created successfully",
        "id": new_product.id,
        "product_name": new_product.product_name,
        "annual_interest_rate": new_product.annual_interest_rate,
        "is_active": new_product.is_active
    }


# READ PRODUCTS
@app.get("/api/v1/products")
def get_loan_products(db: Session = Depends(get_db)):

    products = db.query(LoanProduct).all()

    return {
        "total_products": len(products),
        "products": products
    }


# UPDATE PRODUCT
@app.put("/api/v1/products/{product_id}")
def update_loan_product(
    product_id: int,
    data: LoanProductUpdate,
    db: Session = Depends(get_db)
):

    product = db.query(LoanProduct).filter(
        LoanProduct.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Loan product not found"
        )

    if data.annual_interest_rate <= 0:
        raise HTTPException(
            status_code=400,
            detail="Interest rate must be greater than 0"
        )

    product.annual_interest_rate = data.annual_interest_rate

    db.commit()
    db.refresh(product)

    return {
        "message": "Loan product updated successfully",
        "id": product.id,
        "product_name": product.product_name,
        "annual_interest_rate": product.annual_interest_rate,
        "is_active": product.is_active
    }


# =========================
# EMI AND DTI CALCULATOR
# =========================

@app.post("/api/v1/calculate-loan")
def calculate_loan(
    data: LoanCalculationInput,
    db: Session = Depends(get_db)
):

    # Find selected active loan product
    product = db.query(LoanProduct).filter(
        LoanProduct.id == data.product_id,
        LoanProduct.is_active == True
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Active loan product not found"
        )

    # Convert annual interest rate to monthly rate
    monthly_rate = product.annual_interest_rate / 100 / 12

    principal = data.loan_amount
    months = data.loan_term_months

    # Calculate monthly EMI
    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = (
            principal
            * monthly_rate
            * (1 + monthly_rate) ** months
            / ((1 + monthly_rate) ** months - 1)
        )

    # Calculate DTI
    monthly_income = data.annual_income / 12

    total_monthly_debt = data.existing_monthly_debt + emi

    dti_ratio = total_monthly_debt / monthly_income
    dti_percentage = dti_ratio * 100

    return {
        "product_name": product.product_name,
        "annual_interest_rate": product.annual_interest_rate,
        "monthly_income": round(monthly_income, 2),
        "monthly_installment": round(emi, 2),
        "existing_monthly_debt": data.existing_monthly_debt,
        "total_monthly_debt": round(total_monthly_debt, 2),
        "dti_ratio": round(dti_ratio, 4),
        "dti_percentage": round(dti_percentage, 2)
    }
