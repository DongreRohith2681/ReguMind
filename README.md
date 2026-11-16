# TOC Studio

TOC Studio is a FastAPI and React/Vite application for experimenting with finite automata and regular-language classification. The backend currently supports automaton simulation and transformations, random labeled-word generation, classifier evaluation, and two automaton-construction endpoints. The frontend provides a browser workspace shell with navigation for these activities; its workspace actions are currently presentational and are not yet wired to the API.

## Current status

Implemented:

- FastAPI application with OpenAPI/Swagger documentation at `/docs`.
- DFA/NFA-style word acceptance (transition values may be strings or lists).
- Subset-construction determinization and DFA minimization.
- Random word generation with reproducible seeds.
- Logistic regression, random forest, and decision tree evaluation from labeled words.
- Prefix-tree acceptor (PTA) construction and an `rpni` endpoint (currently a positive-only PTA implementation).
- React/Vite frontend with dashboard and workspace routes.

Not implemented or incomplete:

- Frontend controls do not call the backend yet.
- There is no persisted dataset, model, or experiment storage.
- The RPNI endpoint does not perform true red/blue state-merging RPNI and currently ignores negative examples.
- API routes are not versioned under `/api/v1`; use the paths listed below.

## Architecture

```text
frontend/                 React + Vite browser client
  src/App.tsx             Dashboard and navigable workspace shell
  src/main.tsx            React entry point and router
backend/
  app/main.py             FastAPI application, CORS, root and health routes
  app/routes.py           API route handlers
  app/models.py           Pydantic request models and validation bounds
  app/automata.py         Acceptance, determinization, minimization, PTA/RPNI logic
  app/data.py             Dataset generation, splitting, and feature extraction
  tests/test_api.py       API smoke tests
```

The backend accepts JSON and is the source of truth for computation. CORS allows the Vite development origins `http://localhost:5173` and `http://127.0.0.1:5173`.

## Automaton data model

```json
{
  "states": ["q0", "q1"],
  "alphabet": ["0", "1"],
  "transitions": {
    "q0": {"0": "q0", "1": "q1"},
    "q1": {"0": "q0", "1": "q1"}
  },
  "start_state": "q0",
  "accept_states": ["q1"],
  "deterministic": true
}
```

`states` and `alphabet` are lists of strings. A transition destination can be one string or a list of strings. `word` values are arrays of symbols, so multi-character symbols are supported. Pydantic validates the field shapes, but the current implementation does not comprehensively reject every semantic inconsistency such as unknown state references.

## Algorithms and behavior

- **Acceptance:** starts with the start state, follows each symbol, and carries a set of reachable states. A string destination is treated as a one-item set; a list is treated as an NFA branch. The word is accepted if a final reachable state is accepting. Missing transitions lead to no reachable state and therefore rejection. Epsilon transitions are not supported.
- **Determinization:** uses reachable subset construction. Subset states are named like `{q0,q1}` and empty/dead subsets are omitted.
- **Minimization:** determinizes an NFA first, then applies table-style distinguishability partitioning to the resulting DFA. It does not explicitly remove unreachable states beyond those already omitted by determinization.
- **Dataset generation:** creates `n_samples` random words whose lengths are uniformly selected from `0..max_length`, chooses symbols uniformly from the alphabet, and labels each word with the acceptance result. The local random generator is seeded for reproducibility.
- **Features:** classifiers use one count feature per observed vocabulary symbol plus word length. This is a bag-of-symbols representation; it does not encode transition paths or symbol order.
- **Training:** splits features and labels with `train_test_split`, stratifying when both classes are present, then evaluates the requested classifier on the held-out partition. The response contains metrics and feature metadata, not a serialized model.
- **Learning:** `/api/pta` builds a deterministic prefix tree from positive words. `/api/rpni` currently delegates to the same positive-only PTA builder; negative samples are accepted by the request model but are not used.

## API

