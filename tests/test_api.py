import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path so we can import function_app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from function_app import app

# Create test client
client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI on Azure Functions!"}

def test_get_items():
    response = client.get("/api/items")
    assert response.status_code == 200
    assert len(response.json()) >= 2  # At least 2 items in the sample data

def test_get_item():
    response = client.get("/api/items/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_item_not_found():
    response = client.get("/api/items/999")
    assert response.status_code == 404

def test_create_item():
    new_item = {
        "id": 3,
        "name": "Test Item",
        "description": "Created during tests"
    }
    response = client.post("/api/items", json=new_item)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"