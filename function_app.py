import azure.functions as func
import logging
import json
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional

# -----------------------
# Pydantic Models
# -----------------------
class CardList(BaseModel):
    total_pages: int = Field(default=1, description="Total number of pages available")
    current_page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=1, description="Number of items per page")
    json_content: str = Field(default=None, description="")

class Json_card(BaseModel):
    txt: str = Field(default="...", description="Text description")
    card_list: CardList = Field(default_factory=CardList, description="Contains paginated list of cards")
    location_longitude: Optional[float] = Field(default=None, description="Longitude of the location")
    location_latitude: Optional[float] = Field(default=None, description="Latitude of the location")
    
    class Config:
        arbitrary_types_allowed = True

class RequestMSG(BaseModel):
    request_id: str = Field(example="1", description="Unique request identifier")
    source_system: int = Field(example=46, description="System code (46=Website, 65=Apps)")
    session_id: str = Field(example="xyz-456", description="Session identifier")
    query: str = Field(example="Find nearest hospital", description="User input query")

class Text_card(BaseModel):
    txt: str = Field(example="some text", description="Response to user")

class Options_card(BaseModel):
    text: str = Field(example="some text", description="Response to user")
    options: List[str] = Field(example=["Hospital A", "Hospital B", "Hospital C"], description="List of options")

class ResponseMSG(BaseModel):
    request_id: str = Field(example="1", description="Unique request identifier")
    source_system: int = Field(example=46, description="System code (46=Website, 65=Apps)")
    session_id: str = Field(example="xyz-456", description="Session identifier")
    next_agent: str = Field(example="Classifier/Agent1/Agent2...", description="The next agent to address")
    card_type: str = Field(example="text/options/json", description="Type of card being returned")
    card_sub_type: str = Field(default="None", example="None/POI/Redirect/Shaban...", description="Subtype when card_type is json")
    text_card: Optional[Text_card] = Field(default=None, description="Text response to the user")
    options_card: Optional[Options_card] = Field(default=None, description="Options list for the user")
    json_card: Optional[Json_card] = Field(default=None, description="JSON structured data")

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure only the relevant card is populated based on card_type
        if self.card_type == "text":
            if self.text_card is None:
                self.text_card = Text_card(txt="")
            self.options_card = None
            self.json_card = None
            self.card_sub_type = "Classifier"
        elif self.card_type == "options":
            if self.options_card is None:
                self.options_card = Options_card(text="", options=[])
            self.text_card = None
            self.json_card = None
            self.card_sub_type = "Classifier"
        elif self.card_type == "json":
            if self.json_card is None:
                self.json_card = Json_card()
            self.text_card = None
            self.options_card = None

# -----------------------
# Response Builders
# -----------------------
def create_json_response(request_data: RequestMSG) -> ResponseMSG:
    """Generate JSON response similar to /request_json in FastAPI"""
    # For example purposes, using an empty dict for medical institution.
    medical_institution = {}

    card_list = CardList(
        total_pages=1,
        current_page=1,
        page_size=1,
        json_content=json.dumps([medical_institution])
    )

    json_card = Json_card(
        txt="Medical institution information",
        card_list=card_list,
        location_longitude=34.7818,
        location_latitude=32.0853
    )

    return ResponseMSG(
        request_id=request_data.request_id,
        source_system=request_data.source_system,
        session_id=request_data.session_id,
        next_agent="Agent1",
        card_type="json",
        card_sub_type="Classifier",
        json_card=json_card
    )

def create_text_response(request_data: RequestMSG) -> ResponseMSG:
    """Generate text response similar to /request_text in FastAPI"""
    return ResponseMSG(
        request_id=request_data.request_id,
        source_system=request_data.source_system,
        session_id=request_data.session_id,
        next_agent="Agent1",
        card_type="text",
        text_card=Text_card(txt="Here is your text response")
    )

def create_options_response(request_data: RequestMSG) -> ResponseMSG:
    """Generate options response similar to /request_options in FastAPI"""
    return ResponseMSG(
        request_id=request_data.request_id,
        source_system=request_data.source_system,
        session_id=request_data.session_id,
        next_agent="Agent1",
        card_type="options",
        options_card=Options_card(
            text="Please select an option:",
            options=["Option A", "Option B", "Option C"]
        )
    )

# -----------------------
# Azure Function App
# -----------------------
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="classifier_endpoint", methods=["POST"])
def classifier_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing request for classifier endpoint.")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON format"}),
            status_code=400,
            mimetype="application/json"
        )

    # Validate the incoming payload using the RequestMSG model.
    try:
        request_data = RequestMSG.parse_obj(req_body)
    except ValidationError as e:
        return func.HttpResponse(
            json.dumps({"error": "Payload validation error", "details": e.errors()}),
            status_code=400,
            mimetype="application/json"
        )

    query_type = request_data.query.lower()

    # Choose the response type based on the "query" value.
    if query_type == "json":
        response_model = create_json_response(request_data)
    elif query_type == "text":
        response_model = create_text_response(request_data)
    elif query_type == "options":
        response_model = create_options_response(request_data)
    else:
        return func.HttpResponse(
            json.dumps({"error": "Invalid query type. Use 'json', 'text', or 'options'."}),
            status_code=400,
            mimetype="application/json"
        )

    # Serialize the Pydantic model to JSON.
    response_json = response_model.json()
    return func.HttpResponse(response_json, status_code=200, mimetype="application/json")
