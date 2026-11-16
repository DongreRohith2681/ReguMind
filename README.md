# ReguMind

ReguMind is a FastAPI and React/Vite application for experimenting with finite automata and regular-language classification. The backend supports automaton simulation and transformations, random labeled-word generation, classifier evaluation, and automaton-construction endpoints. The frontend provides a browser workspace for these activities.

## Project branding

The application name is **ReguMind** across the frontend title, browser package metadata, sidebar branding, FastAPI service metadata, and documentation.

## Architecture

```text
frontend/                 React + Vite browser client
  src/App.tsx             Dashboard and navigable workspace
  src/main.tsx            React entry point and router
backend/
  app/main.py             FastAPI application, CORS, root and health routes
  app/routes.py           API route handlers
  app/models.py           Pydantic request models
  app/automata.py         Acceptance, determinization, minimization, PTA/RPNI logic
  app/data.py             Dataset generation, splitting, and feature extraction
  tests/test_api.py       API smoke tests
```

## Setup

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend uses `http://localhost:8000` by default; set `VITE_API_URL` to override it.

## Validation

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

## API

- `GET /` — ReguMind service metadata
- `GET /health` — health check
- `POST /api/accepts` — evaluate a word
- `POST /api/determinize` — convert an automaton to deterministic form
- `POST /api/minimize` — minimize a DFA
- `POST /api/dataset` — generate labeled words
- `POST /api/train` — train and evaluate a classifier
- `POST /api/pta` — build a prefix-tree acceptor
- `POST /api/rpni` — infer an automaton from labeled examples

Interactive API documentation is available at `http://localhost:8000/docs`.

## Limitations

The project has no authentication, persistence, deployment configuration, or production hardening. Model and experiment state is request-scoped. Dataset quality and classifier performance depend on the selected language, alphabet, and sample size.
