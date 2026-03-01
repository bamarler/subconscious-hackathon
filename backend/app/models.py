from pydantic import BaseModel, Field


class DreamInput(BaseModel):
    """User's dream description submitted for analysis."""

    dream_text: str = Field(..., min_length=10, description="Description of the dream")
    mood: str | None = Field(None, description="How the dreamer felt (optional)")


class DreamSymbol(BaseModel):
    """A symbol extracted from the dream."""

    symbol: str = Field(..., description="The symbol or motif found in the dream")
    meaning: str = Field(..., description="Creative psychological interpretation")
    vibe: str = Field(..., description="One-word vibe check for this symbol")


class DreamConnection(BaseModel):
    """A surprising real-world connection found via web search."""

    title: str = Field(..., description="Title of the connection")
    explanation: str = Field(..., description="How this connects to the dream")
    source: str | None = Field(None, description="Source URL if found via search")


class DreamAnalysis(BaseModel):
    """Structured output from the AI dream analysis."""

    summary: str = Field(..., description="A poetic one-sentence summary of the dream")
    archetype: str = Field(..., description="The Jungian archetype this dream evokes")
    symbols: list[DreamSymbol] = Field(..., description="Key symbols and their meanings")
    connections: list[DreamConnection] = Field(
        default_factory=list, description="Surprising real-world connections"
    )
    hidden_message: str = Field(
        ..., description="The 'hidden message' your subconscious is sending you"
    )
    dream_score: int = Field(
        ..., ge=1, le=100, description="How wild this dream is on a scale of 1-100"
    )
    recommended_song: str = Field(
        ..., description="A real song that matches this dream's energy"
    )


class DreamResponse(BaseModel):
    """API response wrapper for dream analysis."""

    analysis: DreamAnalysis
    engine_used: str = Field(..., description="Which Subconscious engine was used")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None
