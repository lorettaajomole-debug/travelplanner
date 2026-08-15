# AeroPlan AI - Travel Planning Expert Chatbot

AeroPlan AI is an interactive, responsive travel assistant powered by Azure AI Foundry. It suggestion day-by-day itineraries, destinations, budgets, and packing guides based on traveler interest, budget, season, and pace.

## Project Structure
- `app.py`: FastAPI server serving index.html and exposing the `/chat` endpoint.
- `index.html`: Clean, modern, responsive glassmorphic chat UI with suggestion chips.
- `requirements.txt`: Python package dependencies.
- `.env`: API credentials (ignored by git).
- `.env.example`: Configuration templates.

---

## Configuration Setup

Before running the server, configure the environment variables:
1. Copy the template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in the values from your Azure AI Foundry deployment page:
   ```env
   AZURE_ENDPOINT=https://<your-resource>.services.ai.azure.com/openai/v1
   AZURE_DEPLOYMENT=gpt-5-mini
   AZURE_API_KEY=your_actual_azure_api_key_here
   ```

---

## Run Instructions

### macOS / Linux
1. Create a virtual environment (skip if `.venv` already exists):
   ```bash
   python3 -m venv .venv
   ```
2. Install dependencies:
   ```bash
   ./.venv/bin/pip install -r requirements.txt
   ```
3. Run the uvicorn development server:
   ```bash
   ./.venv/bin/uvicorn app:app --reload --port 8000
   ```
4. Open the Web UI:
   Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

### Windows
1. Create a virtual environment (skip if `.venv` already exists):
   ```powershell
   python -m venv .venv
   ```
2. Install dependencies:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Run the uvicorn development server:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000
   ```
4. Open the Web UI:
   Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

---

## Troubleshooting

### 1. Changes to `.env` not applying
`uvicorn --reload` watches and reloads on changes to `.py` files but does **NOT** reload when `.env` changes. After editing the `.env` file, you must fully stop (press `Ctrl+C`) and restart the uvicorn command.

### 2. 401 "Access Denied" or Endpoint Connection Error
An error like `Access denied due to invalid subscription key or wrong API endpoint` indicates that Azure rejected the request.
- Check the server terminal output logs for the detailed traceback logged by `logging.exception(...)`.
- Confirm that the `AZURE_API_KEY` and `AZURE_ENDPOINT` match your project's Azure deployment credentials exactly.
- Verify that `AZURE_ENDPOINT` ends with `/openai/v1` (e.g. `https://<your-resource>.services.ai.azure.com/openai/v1`).

### 3. Isolate Backend Errors (CLI Connection Test)

To test the backend API response directly and rule out browser/CORS/UI errors, run one of the following CLI commands:

#### PowerShell:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat -Method Post -ContentType 'application/json' -Body '{"messages":[{"role":"user", "content":"hi"}]}'
```

#### Bash/curl:
```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user", "content":"hi"}]}'
```
