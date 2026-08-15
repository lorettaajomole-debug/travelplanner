import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging to write to terminal/stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

app = FastAPI(title="Travel Planner Expert Chatbot")

# Pydantic models for input validation
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# Verbatim system prompt
SYSTEM_PROMPT = (
    "You are a friendly, well-traveled trip-planning expert. You help people plan trips - "
    "suggesting destinations, day-by-day itineraries, things to do, rough budgeting, and "
    "packing tips - in clear, practical language tailored to their interests, budget, dates, "
    "and travel style. Ask clarifying questions when useful, such as who is going, the budget, "
    "the season, and the preferred pace. Remind users to verify time-sensitive details "
    "themselves - visas, opening hours, prices, weather, and safety or travel advisories - "
    "since these change and you may not have current information. Be enthusiastic but realistic."
)

def get_openai_client_or_raise():
    """
    Validates configuration environment variables and returns (client, deployment).
    Raises HTTPException 500 if missing configuration.
    """
    endpoint = os.environ.get("AZURE_ENDPOINT")
    deployment = os.environ.get("AZURE_DEPLOYMENT")
    api_key = os.environ.get("AZURE_API_KEY")

    missing = []
    if not endpoint or endpoint.strip() == "" or "your-resource" in endpoint:
        missing.append("AZURE_ENDPOINT")
    if not deployment or deployment.strip() == "":
        missing.append("AZURE_DEPLOYMENT")
    if not api_key or api_key.strip() == "" or "paste-your-key-here" in api_key:
        missing.append("AZURE_API_KEY")

    if missing:
        err_msg = f"Configuration error: Missing environment variables: {', '.join(missing)}"
        logger.error(err_msg)
        raise HTTPException(
            status_code=500,
            detail=err_msg
        )

    # Initialize client
    client = OpenAI(
        base_url=endpoint,
        api_key=api_key
    )
    return client, deployment

@app.get("/")
async def get_index():
    """
    Serves the chat UI HTML page.
    """
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html file not found")
    return FileResponse(index_path)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Receives chat messages history, prepends system prompt, and calls Azure OpenAI endpoint.
    """
    # 1. Validate environment configuration
    client, deployment = get_openai_client_or_raise()

    # 2. Build full conversation history payload
    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in request.messages:
        messages_payload.append({"role": msg.role, "content": msg.content})

    # 3. Request completion from OpenAI-compatible endpoint
    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages_payload
        )
        reply = completion.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        # ALWAYS log the real exception server-side
        logger.exception("Error occurred while communicating with Azure OpenAI Foundry")
        # Return generic, readable JSON error message to the client without leaking secrets
        raise HTTPException(
            status_code=500,
            detail="Sorry, I'm having trouble answering right now..."
        )
