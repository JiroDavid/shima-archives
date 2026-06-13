# ShimaVault

A Twitch companion platform for browsing VODs, clips, and chat logs — with synced chat replay and an AI chatbot for querying chat history.

## What it does

- **Browse** VODs (published and unpublished), clips, and chat logs for any channel
- **Watch** VODs with chat replay synced to the video timeline
- **Ask** an AI chatbot about chat history (e.g. _"when did chat go crazy during this VOD?"_) and jump straight to the moment

Two tiers:

- **Public** — search any channel, browse VODs / clips / chat, use the chatbot. No login.
- **Streamer** — sign in with Twitch and invite the bot to your channel for live logging and richer data.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind |
| Backend | FastAPI (Python) |
| Bot | twitchio |
| Database | PostgreSQL |
| Vector store | Chroma (dev) / Pinecone (prod) |
| Player | HLS.js |

## Repository layout

```
shima-archives/
├── backend/    FastAPI app — Twitch API proxy, VOD/chat/clips, RAG query
├── frontend/   Next.js app — browsing, player, chatbot UI
└── bot/        twitchio bot — live chat logging
```

## Development

Each service has its own setup instructions in its directory's `README.md`.

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Twitch + API credentials
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## License

TBD
