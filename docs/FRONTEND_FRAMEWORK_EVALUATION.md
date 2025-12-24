# Frontend Framework Evaluation: React + Vite vs Next.js

> Last updated: 2024-12-24

## Context

This evaluation was conducted after deciding to adopt Supabase for the backend. The key question: should we use plain React + Vite (original plan) or switch to Next.js?

**Decision context:**
- Supabase adopted for database/backend
- Personal project (single user)
- Phase 6 (RAG Chat) requires Claude API calls
- Evaluating Vercel for deployment

---

## What's the Relationship?

**Next.js is built on top of React.** It's not an alternative—it's React with additional features and opinions.

```
React (library)
  └── You build everything yourself: routing, data fetching, build config

Next.js (framework)
  └── React + routing + data fetching + build tooling + server capabilities
```

Think of it like:
- **React** = engine
- **Next.js** = complete car built around that engine

---

## Original Plan: React + Vite

From `SEMANTIC_SEARCH_DESIGN.md`:
```
- React - Industry standard, large ecosystem, Claude-friendly
- Vite - Fast dev server and build tool
- React Router - Client-side routing
- Tailwind + shadcn/ui - Styling
```

This is a **client-side only** setup:
1. Vite builds React app into static HTML/JS/CSS
2. Browser downloads everything upfront
3. All rendering happens in the browser
4. API calls go to backend (Supabase)

---

## What Next.js Adds

| Feature | React + Vite | Next.js |
|---------|--------------|---------|
| **Routing** | React Router (manual setup) | File-based (automatic) |
| **Build tool** | Vite (separate config) | Built-in (zero config) |
| **API routes** | Need separate backend | Built-in `/app/api/` |
| **Server rendering** | No | Yes (SSR, SSG, ISR) |
| **Image optimization** | Manual or library | Built-in `<Image>` |
| **Font optimization** | Manual | Built-in `next/font` |
| **Metadata/SEO** | Manual `<head>` management | Built-in Metadata API |
| **Middleware** | Not available | Edge middleware |
| **Deployment** | Any static host | Optimized for Vercel |

---

## Deep Dive: Key Differences

### 1. Routing

**React + Vite + React Router:**
```jsx
// You manually define routes
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/post/:id" element={<PostDetail />} />
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**Next.js (App Router):**
```
app/
├── page.tsx           → /
├── search/
│   └── page.tsx       → /search
├── post/
│   └── [id]/
│       └── page.tsx   → /post/:id
└── chat/
    └── page.tsx       → /chat
```

No router configuration needed. File structure *is* the routing.

**Verdict:** Next.js is cleaner, but React Router is fine. Minor difference.

---

### 2. API Routes (Critical for This Project)

**React + Vite:**
- Frontend only—cannot run server code
- All API calls must go to external backend (Supabase, FastAPI)
- Claude API key must live somewhere else (can't be in browser)

**Next.js:**
```typescript
// app/api/chat/route.ts - runs on server, not in browser
import Anthropic from '@anthropic-ai/sdk';

export async function POST(request: Request) {
  const { message, context } = await request.json();

  const anthropic = new Anthropic({
    apiKey: process.env.CLAUDE_API_KEY  // Safe! Never sent to browser
  });

  const response = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    messages: [{ role: 'user', content: message }],
    // ... RAG context
  });

  return Response.json({ response: response.content });
}
```

**This is significant for Phase 6 (RAG Chat):**

| Approach | Where Claude API is called | API key security |
|----------|---------------------------|------------------|
| React + Vite | Separate backend (VPS or Vercel Function) | Key on backend |
| Next.js | Built-in API route | Key in Next.js env |

With Next.js, no separate backend needed for Claude calls.

---

### 3. Server vs Client Rendering

**React + Vite (Client-Side Rendering):**
```
User visits /search
  → Browser downloads JS bundle (~500KB)
  → React renders loading spinner
  → Fetch data from Supabase
  → React renders results

Total time to content: 1-3 seconds (depends on network)
```

**Next.js (Server-Side Rendering):**
```
User visits /search
  → Server fetches data from Supabase
  → Server renders HTML with data
  → Browser receives complete HTML
  → JS hydrates for interactivity

Total time to content: 0.5-1 second
```

**For this project:** Since it's personal and single-user, this performance difference is minor.

---

### 4. Deployment

**React + Vite:**
- Builds to static files (`dist/` folder)
- Deploy anywhere: Vercel, Netlify, VPS, S3, GitHub Pages
- No server needed (it's just files)

**Next.js:**
- Can build to static files (if no server features used)
- **Or** needs a Node.js server (if using API routes, SSR)
- Optimized for Vercel, but works on VPS, Railway, Fly.io, etc.

If using Next.js API routes for Claude, a server runtime is required—not just static hosting.

---

## Architecture Comparison

### Option A: React + Vite + Supabase

```
┌──────────────────────────────────────────────────────┐
│                    Vercel (or VPS)                   │
│           React + Vite (static files)                │
│                                                      │
│   Browser ──→ Supabase (data, auth, vectors)         │
│           └─→ ??? (Claude API calls)                 │
└──────────────────────────────────────────────────────┘
```

**Problem:** Where do Claude API calls happen?
- Can't call Claude from browser (exposes API key)
- Need either:
  - Vercel Edge Function (separate from React app)
  - Supabase Edge Function
  - Separate backend on VPS

### Option B: Next.js + Supabase

```
┌──────────────────────────────────────────────────────┐
│                       Vercel                         │
│                      Next.js                         │
│   ┌─────────────────┬────────────────────────────┐   │
│   │  React Frontend │  API Routes (/api/chat)    │   │
│   │  (pages)        │  (Claude calls, server)    │   │
│   └────────┬────────┴─────────────┬──────────────┘   │
└────────────┼──────────────────────┼──────────────────┘
             │                      │
             ▼                      ▼
