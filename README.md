# Prompt Engineering Platform — Capstone Project

A zero-cost, production-style platform for managing, testing, and monitoring AI prompts.
Built with Streamlit + Google Gemini (free tier) + Hugging Face Inference API (free tier).

## Features
- **Prompt Manager** — create prompts, auto-versioned (v1, v2, v3...)
- **A/B Testing** — run one prompt against two different models, compare speed/length/cost
- **Analytics Dashboard** — charts of response time and cost over all tests run
- **Cost Tracker** — estimates paid-tier-equivalent cost, shows $0 actual spend

## 1. Get free API keys (5 minutes)

**Google Gemini (free tier):**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with a Google account
3. Click "Create API Key" — copy it

**Hugging Face (free tier):**
1. Go to https://huggingface.co/settings/tokens
2. Sign up / log in
3. Click "New token" → role "Read" → copy it

Neither requires a credit card.

## 2. Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

It opens at `http://localhost:8501`. Paste your two API keys into the sidebar.

## 3. Deploy for free (optional, gives you a public URL)

1. Push this folder to a public GitHub repo
2. Go to https://share.streamlit.io
3. Sign in with GitHub → "New app" → select your repo → main file `app.py`
4. Click Deploy — you get a live URL in ~2 minutes

Your API keys are entered by whoever visits the app (or you can set them as
"Secrets" in Streamlit Cloud settings so they're pre-filled).

## Talking points for your presentation

- **Multi-API integration**: Gemini + Hugging Face, architected so a third
  provider (OpenAI/Anthropic) can be added by writing one more `call_x()` function
- **Versioning**: every save creates a new version instead of overwriting — like Git for prompts
- **A/B testing**: side-by-side output, response time, word count comparison
- **Analytics**: time-series charts built from logged test history
- **Cost tracking**: uses real published per-token pricing to show what this
  *would* cost on a paid tier, while actual spend is $0 — a genuine selling
  point for a startup/small team use case
- **Deployment**: live on Streamlit Community Cloud, no server cost

## Honest scope note (for Q&A)

To hit a zero-cost, one-night build, this version simplifies a few things
from a full production spec:
- No user authentication (single-user demo)
- Two providers instead of three (easy to extend)
- JSON file storage instead of a database (fine for demo scale)

These are natural "next steps" to mention if asked how you'd take it further.
