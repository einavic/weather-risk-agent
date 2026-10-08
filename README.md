# weather-risk-agent

## Run the backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/health

## Run the tests

From `backend/` with the virtual environment activated:

```bash
python -m pytest
```
