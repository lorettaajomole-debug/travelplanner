import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load local environment variables if .env exists (useful for local Netlify Dev testing)
load_dotenv()

# Verbatim Travel Planner System Prompt
SYSTEM_PROMPT = (
    "You are a friendly, well-traveled trip-planning expert. You help people plan trips - "
    "suggesting destinations, day-by-day itineraries, things to do, rough budgeting, and "
    "packing tips - in clear, practical language tailored to their interests, budget, dates, "
    "and travel style. Ask clarifying questions when useful, such as who is going, the budget, "
    "the season, and the preferred pace. Remind users to verify time-sensitive details "
    "themselves - visas, opening hours, prices, weather, and safety or travel advisories - "
    "since these change and you may not have current information. Be enthusiastic but realistic."
)

def handler(event, context):
    """
    Netlify serverless function handler.
    Receives request payload, validates Azure OpenAI config, and requests chat completions.
    """
    # CORS Headers configuration
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }

    # Handle OPTIONS preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }

    # 1. Validate environment configuration
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
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"detail": err_msg})
        }

    # 2. Parse request body
    body_str = event.get("body")
    if not body_str:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"detail": "Missing request body"})
        }

    try:
        req_data = json.loads(body_str)
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"detail": "Invalid JSON in request body"})
        }

    messages = req_data.get("messages", [])
    if not isinstance(messages, list):
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"detail": "messages must be a list"})
        }

    # 3. Build full conversation history payload
    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role and content:
            messages_payload.append({"role": role, "content": content})

    # 4. Request completion from OpenAI-compatible endpoint
    try:
        client = OpenAI(
            base_url=endpoint,
            api_key=api_key
        )
        completion = client.chat.completions.create(
            model=deployment,
            messages=messages_payload
        )
        reply = completion.choices[0].message.content
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"reply": reply})
        }
    except Exception as e:
        # ALWAYS log the real exception in Netlify server logs
        logger.exception("Error occurred while communicating with Azure OpenAI Foundry")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"detail": "Sorry, I'm having trouble answering right now..."})
        }
