from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import verify_token
from app.services.llm_client import ask_llm
from app.services.json_utils import extract_json_array

router = APIRouter()

MIN_CHARS = 10
MAX_CHARS = 1500

ANGLES = ["Visual Metaphor", "Clever Wordplay", "Unexpected Scale"]

SYSTEM_PROMPT = (
    "You are an award-winning creative director, the kind whose print and "
    "billboard work wins Cannes Lions and D&AD golds. Your entire job is "
    "inventing ONE surprising visual idea per concept - something a viewer "
    "would stop and look twice at - and pairing it with a short headline "
    "that only makes sense once they've seen the visual. "
    "\n\n"
    "You NEVER write generic benefit statements ('great sound', 'save time', "
    "'built for you'). Every concept must reframe the product as an "
    "unexpected image: an object transformed into something else that makes "
    "the same point visually, an absurd exaggeration of scale, a physical pun "
    "on the product's function or name. The three techniques, one concept "
    "each, in this order:\n"
    "1. Visual Metaphor - the product or its effect is replaced by a visually "
    "striking stand-in object that makes the benefit obvious without saying it.\n"
    "2. Clever Wordplay - the headline turns on a genuine pun or double "
    "meaning tied to something specific about the product, not a generic pun.\n"
    "3. Unexpected Scale - the product's effect is shown through absurd "
    "exaggeration of size, quantity, or physical consequence.\n"
    "\n"
    "For each concept also name a real advertising format it belongs on "
    "(e.g. 'Billboard', 'Transit Poster', 'Magazine Spread', 'Social Static') "
    "- pick whichever format the visual idea would actually work best on.\n"
    "\n"
    "Respond with ONLY a JSON array, no other text, no markdown fences, in "
    "exactly this shape: "
    '[{"angle": "<one of the three technique names>", '
    '"format": "<ad format>", '
    '"visual_concept": "<one vivid, concrete sentence describing exactly '
    'what appears in the ad - specific enough a designer could mock it up>", '
    '"headline": "<3-6 words, only makes sense with the visual>", '
    '"why_it_works": "<one sentence explaining the creative logic>"}, ...] '
    "with exactly three objects, one per technique, in the order given."
)


class AdRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    audience: str | None = Field(default=None, max_length=200)


class AdConcept(BaseModel):
    angle: str
    format: str
    visual_concept: str
    headline: str
    why_it_works: str


class AdResponse(BaseModel):
    concepts: list[AdConcept]


@router.post("/api/generate", response_model=AdResponse, dependencies=[Depends(verify_token)])
async def generate_ads(payload: AdRequest):
    description = payload.description.strip()

    if len(description) < MIN_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Give at least {MIN_CHARS} characters of product description - too little to work from.",
        )
    if len(description) > MAX_CHARS:
        description = description[:MAX_CHARS]

    audience_line = f"\nTarget audience: {payload.audience.strip()}" if payload.audience else ""

    prompt = (
        f"Product name: {payload.product_name.strip()}\n"
        f"Description: {description}"
        f"{audience_line}\n\n"
        f"Invent three concepts using these techniques, in this order: {', '.join(ANGLES)}."
    )

    try:
        raw = await ask_llm(prompt, system=SYSTEM_PROMPT)
        parsed = extract_json_array(raw)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Generation failed: {exc}")

    if not isinstance(parsed, list) or len(parsed) == 0:
        raise HTTPException(status_code=502, detail="Model returned no concepts")

    concepts = []
    for item in parsed[:3]:
        concepts.append(
            AdConcept(
                angle=str(item.get("angle", "")).strip() or "Concept",
                format=str(item.get("format", "")).strip() or "Poster",
                visual_concept=str(item.get("visual_concept", "")).strip() or "—",
                headline=str(item.get("headline", "")).strip() or "—",
                why_it_works=str(item.get("why_it_works", "")).strip() or "",
            )
        )

    return AdResponse(concepts=concepts)
