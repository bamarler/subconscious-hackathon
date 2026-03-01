# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Lecture-to-Comic Converter

A hackathon project that converts lecture slideshow notes into comic book panels. Uses a 5-tool Subconscious AI agent pipeline to extract concepts, build characters, write dialogue, generate image prompts, and produce visuals via Ideogram.

## Architecture

Monorepo with two independent projects:

- **`backend/`** — Python FastAPI server. All request/response types use Pydantic models, including `answerFormat` for structured LLM outputs from Subconscious. Manages the 5-step pipeline and calls Ideogram for image generation.
- **`frontend/`** — React + TypeScript SPA built with Vite. Lightweight, minimal dependencies.

### Pipeline (5 Subconscious agent tools, chained sequentially)

Each step is a separate Subconscious `client.run()` call with its own Pydantic `answerFormat`:

1. **Concept Extractor** — Takes raw lecture notes. Extracts key ideas, core tension/conflict, and the narrative arc that will drive the comic. Output: list of concepts with relationships and a central conflict.

2. **Character Mapper** — Takes extracted concepts. Assigns a persona/character to each concept (e.g., "Recursion" becomes a snake eating its tail, "Big-O Notation" becomes a stopwatch-wielding referee). Output: character profiles with names, visual descriptions, and which concept they embody.

3. **Panel Script Writer** — Takes characters + concepts. Writes a 5-panel comic script with dialogue, action descriptions, and panel layout notes. The narrative should use the tension from step 1 to create an actual mini-story. Output: 5 panels each with setting, characters present, dialogue, and action.

4. **Image Prompt Generator** — Takes each panel script. Generates a detailed Ideogram-optimized image prompt per panel, including art style consistency cues, character visual references, and composition direction. Output: 5 image generation prompts with style/aspect ratio metadata.

5. **Image Generator (Ideogram API)** — Takes the prompts from step 4. Calls Ideogram v3 API (`POST https://api.ideogram.ai/v1/ideogram-v3/generate`) to generate the actual comic panel images. Uses `style_type: FICTION`, consistent style codes across panels, and comic-appropriate aspect ratios.

### Pydantic Models (all in `backend/app/models.py`)

Every pipeline step has a dedicated Pydantic model for its structured output. These models are passed directly as `answerFormat` to Subconscious — the SDK auto-converts via `model_json_schema()`.

## Commands

### Backend (uv)
```bash
# Install dependencies
uv sync --project backend

# Run dev server
uv run --project backend --directory backend uvicorn app.main:app --reload --port 8000
```

### Frontend (bun)
```bash
# Install dependencies
bun install --cwd frontend

# Dev server (port 5173)
bun run --cwd frontend dev

# Build
bun run --cwd frontend build

# Type check
bun run --cwd frontend tsc -b
```

## Environment Variables

`backend/.env` (copy from `.env.example`):
- `SUBCONSCIOUS_API_KEY` — from subconscious.dev dashboard
- `IDEOGRAM_API_KEY` — from ideogram.ai developer settings
- `VITE_API_URL` — (frontend) defaults to `http://localhost:8000`

## Subconscious SDK Usage

- `client.run(engine, input, options)` with `await_completion=True` for sync calls
- `client.stream(engine, input)` yields `DeltaEvent`/`DoneEvent`/`ErrorEvent` for SSE
- Pass Pydantic model classes directly to `answerFormat` — SDK auto-converts
- Available engines: `tim-edge`, `tim-gpt`, `tim-gpt-heavy` (use `tim-gpt` as default)
- Platform tools: `{"type": "platform", "id": "web_search"}`

## Ideogram API Usage

- **Endpoint**: `POST https://api.ideogram.ai/v1/ideogram-v3/generate`
- **Auth**: `Api-Key` header
- **Content-Type**: `multipart/form-data`
- **Key params**: `prompt`, `aspect_ratio`, `style_type` (FICTION for comics), `style_preset`, `rendering_speed`, `num_images`, `negative_prompt`
- **Response**: `{ data: [{ url, prompt, resolution, seed, is_image_safe }] }`
- Image URLs expire — download and serve/cache them

## Key Files

- `backend/app/models.py` — All Pydantic models for each pipeline step's input/output
- `backend/app/routes.py` — FastAPI routes: main `/api/convert` endpoint that orchestrates the pipeline
- `backend/app/pipeline.py` — The 5-step pipeline logic: concept extraction → character mapping → script writing → prompt generation → image generation
- `backend/app/config.py` — Settings via pydantic-settings, reads from `.env`
- `frontend/src/App.tsx` — Upload/paste interface and comic panel display
