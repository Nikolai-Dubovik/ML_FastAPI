from fastapi import FastAPI

app = FastAPI(title="ML Churn Service")


@app.get("/")
def get_message():
    return {"message": "ml churn service is running"}
