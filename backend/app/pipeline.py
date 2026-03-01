from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from .job_store import Job

import fal_client
from subconscious import Subconscious

from .config import settings
from .models import (
    ComicBlueprint,
    ComicPanel,
    ComicResult,
    ParsedLecture,
    PipelineEvent,
    SlideContent,
)

STEP_NAMES = [
    "Parsing slideshow",
    "Creating comic blueprint",
    "Drawing panels",
]


def _emit(
    step: int, status: str, data: dict | None = None, error: str | None = None
) -> PipelineEvent:
    return PipelineEvent(
        step=step,
        step_name=STEP_NAMES[step - 1],
        status=status,
        data=data,
        error=error,
    )


# ── Step 1: Parse uploaded file ──


def parse_pptx(file_bytes: bytes) -> ParsedLecture:
    from pptx import Presentation

    prs = Presentation(io.BytesIO(file_bytes))
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                texts.append(shape.text_frame.text)
        slides.append(SlideContent(slide_number=i, text="\n".join(texts)))
    title = slides[0].text.split("\n")[0] if slides else ""
    full_text = "\n\n".join(f"[Slide {s.slide_number}]\n{s.text}" for s in slides)
    return ParsedLecture(title=title, slides=slides, full_text=full_text)


def parse_pdf(file_bytes: bytes) -> ParsedLecture:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    slides = []
    for i, page in enumerate(doc, 1):
        text = page.get_text()
        slides.append(SlideContent(slide_number=i, text=text))
    doc.close()
    title = slides[0].text.split("\n")[0] if slides else ""
    full_text = "\n\n".join(f"[Page {s.slide_number}]\n{s.text}" for s in slides)
    return ParsedLecture(title=title, slides=slides, full_text=full_text)


def parse_file(file_bytes: bytes, filename: str) -> ParsedLecture:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pptx":
        return parse_pptx(file_bytes)
    elif ext == "pdf":
        return parse_pdf(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


# ── Step 2: Single Subconscious call ──


def create_blueprint(client: Subconscious, lecture: ParsedLecture) -> ComicBlueprint:
    instructions = f"""You are Comify, an expert at turning lecture content into engaging educational comics.

Given the lecture notes below, produce a complete comic blueprint in a single pass:

1. EXTRACT KEY CONCEPTS (3-8) from the lecture. Identify a central tension or conflict that can drive a narrative.
2. DESIGN CHARACTERS (2-6) that personify the concepts. Give each a creative name, detailed visual description (for image generation), personality, and story role.
3. CHOOSE AN ART STYLE that fits the subject matter (e.g. "retro sci-fi illustration", "Studio Ghibli watercolor", "pop art comic book").
4. WRITE A 5-PANEL COMIC SCRIPT with dialogue, action, settings, and mood. Use the central tension to create a mini-story with beginning, middle, and end.
5. GENERATE 5 IMAGE PROMPTS optimized for AI image generation. Each prompt MUST start with the art style. Include character visual descriptions, composition, lighting, and mood. Do NOT include text, speech bubbles, or lettering in the image prompts.

Lecture content:
{lecture.full_text}"""

    run = client.run(
        engine=settings.engine,
        input={
            "instructions": instructions,
            "answerFormat": ComicBlueprint,
        },
        options={"await_completion": True},
    )
    if not run.result or not run.result.answer:
        raise RuntimeError("No result from Subconscious")
    return ComicBlueprint.model_validate_json(run.result.answer)


# ── Step 3: fal.ai image generation ──


def generate_image(prompt: str, negative_prompt: str = "") -> str:
    if settings.fal_key:
        os.environ["FAL_KEY"] = settings.fal_key

    full_negative = "text, words, letters, speech bubbles, watermark"
    if negative_prompt:
        full_negative = f"{negative_prompt}, {full_negative}"

    response = fal_client.run(
        "fal-ai/nano-banana-2",
        arguments={
            "prompt": prompt,
            "image_size": "landscape_16_9",
            "num_images": 1,
            "enable_safety_checker": True,
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
        },
    )
    return response["images"][0]["url"]


# ── Full pipeline generator ──


def run_pipeline(file_bytes: bytes, filename: str) -> Generator[PipelineEvent, None, None]:
    client = Subconscious(api_key=settings.subconscious_api_key)

    # Step 1: Parse
    yield _emit(1, "started")
    try:
        lecture = parse_file(file_bytes, filename)
        yield _emit(1, "completed", data={"slide_count": len(lecture.slides), "title": lecture.title})
    except Exception as e:
        yield _emit(1, "error", error=str(e))
        return

    # Step 2: Single Subconscious call — concepts, characters, script, prompts
    yield _emit(2, "started")
    try:
        blueprint = create_blueprint(client, lecture)
        yield _emit(2, "completed", data=blueprint.model_dump())
    except Exception as e:
        yield _emit(2, "error", error=str(e))
        return

    # Step 3: Image Generation (fal.ai)
    yield _emit(3, "started")
    try:
        panels: list[ComicPanel] = []
        for i, (panel_script, img_prompt) in enumerate(
            zip(blueprint.panels, blueprint.image_prompts)
        ):
            image_url = generate_image(
                prompt=img_prompt.prompt,
                negative_prompt=img_prompt.negative_prompt,
            )
            panel = ComicPanel(
                panel_number=panel_script.panel_number,
                setting=panel_script.setting,
                characters=panel_script.characters_present,
                dialogue=panel_script.dialogue,
                action=panel_script.action,
                image_url=image_url,
                image_prompt=img_prompt.prompt,
            )
            panels.append(panel)
            yield _emit(
                3,
                "progress",
                data={
                    "panel_number": panel.panel_number,
                    "image_url": image_url,
                    "panels_done": i + 1,
                    "panels_total": 5,
                },
            )

        result = ComicResult(title=blueprint.title, panels=panels)
        yield _emit(3, "completed", data=result.model_dump())
    except Exception as e:
        yield _emit(3, "error", error=str(e))
        return


def run_pipeline_into_job(job: Job, file_bytes: bytes, filename: str) -> None:
    """Run the pipeline in a background thread, writing events into the job store."""
    job.status = "running"
    for event in run_pipeline(file_bytes, filename):
        job.append_event(event)
