# weather-risk-agent

A chat agent that helps a logistics company decide which of its 12 US distribution hubs are most exposed to weather disruption.
It scores each hub for winter, flood, hurricane and heat risk from Open-Meteo daily weather (2021-2025) and FEMA major disaster declarations (2006-2025).
A Claude agent answers questions using tools over those scores, behind a FastAPI backend and a React chat page.

## Prerequisites

- Python 3.13 (tested with 3.13.14)
- Node.js 24 with npm (tested with Node 24.18.0, npm 11.16.0)
- An Anthropic API key

## Setup

All commands start from the repository root.

1. Backend: create a virtual environment and install the packages.

   ```bash
   cd backend
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

   If PowerShell says "running scripts is disabled on this system", run
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

2. API key: copy `.env.example` to `.env` in the repository root and put your key after the `=`:

   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

   `.env` is ignored by git, so the key is never committed.

3. Frontend: install the packages.

   ```bash
   cd frontend
   npm install
   ```

## Data

The database `data/weather.db` is included in the repository, so no download is needed to run the app.

To rebuild it from the APIs (needs internet, takes about a minute), run from `backend/` with the virtual environment activated:

```bash
python -m scripts.ingest_weather   # Open-Meteo daily weather, prints "<hub> 1826 rows" for each of the 12 hubs
python -m scripts.ingest_fema      # FEMA declarations, prints "<hub> <n> rows" for each hub
```

Both scripts use `INSERT OR REPLACE`, so running them again updates the rows instead of duplicating them.
The hub list is in `data/hubs.json`.

## Run

Start the backend, from `backend/` with the virtual environment activated:

```bash
uvicorn app.main:app --reload
```

Check it at http://localhost:8000/health. Logs go to `logs/api_<date-time>.log`.

Start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Then open http://localhost:5173. Use `localhost`, not `127.0.0.1`: the backend only accepts
requests from `http://localhost:5173`. If Vite says port 5173 is in use and picks another port,
stop the other process first, otherwise the page cannot reach the backend.

## Tests and evals

From `backend/` with the virtual environment activated:

```bash
python -m pytest            # unit and API tests, no Anthropic API calls
python -m evals.run_evals   # 12 evaluation cases with real API calls
```

The evals print one line per case and save full results to `backend/evals/results/`.

Other scripts, also from `backend/`:

```bash
python -m scripts.chat_cli       # chat with the agent in the terminal (real API calls)
python -m scripts.print_scores   # table of the hazard scores for all 12 hubs
```

## Example questions

- Which hubs in the Midwest are most exposed to winter disruption?
- Compare Miami and Houston in terms of hurricane and flood exposure.
- What percentage of days in Denver last year had snowfall?
- Why is the Dallas hub's weather disruption risk high?

Follow-ups such as "and how does Houston compare?" work in the same chat.

## Design doc and transcripts

- Design doc: `docs/DESIGN.md`
- Development transcripts: `transcripts/`
