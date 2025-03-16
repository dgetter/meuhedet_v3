import azure.functions as func
import json
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uvicorn

app = FastAPI( title="Classifier (Orchestrator) - Agent",
    description="This is a sample API for Classifier page agent",)

# ---------------------------------------------------------
# Models
# ---------------------------------------------------------
class CardList(BaseModel):
    total_pages: int = Field(default=1, description="Total number of pages available")
    current_page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=1, description="Number of items per page")
    json_content: str = Field(default=None, description="")

class Json_card(BaseModel):
    txt: str = Field(default="...", description="Text description")
    card_list: CardList = Field(default_factory=CardList, description="Contains paginated list of cards")

    class Config:
        arbitrary_types_allowed = True


class RequestMSG(BaseModel):
    request_id: str = Field(example="1", description="Unique request identifier")
    source_system: int = Field(example=46, description="System code (46=Website, 65=Apps)")
    session_id: str = Field(example="xyz-456", description="Session identifier")
    query: str = Field(example="Find nearest hospital", description="User input query")


class Text_card(BaseModel):
    txt: str = Field(example="some text", description="response to user")


class Options_card(BaseModel):
    text: str = Field(example="some text", description="response to user")
    options: List[str] = Field(example=["Hospital A", "Hospital B", "Hospital C"], description="List of options")


class ResponseMSG(BaseModel):
    request_id: str = Field(example="1", description="Unique request identifier")
    source_system: int = Field(example=46, description="System code (46=Website, 65=Apps)")
    session_id: str = Field(example="xyz-456", description="Session identifier")

    next_agent: str = Field(example="Classifier/Agent1/Agent2...", description="the next agent to address")
    card_type: str = Field(example="text/options/json", description="Type of card being returned")
    card_sub_type: str = Field(default="None", example="None/POI/Redirect/Shaban...",
                               description="Subtype when card_type is json")

    text_card: Optional[Text_card] = Field(default=None, description="Text response to the user")
    options_card: Optional[Options_card] = Field(default=None, description="Options list for the user")
    json_card: Optional[Json_card] = Field(default=None, description="JSON structured data")

    # Validators to ensure proper card setup based on card_type
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
            # card_sub_type remains as set
            self.text_card = None
            self.options_card = None


# ---------------------------------------------------------
# Route
# ---------------------------------------------------------
@app.post("/request_json", response_model=ResponseMSG)
def income_request(req: RequestMSG = Body(...)) -> ResponseMSG:
    # Example usage - create a JSON card response with medical institution
    medical_institution = {}

    # Create a CardList with the medical institution
    card_list = CardList(
        total_pages=1,
        current_page=1,
        page_size=1,
        json_content = json.dumps([medical_institution])
    )

    # Create a Json_card with the CardList
    json_card = Json_card(
        txt="Medical institution information",
        card_list=card_list,
        location_longitude=34.7818,
        location_latitude=32.0853
    )

    # Create and return the response
    return ResponseMSG(
        request_id=req.request_id,
        source_system=req.source_system,
        session_id=req.session_id,
        next_agent="Agent1",
        card_type="json",
        card_sub_type="Classifier",
        json_card=json_card
    )

@app.post("/request_text", response_model=ResponseMSG)
# Example of different response types
def create_text_response(req: RequestMSG) -> ResponseMSG:
    return ResponseMSG(
        request_id=req.request_id,
        source_system=req.source_system,
        session_id=req.session_id,
        next_agent="Agent1",
        card_type="text",
        text_card=Text_card(txt="Here is your text response")
    )


@app.post("/request_options", response_model=ResponseMSG)
def create_options_response(req: RequestMSG) -> ResponseMSG:
    return ResponseMSG(
        request_id=req.request_id,
        source_system=req.source_system,
        session_id=req.session_id,
        next_agent="Agent1",
        card_type="options",
        options_card=Options_card(
            text="Please select an option:",
            options=["Option A", "Option B", "Option C"]
        )
    )