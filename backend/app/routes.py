import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from subconscious import Subconscious, SubconsciousError

from .config import settings
from .models import DreamAnalysis, DreamInput, DreamResponse, ErrorResponse

router = APIRouter()


def _get_client() -> Subconscious:
    if not settings.subconscious_api_key:
        raise HTTPException(status_code=500, detail="SUBCONSCIOUS_API_KEY not configured")
    return Subconscious(api_key=settings.subconscious_api_key)


def _build_instructions(dream: DreamInput) -> str:
    mood_line = f"\nThe dreamer's mood: {dream.mood}" if dream.mood else ""
    return f"""You are the Dream Decoder — a surreal, poetic, and slightly unhinged dream analyst.
You combine Jungian psychology, pop culture, and cosmic vibes to decode dreams.

Analyze this dream and return a structured JSON response matching the schema exactly.
Be creative, surprising, and fun. The "hidden_message" should feel like a fortune cookie written by a philosopher on mushrooms.
The "recommended_song" must be a real song that exists.
For "connections", search the web for surprising real-world parallels to elements in the dream.

The dream:
\"\"\"{dream.dream_text}\"\"\"{mood_line}"""


@router.post("/decode", response_model=DreamResponse, responses={500: {"model": ErrorResponse}})
def decode_dream(dream: DreamInput) -> DreamResponse:
    client = _get_client()
    instructions = _build_instructions(dream)

    try:
        run = client.run(
            engine=settings.engine,
            input={
                "instructions": instructions,
                "tools": [{"type": "platform", "id": "web_search"}],
                "answerFormat": DreamAnalysis,
            },
            options={"await_completion": True},
        )
    except SubconsciousError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not run.result or not run.result.answer:
        raise HTTPException(status_code=502, detail="No result from Subconscious")

    try:
        analysis = DreamAnalysis.model_validate_json(run.result.answer)
    except Exception:
        # If structured output parsing fails, try to extract what we can
        raise HTTPException(status_code=502, detail="Failed to parse dream analysis")

    return DreamResponse(analysis=analysis, engine_used=settings.engine)


@router.post("/decode/stream")
def decode_dream_stream(dream: DreamInput) -> StreamingResponse:
    client = _get_client()
    instructions = _build_instructions(dream)

    def generate():
        try:
            for event in client.stream(
                engine=settings.engine,
                input={
                    "instructions": instructions,
                    "tools": [{"type": "platform", "id": "web_search"}],
                    "answerFormat": DreamAnalysis,
                },
            ):
                if event.type == "delta":
                    yield f"data: {json.dumps({'type': 'delta', 'content': event.content})}\n\n"
                elif event.type == "done":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                elif event.type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event.message})}\n\n"
        except SubconsciousError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
