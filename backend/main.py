from fastapi import FastAPI

app = FastAPI(
    title="Loan Risk Assessment System",
    description="An AI-powered personal loan risk assessment API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to the Loan Risk Assessment System!",
        "status": "Backend is running successfully"
    }
