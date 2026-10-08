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

## Run the frontend

Start the backend first (see above), then in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173 (use `localhost`, not `127.0.0.1`: the backend
only accepts requests from `http://localhost:5173`).

## Run the tests

From `backend/` with the virtual environment activated:

```bash
python -m pytest
```
