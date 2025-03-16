import azure.functions as func
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# Create FastAPI app
app = FastAPI(title="FastAPI Azure Function App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Define a data model
class Item(BaseModel):
    id: int
    name: str
    description: str = None


# Sample data
items = [
    {"id": 1, "name": "Item 1", "description": "Description for Item 1"},
    {"id": 2, "name": "Item 2", "description": "Description for Item 2"}
]


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI on Azure Functions!"}


# Get all items
@app.get("/api/items")
async def get_items():
    return items


# Get a specific item by ID
@app.get("/api/items/{item_id}")
async def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")


# Create a new item
@app.post("/api/items")
async def create_item(item: Item):
    items.append(item.dict())
    return item


# Setup Azure Function
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


# Create an HTTP trigger for Azure Functions
@func.HttpTrigger(
    route="{*route}",  # This captures any route
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    authLevel=func.AuthLevel.ANONYMOUS
)
async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """
    This function processes all HTTP requests and forwards them to FastAPI
    """
    logging.info('Python HTTP trigger function processed a request.')

    # Get the route from the request
    route = req.route_params.get('route')
    logging.info(f"Route: {route}")

    # Get the request method
    method = req.method
    logging.info(f"Method: {method}")

    # Get the request headers
    headers = dict(req.headers)
    logging.info(f"Headers: {headers}")

    # Get the request body
    body = req.get_body() if req.get_body() else b''

    # Process request through FastAPI
    from fastapi.applications import Request

    # Create a FastAPI Request object
    fastapi_request = Request(
        {
            "type": "http",
            "method": method,
            "headers": headers,
            "path": f"/{route}" if route else "/",
            "query_string": req.url.split('?')[1].encode() if '?' in req.url else b'',
            "body": body
        }
    )

    # Process the request through FastAPI
    response = await app.dispatch_request(fastapi_request)

    # Convert response to Azure Functions response
    azure_response = func.HttpResponse(
        body=response.body,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

    return azure_response