┌────────────────────────┐    ┌─────────────────┐
│       Supabase         │    │   Claude API    │
│  (data, vectors, auth) │    │   (via server)  │
└────────────────────────┘    └─────────────────┘
```

**Simpler:** Everything in one Next.js app. No separate backend needed.

---

## Pros & Cons Summary

### React + Vite

**Pros:**
- Simpler mental model (just a frontend)
- Faster dev server startup
- Smaller bundle (no Next.js overhead)
- Deploy anywhere as static files
- More control over build configuration
- No framework lock-in

**Cons:**
- Need separate backend for Claude API calls
- Manual routing setup
- No built-in image optimization
- No server rendering (minor for personal use)
- More configuration (Vite, React Router, etc.)

### Next.js

**Pros:**
- API routes solve Claude API key problem
- File-based routing (less boilerplate)
- Zero-config (works out of the box)
- Built-in optimizations (images, fonts, code splitting)
- Excellent Vercel integration
- Server components for performance (optional)
- Large ecosystem, lots of examples

**Cons:**
- More complex (client vs server components)
- Larger framework to learn
- Needs server runtime if using API routes
- Opinionated (less flexibility)
- Heavier than plain React

---

## The Deciding Factor: Where Does Claude API Live?

This is the critical architectural question for Phase 6 (RAG Chat).

**If React + Vite:**
- Option 1: Supabase Edge Functions (call Claude from there)
- Option 2: Keep minimal FastAPI on VPS just for `/api/chat`
- Option 3: Vercel Edge Functions (separate from React app)

**If Next.js:**
- Claude calls live in `/app/api/chat/route.ts`
- No separate backend needed
- Deploy as one unit to Vercel

---

## Recommended Architecture: Next.js + Supabase + Vercel

```
┌─────────────────── Vercel ───────────────────┐
│                   Next.js                    │
│  /app                                        │
│  ├── page.tsx          (home)                │
│  ├── search/page.tsx   (search UI)           │
│  ├── post/[id]/page.tsx (post detail)        │
│  ├── chat/page.tsx     (RAG chat UI)         │
│  └── api/                                    │
│      └── chat/route.ts (Claude API calls)    │
└──────────────────────┬───────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────┐              ┌──────────────┐
│   Supabase    │              │  Claude API  │
│  PostgreSQL   │              │  (from api/) │
│  pgvector     │              └──────────────┘
│  Realtime     │
└───────────────┘
        ▲
        │
┌───────┴───────┐
│  Hetzner VPS  │
│ Telegram Bot  │
│ (writes to    │
│  Supabase)    │
└───────────────┘
```

**What runs where:**
- **Vercel**: Next.js (frontend + API routes)
- **Supabase**: All data (posts, vectors, sessions)
- **Hetzner VPS**: Only the Telegram bot

The VPS becomes much simpler—just running the Telegram bot.

---

## Decision Matrix

| If you want... | Choose... |
|----------------|-----------|
| Simpler mental model, more control | React + Vite |
| Built-in Claude API solution, less config | Next.js |
| Maximum Vercel/Supabase synergy | Next.js |
| Lighter bundle, faster dev startup | React + Vite |
| More examples/tutorials available | Next.js |

---

## Recommendation

### For This Project: **Next.js**

Reasoning:

1. **Claude API routes built-in** — Solves Phase 6 architecture cleanly
2. **Supabase + Next.js is a well-documented pattern** — Lots of examples
3. **No existing React preference** — No migration cost
4. **Vercel deployment is seamless** — Since Vercel is being evaluated
5. **File-based routing is cleaner** — Less boilerplate for planned pages
6. **shadcn/ui works great with Next.js** — First-class support

The main "con" (complexity) is mitigated because:
- Can ignore advanced features (Server Components, ISR) initially
- Start with simple client components, add server features if needed
- The App Router is now stable and well-documented

---

## If React + Vite Were Chosen Instead

Totally valid. Would need to decide where Claude API calls happen:
- **Easiest**: Supabase Edge Functions
- **Most control**: Minimal FastAPI on VPS

---

## Impact on Other Decisions

### Vercel Becomes More Attractive

With Next.js:
- Vercel is the optimal deployment target
- Zero-config deployment
- API routes work seamlessly
- Preview deployments for each branch

### VPS Role Shrinks

With Next.js + Supabase + Vercel:
- VPS only runs Telegram bot
- No FastAPI needed
- No Nginx configuration for frontend
- Simpler infrastructure overall

### shadcn/ui Remains the Same

shadcn/ui works with both:
- React + Vite: Full support
- Next.js: First-class support, slightly easier setup

---

## Updated Tech Stack

**Before (original plan):**
```
Frontend: React + Vite + React Router
Backend:  FastAPI
Database: ChromaDB + JSON files
Hosting:  Hetzner VPS (everything)
```

**After (with all evaluations):**
```
Frontend: Next.js (React + built-in routing + API routes)
Backend:  Supabase (auto-generated API) + Next.js API routes (Claude)
Database: Supabase PostgreSQL + pgvector
Hosting:  Vercel (Next.js) + Supabase (data) + Hetzner VPS (bot only)
```

---

## References

- [Next.js Documentation](https://nextjs.org/docs)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Supabase + Next.js Guide](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Vercel + Next.js](https://vercel.com/docs/frameworks/nextjs)
- [shadcn/ui + Next.js](https://ui.shadcn.com/docs/installation/next)
