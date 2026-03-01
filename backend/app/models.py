from pydantic import BaseModel, Field


# ── Step 1: File Parsing ──


class SlideContent(BaseModel):
    slide_number: int
    text: str = Field(..., description="All text extracted from this slide")


class ParsedLecture(BaseModel):
    title: str = Field("", description="Lecture title if detected")
    slides: list[SlideContent]
    full_text: str = Field(..., description="Concatenated text from all slides")


# ── Step 2: Single Subconscious call (answerFormat) ──
# Combines concept extraction, character mapping, script writing, and image prompt generation.


class Concept(BaseModel):
    name: str = Field(..., description="Short name for the concept")
    description: str = Field(..., description="One-sentence explanation")
    importance: int = Field(..., ge=1, le=10, description="How central to the lecture (1-10)")


class Character(BaseModel):
    name: str = Field(..., description="Character name (creative, memorable)")
    concept: str = Field(..., description="Which concept this character personifies")
    visual_description: str = Field(
        ..., description="Detailed visual appearance for image generation: clothing, colors, features"
    )
    personality: str = Field(..., description="One-sentence personality trait")
    role: str = Field(
        ..., description="Role in the story: protagonist, antagonist, mentor, etc."
    )


class PanelScript(BaseModel):
    panel_number: int = Field(..., ge=1, le=5)
    setting: str = Field(..., description="Where this panel takes place")
    characters_present: list[str] = Field(..., description="Character names in this panel")
    dialogue: str = Field(..., description="Speech bubble text")
    action: str = Field(..., description="What is happening visually in the panel")
    mood: str = Field(..., description="Emotional tone: tense, humorous, triumphant, etc.")


class ImagePrompt(BaseModel):
    panel_number: int = Field(..., ge=1, le=5)
    prompt: str = Field(
        ..., description="Detailed image prompt: scene, characters, composition, lighting, style. Must start with the art_style for consistency."
    )
    negative_prompt: str = Field(default="", description="What to avoid in the image")


class ComicBlueprint(BaseModel):
    """Single structured output from Subconscious that covers the entire creative pipeline:
    concept extraction, character design, script writing, and image prompt generation."""

    # Concept extraction
    lecture_topic: str = Field(..., description="One-line summary of the lecture topic")
    concepts: list[Concept] = Field(
        ..., description="3-8 key concepts extracted from the lecture"
    )
    central_tension: str = Field(
        ..., description="The core conflict or tension that drives the comic narrative"
    )
    narrative_arc: str = Field(
        ..., description="Brief description of how the story flows from setup to resolution"
    )

    # Character design
    characters: list[Character] = Field(
        ..., description="2-6 characters, each personifying a concept with detailed visual descriptions"
    )
    art_style: str = Field(
        ..., description="Consistent art style for all panels, e.g. 'vibrant manga with cel shading'"
    )

    # Comic script
    title: str = Field(..., description="Comic title")
    panels: list[PanelScript] = Field(
        ..., description="Exactly 5 comic panels with dialogue, action, and mood"
    )

    # Image prompts
    image_prompts: list[ImagePrompt] = Field(
        ..., description="Exactly 5 detailed image generation prompts, one per panel"
    )


# ── Step 3: Image Generation result ──


class GeneratedImage(BaseModel):
    panel_number: int
    url: str
    seed: int | None = None


# ── SSE Event Envelope ──


class PipelineEvent(BaseModel):
    step: int = Field(..., ge=1, le=3, description="Pipeline step number")
    step_name: str
    status: str = Field(..., description="started | completed | progress | error")
    data: dict | None = Field(default=None, description="Step output data when completed")
    error: str | None = None


# ── Final Comic Output ──


class ComicPanel(BaseModel):
    panel_number: int
    setting: str
    characters: list[str]
    dialogue: str
    action: str
    image_url: str | None = None
    image_prompt: str


class ComicResult(BaseModel):
    title: str
    panels: list[ComicPanel]
