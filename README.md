# Ad Maker

Paste a product description, get back three ad copy variants — Bold & Punchy,
Warm & Friendly, and Premium & Minimal — each with a headline, body, and CTA.

## What it does
Sends the product name/description/audience to an LLM (Groq by default) with
a copywriting prompt that forces three genuinely distinct voices instead of
reworded synonyms of the same ad, and parses a strict JSON array back into
copy-able cards.

## How it works
- `app/main.py` — wires routers + serves the static frontend
- `app/routers/generate.py` — the `/api/generate` endpoint, prompt + validation
- `app/services/llm_client.py` — provider-switchable LLM call (`LLM_PROVIDER=groq|anthropic`)
- `app/services/json_utils.py` — shared JSON-array extraction (strips markdown fences)
- `app/static/index.html` — frontend, no build step

## Run locally
```bash
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # fill in GROQ_API_KEY
uvicorn app.main:app --reload
```

## Deploy (Render)
1. Push to a new GitHub repo
2. Render → New → Web Service → connect repo → Docker
3. Environment tab (not .env — that's git-ignored): `GROQ_API_KEY`, `ENVIRONMENT=production`
4. Deploy — health check is `/health`
