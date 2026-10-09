# weather-risk-agent

A chat agent that helps a logistics company decide which of its 12 US distribution hubs are most exposed to weather disruption.
It scores each hub for winter, flood, hurricane and heat risk from Open-Meteo daily weather (2021-2025) and FEMA major disaster declarations (2006-2025).
A Claude agent answers questions using tools over those scores, behind a FastAPI backend and a React chat page.

Live demo: https://weather-risk-agent.onrender.com

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

   On Windows, clone into a short path such as `C:\Users\you\weather-risk-agent`, or enable
   long paths (see pip's hint in the error). Some file paths inside the `anthropic` package are
   long, and `pip install` fails if the full path goes over Windows' 260-character limit.

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

To rebuild it from the APIs (needs internet), run from `backend/` with the virtual environment activated:

```bash
python -m scripts.ingest_weather   # Open-Meteo daily weather, prints "<hub> 1826 rows" for each of the 12 hubs
python -m scripts.ingest_fema      # FEMA declarations, prints "<hub> <n> rows" for each hub
```

Both scripts use `INSERT OR REPLACE`, so running them again updates the rows instead of duplicating them.

Each weather request covers five years of data, so `ingest_weather` can hit Open-Meteo's free rate
limit. If it stops with `429 Too Many Requests`, wait a minute and run it again. Rows that are
already there are just replaced.
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

## Alerts

`check_alerts` compares every hub's four hazard scores and composite with the last saved
snapshot (`data/score_snapshot.json`) and prints an alert for any score that changed by
1.0 point or more. If the environment variable `ALERT_WEBHOOK_URL` is set, it also POSTs the
alerts as JSON to that URL. It then saves the current scores as the new snapshot.

Run it from `backend/` with the virtual environment activated:

```bash
python -m scripts.check_alerts
```

It is meant to run on a schedule (cron or Windows Task Scheduler), right after the two
ingest scripts refresh the data.

To try it: if `data/score_snapshot.json` does not exist, the first run creates it and prints
"snapshot created". Change one number in that file (for example dallas `"heat": 100.0` to
`90.0`), run it again, and it prints `dallas: heat changed from 90.0 to 100.0`.

## Deploy

The backend also serves the built chat page, so one service runs the whole app.
`frontend/dist` is committed, so the host does not need Node.

- Build command: `pip install -r backend/requirements.txt`
- Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set `ANTHROPIC_API_KEY` as an environment variable on the host (there is no `.env` there).

The page is then at the host's root URL, and the API at `/chat` and `/health`.
After changing the frontend, run `npm run build` in `frontend/` and commit `frontend/dist`.
Chat sessions are kept in server memory, so a restart or redeploy clears them.

## Example questions

- Which hubs in the Midwest are most exposed to winter disruption?
- Compare Miami and Houston in terms of hurricane and flood exposure.
- What percentage of days in Denver last year had snowfall?
- Why is the Dallas hub's weather disruption risk high?

Follow-ups such as "and how does Houston compare?" work in the same chat.

## Transcripts
- Development transcripts: `transcripts/`
