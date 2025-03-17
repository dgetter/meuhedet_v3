import azure.functions as func
from fastapi import FastAPI
import logging

# Create FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI in Azure Functions"}

@app.post("/classifier_endpoint")
def classifier_endpoint(data: dict):
    name = data.get("name", "Guest")
    return {"message": f"Hello, {name}. This HTTP triggered function executed successfully."}

# Wrap FastAPI app in Azure Functions
function_app = func.AsgiFunctionApp(app=app, http_auth_level=func.AuthLevel.ANONYMOUS)
