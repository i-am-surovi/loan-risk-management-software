
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, func
from .database import Base


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    annual_income = Column(Float, nullable=False)
    loan_amount = Column(Float, nullable=False)
    loan_term_months = Column(Integer, nullable=False)
    employment_years = Column(Float, nullable=False)
    existing_monthly_debt = Column(Float, nullable=False)
    credit_history_years = Column(Float, nullable=False)
    previous_defaults = Column(Integer, nullable=False)
    previous_loan_count = Column(Integer, nullable=False)


class LoanPrediction(Base):
    __tablename__ = "loan_predictions"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer, nullable=False)
    income = Column(Float, nullable=False)
    loan_amount = Column(Float, nullable=False)
    credit_score = Column(Integer, nullable=False)
    default_probability = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    prediction = Column(Integer, nullable=False)
    risk = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )


class LoanProduct(Base):
    __tablename__ = "loan_products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, unique=True)
    annual_interest_rate = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