The service runs on `http://localhost:8000`. Interactive documentation is available at `http://localhost:8000/docs`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Returns application name, version, and docs path. |
| `GET` | `/health` | Returns `{ "status": "ok" }`. |
| `POST` | `/api/accepts` | Evaluate one word against an automaton. |
| `POST` | `/api/determinize` | Return a deterministic automaton. |
| `POST` | `/api/minimize` | Return a minimized deterministic automaton. |
| `POST` | `/api/dataset` | Generate words and acceptance labels. |
| `POST` | `/api/train` | Evaluate a classifier on a train/test split. |
| `POST` | `/api/pta` | Build a PTA from positive examples. |
| `POST` | `/api/rpni` | Current positive-only PTA-backed RPNI placeholder. |

### Acceptance example

```bash
curl -X POST http://localhost:8000/api/accepts \
  -H "Content-Type: application/json" \
  -d '{"automaton":{"states":["q0","q1"],"alphabet":["0","1"],"transitions":{"q0":{"0":"q0","1":"q1"},"q1":{"0":"q0","1":"q1"}},"start_state":"q0","accept_states":["q1"],"deterministic":true},"word":["1","0"]}'
```

Response:

```json
{"accepted": true, "word": ["1", "0"]}
```

### Dataset example

```bash
curl -X POST http://localhost:8000/api/dataset \
  -H "Content-Type: application/json" \
  -d '{"automaton":{"states":["q0","q1"],"alphabet":["0","1"],"transitions":{"q0":{"0":"q0","1":"q1"},"q1":{"0":"q0","1":"q1"}},"start_state":"q0","accept_states":["q1"],"deterministic":true},"n_samples":100,"max_length":10,"test_size":0.2,"seed":42}'
```

The response contains `words`, `labels`, `positive_count`, and `negative_count`. `test_size` is validated by the request model but is not used by this endpoint's response; splitting occurs in `/api/train`.

### Training example

```bash
curl -X POST http://localhost:8000/api/train \
  -H "Content-Type: application/json" \
  -d '{"words":[["1"],["0"],["1","0"]],"labels":[1,0,1],"test_size":0.2,"seed":42,"model":"logistic_regression"}'
```

Supported `model` values are `logistic_regression`, `random_forest`, and `decision_tree`. The response includes `accuracy`, `precision`, `recall`, `f1`, `confusion_matrix`, `n_features`, and `vocabulary`. Words and labels must have matching lengths and labels must contain at least two classes.

## Setup and usage

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run the backend commands from `backend` so the `app` package is importable.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`. The current frontend renders dashboard, datasets, DFA builder, learning, ML, string tester, comparison, and visualization routes, but the generic workspaces do not yet submit API requests.

## Testing and quality checks

Backend smoke tests:

```bash
cd backend
pytest
python -m compileall app
```

Frontend type-check and production build:

```bash
cd frontend
npm run build
```

`frontend/package.json` does not currently define dedicated `lint` or `test` scripts. The backend test suite currently covers health, acceptance at `/api/accepts`, and determinization at `/api/determinize`.

## Limitations

- No authentication, persistence, deployment configuration, request-rate limits, or production hardening.
- No epsilon transitions, weighted/probabilistic automata, regular-expression parsing, grammar conversion, or language-equivalence proof.
- Semantic validation of transition references and consistency between `states`, `alphabet`, and `transitions` is limited.
- NFA acceptance does not implement epsilon closure.
- Dataset generation can produce class imbalance and may use a vocabulary that differs from later inputs.
- Feature extraction discards symbol order and transition structure, so classifier quality depends on the data.
- Small datasets can make held-out metrics unstable; train/test splitting can also fail for unsuitable class counts or test sizes.
- `/api/rpni` is a placeholder rather than a complete RPNI implementation, and does not enforce negative examples.
- Large sample or word-length limits can consume substantial CPU and memory; model objects are not retained after a training request.
