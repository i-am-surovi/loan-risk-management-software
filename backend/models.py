
from sqlalchemy import Column, Integer, Float
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
