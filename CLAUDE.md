# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Comify

A hackathon project that converts lecture slideshows into comic book panels. Users upload a .pptx or .pdf, and a 3-step AI pipeline extracts concepts, builds characters, writes a script, generates image prompts, and produces comic panel images.

## Architecture

Monorepo with two independent projects:

- **`backend/`** — Python FastAPI server. All request/response types use Pydantic models, including `answerFormat` for structured LLM outputs from Subconscious. Orchestrates the 3-step pipeline and calls fal.ai for image generation.
- **`frontend/`** — React + TypeScript SPA built with Vite. Drag-and-drop file upload, SSE streaming for real-time pipeline progress, progressive panel rendering.

### Pipeline (3 steps, streamed via SSE)

Each step yields `PipelineEvent` objects streamed as SSE to the frontend:

1. **Parse Slideshow** — `python-pptx` for .pptx, `PyMuPDF` for .pdf. Extracts text per slide.
2. **Create Comic Blueprint** — Single Subconscious `client.run()` with `answerFormat=ComicBlueprint`. The TIM engine handles the full creative chain in one call: concept extraction, character design, script writing, and image prompt generation. Output is a single `ComicBlueprint` Pydantic model containing all fields.
3. **Draw Panels** — `fal_client.run("fal-ai/flux/dev")` for each of 5 panels. Yields `progress` events so panels appear progressively on the frontend.

### Background Jobs + Persistence

The pipeline runs in a background thread decoupled from the SSE connection:
- `POST /api/convert` starts the job and returns `{ job_id }`
- `GET /api/jobs/{id}/stream` replays completed events then follows live
- `GET /api/jobs/{id}` returns quick status
- Jobs stored in-memory (`backend/app/job_store.py`) with 30-min TTL
- Frontend stores `job_id` in localStorage — browser refresh reconnects to the running job
- Final comic result cached in localStorage

### SSE Event Format
```
data: {"step":1,"step_name":"Parsing slideshow","status":"started","data":null,"error":null}
data: {"step":2,"step_name":"Creating comic blueprint","status":"completed","data":{...},"error":null}
data: {"step":3,"step_name":"Drawing panels","status":"progress","data":{"panel_number":1,"image_url":"..."},"error":null}
```
Status values: `started`, `completed`, `progress` (step 3 only), `error`.

## Commands

### Backend (uv)
```bash
uv sync --project backend
uv run --project backend --directory backend uvicorn app.main:app --reload --port 8000
```

### Frontend (bun)
```bash
bun install --cwd frontend
bun run --cwd frontend dev
bun run --cwd frontend build
```

### Both (Makefile)
```bash
make init    # install all deps + create .env
make up      # start backend + frontend dev servers
```

## Environment Variables

`backend/.env` (copy from `.env.example`):
- `SUBCONSCIOUS_API_KEY` — from subconscious.dev dashboard
- `FAL_KEY` — from fal.ai dashboard

Frontend: `VITE_API_URL` defaults to `http://localhost:8000`.

## Key Files

- `backend/app/models.py` — All Pydantic models. `ComicBlueprint` is the single answerFormat for the Subconscious call.
- `backend/app/pipeline.py` — 3-step pipeline generator: file parsing, 1 Subconscious call, fal.ai image gen
- `backend/app/job_store.py` — In-memory job store with threading.Event for SSE notification
- `backend/app/routes.py` — `POST /api/convert`, `GET /api/jobs/{id}/stream`, `GET /api/jobs/{id}`
- `backend/app/config.py` — Settings via pydantic-settings
- `frontend/src/App.tsx` — Drag-and-drop upload, SSE consumption, reconnect on refresh, progressive rendering
- `api/index.py` — Vercel serverless entrypoint

## Subconscious SDK

- `client.run(engine, input, options)` with `await_completion=True`
- Pass Pydantic classes directly to `answerFormat` — auto-converts via `model_json_schema()`
- Engines: `tim-edge`, `tim-gpt`, `tim-gpt-heavy` (default: `tim-gpt`)

## fal.ai SDK

- `fal_client.run("fal-ai/flux/dev", arguments={...})` — returns `{"images": [{"url": "..."}]}`
- Auth: reads `FAL_KEY` env var automatically
- Key params: `prompt`, `image_size` (landscape_16_9), `num_images`, `num_inference_steps`, `guidance_scale`
