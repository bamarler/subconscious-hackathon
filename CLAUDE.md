# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Comify

A hackathon project that converts lecture slideshows into comic book panels. Users upload a .pptx or .pdf, and a 6-step AI pipeline extracts concepts, builds characters, writes a script, generates image prompts, and produces comic panel images.

## Architecture

Monorepo with two independent projects:

- **`backend/`** — Python FastAPI server. All request/response types use Pydantic models, including `answerFormat` for structured LLM outputs from Subconscious. Orchestrates the 6-step pipeline and calls fal.ai for image generation.
- **`frontend/`** — React + TypeScript SPA built with Vite. Drag-and-drop file upload, SSE streaming for real-time pipeline progress, progressive panel rendering.

### Pipeline (6 steps, streamed via SSE)

Each step yields `PipelineEvent` objects streamed as SSE to the frontend:

1. **Parse Slideshow** — `python-pptx` for .pptx, `PyMuPDF` for .pdf. Extracts text per slide.
2. **Concept Extractor** — Subconscious `client.run()` with `answerFormat=ConceptExtraction`. Finds key ideas, central tension, narrative arc.
3. **Character Mapper** — Subconscious run, `answerFormat=CharacterMap`. Assigns personas to concepts with visual descriptions and an art style.
4. **Panel Script Writer** — Subconscious run, `answerFormat=ComicScript`. Writes 5-panel comic script with dialogue, action, mood.
5. **Image Prompt Generator** — Subconscious run, `answerFormat=ImagePrompts`. Creates fal.ai-optimized prompts per panel.
6. **Image Generator** — `fal_client.run("fal-ai/flux/dev")` for each panel. Yields progress events so panels appear progressively on the frontend.

### SSE Event Format
```
data: {"step":2,"step_name":"Extracting concepts","status":"started","data":null,"error":null}
data: {"step":2,"step_name":"Extracting concepts","status":"completed","data":{...},"error":null}
data: {"step":6,"step_name":"Drawing panels","status":"progress","data":{"panel_number":1,"image_url":"..."},"error":null}
```
Status values: `started`, `completed`, `progress` (step 6 only), `error`.

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

- `backend/app/models.py` — All Pydantic models for each pipeline step
- `backend/app/pipeline.py` — 6-step pipeline generator: file parsing, 4 Subconscious calls, fal.ai image gen
- `backend/app/routes.py` — `POST /api/convert` accepts file upload, streams SSE
- `backend/app/config.py` — Settings via pydantic-settings
- `frontend/src/App.tsx` — Drag-and-drop upload, SSE consumption, progressive rendering
- `api/index.py` — Vercel serverless entrypoint

## Subconscious SDK

- `client.run(engine, input, options)` with `await_completion=True`
- Pass Pydantic classes directly to `answerFormat` — auto-converts via `model_json_schema()`
- Engines: `tim-edge`, `tim-gpt`, `tim-gpt-heavy` (default: `tim-gpt`)

## fal.ai SDK

- `fal_client.run("fal-ai/flux/dev", arguments={...})` — returns `{"images": [{"url": "..."}]}`
- Auth: reads `FAL_KEY` env var automatically
- Key params: `prompt`, `image_size` (landscape_16_9), `num_images`, `num_inference_steps`, `guidance_scale`
