import json
import pandas as pd


from .database import Base, engine, get_db
from pydantic import Field
from .models import Applicant, LoanPrediction, LoanProduct
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Literal
from pathlib import Path
from catboost import CatBoostClassifier
from fastapi.middleware.cors import CORSMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Loan Risk Assessment System",
    description="An AI-powered personal loan risk assessment API",
    version="1.0.0"
)

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
    DTIRatio: float

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


#PREDICT

@app.post("/api/v1/predict")
def predict_loan(data: LoanPredictionInput, db=Depends(get_db)):

    input_data = pd.DataFrame([data.model_dump()])

    probability = float(model.predict_proba(input_data)[0][1])

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


@app.get("/api/v1/predictions")
def get_predictions(db=Depends(get_db)):

    predictions = db.query(LoanPrediction).all()

    return {
        "total_predictions": len(predictions),
        "predictions": predictions
    }

@app.get("/api/v1/predictions/{prediction_id}")
def get_prediction(prediction_id: int, db=Depends(get_db)):

    prediction = db.query(LoanPrediction).filter(
        LoanPrediction.id == prediction_id
    ).first()

    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found"
        )

    return prediction


@app.delete("/api/v1/predictions/{prediction_id}")
def delete_prediction(prediction_id: int, db=Depends(get_db)):

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


@app.post("/api/v1/products")
def create_loan_product(data: LoanProductCreate, db=Depends(get_db)):

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

@app.get("/api/v1/products")
def get_loan_products(db=Depends(get_db)):

    products = db.query(LoanProduct).all()

    return {
        "total_products": len(products),
        "products": products
    }

@app.put("/api/v1/products/{product_id}")
def update_loan_product(
    product_id: int,
    data: LoanProductUpdate,
    db=Depends(get_db)
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