# ShimaVault Frontend

Next.js (App Router) + TypeScript + Tailwind frontend: channel search, VOD/clip/chat
browsing, and the RAG chatbot UI. Talks to the [backend](../backend) — never to Twitch
directly.

## Setup

```bash
npm install
cp .env.example .env.local   # adjust API_URL if the backend isn't on the default port
```

## Run

```bash
npm run dev
```

- App: http://localhost:3000
- Requires the backend running at the URL in `API_URL` (defaults to `http://localhost:8000/api/v1`).

## Lint / types

```bash
npm run lint
npx tsc --noEmit
```

## Layout

```
src/
├── app/           routes (App Router), Server Actions (actions.ts)
├── components/    client components
└── lib/           API client, shared types
```

All backend calls happen server-side (Server Actions/Components) via `src/lib/api.ts` —
`API_URL` is intentionally not `NEXT_PUBLIC_`-prefixed, so it never reaches the browser.
