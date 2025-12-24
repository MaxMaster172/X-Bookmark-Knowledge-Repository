# Vercel Evaluation for X-Bookmark Knowledge Repository

> Last updated: 2024-12-24

## Context

This evaluation was conducted after deciding to adopt Supabase and Next.js. The question: should we deploy to Vercel or keep everything on the existing Hetzner VPS?

**Decision context:**
- Supabase adopted for database/backend
- Next.js chosen as frontend framework
- Personal project (single user)
- Telegram bot already running on Hetzner VPS

---

## What is Vercel?

Vercel is a **frontend cloud platform** optimized for deploying modern web applications. It's the company behind Next.js.

| Core Feature | Description |
|--------------|-------------|
| **Frontend Hosting** | Deploy React, Next.js, Vue, Svelte, static sites |
| **Edge Network** | Global CDN with 100+ edge locations |
| **Serverless Functions** | Backend API routes that scale automatically |
| **Edge Functions** | Lightweight functions running at CDN edge (~0ms cold start) |
| **Preview Deployments** | Every git branch gets a unique URL |
| **Build Pipeline** | Automatic builds on git push |
| **Analytics** | Web Vitals, performance monitoring |

---

## Original Plan vs Vercel

### Original Plan: Everything on Hetzner VPS

```
┌────────────────────── Hetzner VPS ──────────────────────┐
│   Telegram Bot    │    FastAPI    │    React Frontend   │
│                   │               │    (static files)   │
│                   └───────────────┴─────────────────────│
│                          Nginx reverse proxy            │
└─────────────────────────────────────────────────────────┘
```

### With Vercel + Supabase

```
┌─────────── Vercel ────────────┐
│   Next.js                     │
│   (Frontend + API routes)     │
│   Global CDN                  │
└───────────────┬───────────────┘
                │
    ┌───────────┴───────────┐
    ▼                       ▼
┌───────────┐        ┌──────────────┐
│ Supabase  │        │ Hetzner VPS  │
│ (data)    │        │ (bot only)   │
└───────────┘        └──────────────┘
```

---

## What Vercel Replaces

| Component | Original Plan | With Vercel |
|-----------|---------------|-------------|
| Frontend hosting | Nginx on VPS serving static files | Vercel global CDN |
| SSL certificates | Certbot/Let's Encrypt (manual) | Automatic HTTPS |
| Deployment | SSH + git pull + build + restart | Git push (automatic) |
| API routes | FastAPI on VPS | Next.js API routes on Vercel |
| Preview environments | None (or manual setup) | Automatic per branch |

---

## Pros of Using Vercel

### 1. Zero-Config Deployments

```bash
# Original plan
ssh vps
cd /app && git pull
npm run build
sudo systemctl restart nginx

# With Vercel
git push  # Done. Deployed in ~30 seconds.
```

Every push to `main` deploys automatically. Every PR gets a preview URL.

### 2. Preview Deployments

Each branch gets its own URL:
```
main              → bookmarks.yourdomain.com
feature/chat      → bookmarks-git-feature-chat.vercel.app
fix/search-bug    → bookmarks-git-fix-search-bug.vercel.app
```

Excellent for testing features before merging.

### 3. Global Performance

Frontend assets served from 100+ edge locations:
- Users get the app from the nearest server
- Typical latency: 10-50ms instead of 100-300ms for distant users

For a personal project this matters less, but helpful when accessing from different locations.

### 4. Next.js Optimization

Vercel created Next.js and provides:
- Automatic code splitting
- Image optimization
- Smart caching headers
- Serverless function optimization
- Edge runtime support

### 5. Built-in Analytics

- Core Web Vitals monitoring
- Real user performance data
- No additional setup needed

### 6. Generous Free Tier

- 100GB bandwidth/month
- Unlimited static sites
- Serverless function hours included
- Custom domains with automatic SSL

---

## Cons of Using Vercel

### 1. Split Architecture

Instead of one VPS, now managing:
- Vercel (frontend + API routes)
- Supabase (database)
- Hetzner VPS (Telegram bot)

More services = more things to configure and monitor.

**Mitigation:** Each service does one thing well. Complexity is manageable.

### 2. CORS Configuration

Frontend on Vercel, Supabase elsewhere:
```
Frontend: https://bookmarks.vercel.app
Supabase: https://xxx.supabase.co
```

Need to configure allowed origins in Supabase dashboard.

**Mitigation:** Supabase handles this well; just add Vercel domain to allowed origins.

### 3. Cold Starts for Serverless Functions

If using Vercel Functions for Claude API routes:
- Cold start: 250-500ms for first request
- Subsequent requests: fast

**Mitigation:** For RAG chat, Claude API latency (~1-3s) dominates anyway.

### 4. Vendor Lock-in (Partial)

- Static Next.js: fully portable
- Vercel-specific features (Edge Config, KV): some lock-in
- Next.js itself: portable to other hosts (Railway, Fly.io, self-hosted)

**Mitigation:** Avoid Vercel-specific features; stick to standard Next.js.

### 5. Cost at Scale

Free tier is generous, but:
- Pro plan: $20/month per team member
- Bandwidth overages: $40/100GB

**Mitigation:** Personal use will stay well within free tier.

### 6. Less Control

On VPS: full control over everything.
On Vercel: managed platform with constraints.

**Mitigation:** For this project, Vercel's constraints don't limit any planned features.

---

## Vercel + Supabase: A Common Pairing

These services are frequently used together:

```
┌─────────────────────────────────────────────────────────────┐
│                          Vercel                             │
│   Next.js App                                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Uses @supabase/supabase-js client directly         │   │
│   │  API routes for server-side operations (Claude)     │   │
│   └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Direct connection
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        Supabase                             │
│   PostgreSQL + pgvector + Auth + Realtime + Auto-API        │
└─────────────────────────────────────────────────────────────┘
```

Benefits of the pairing:
- Supabase client works directly from Next.js (client and server)
- No custom backend needed for CRUD operations
- Realtime subscriptions work out of the box
- Well-documented integration pattern

---

## Comparison: All-VPS vs Vercel

| Aspect | All on Hetzner VPS | Vercel + Supabase + VPS |
|--------|-------------------|-------------------------|
| **Deployment** | Manual SSH + restart | Git push auto-deploy |
| **Frontend latency** | Single location | Global edge CDN |
| **Architecture** | Simple, unified | Split, specialized |
| **Cost** | ~$5-10/month VPS only | VPS + free tiers |
| **Debugging** | SSH, full access | Vercel dashboard + logs |
| **Preview deploys** | Manual setup | Automatic per branch |
| **SSL** | Certbot/Let's Encrypt | Automatic |
| **Control** | Full | Partial (frontend) |
| **Scaling** | Manual | Automatic (frontend) |

---

## Cost Analysis

### Vercel Free Tier (Hobby)
- 100 GB bandwidth/month
- 100 GB-hours serverless functions
- Unlimited static deployments
- 1 concurrent build
- Custom domains with SSL

### Expected Usage
- Single user, occasional access
- ~1-10 MB frontend bundle
- ~100-1000 page views/month
- Bandwidth: <1 GB/month

**Verdict:** Free tier is more than sufficient. Would need significant growth to exceed it.

---

## What Runs Where (Final Architecture)

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

**Vercel handles:**
- Next.js frontend (React pages)
- API routes (Claude calls for RAG)
- Global CDN distribution
- Automatic deployments

**Supabase handles:**
- PostgreSQL database
- pgvector for embeddings
- Auto-generated REST API
- Realtime subscriptions

**Hetzner VPS handles:**
- Telegram bot only
- Much simpler than original plan

---

## Decision Matrix

| If you value... | Choose... |
|-----------------|-----------|
| Simple, unified deployment | All on VPS |
| Automatic deploys, preview URLs | Vercel |
| Global frontend performance | Vercel |
| Full control, no external deps | All on VPS |
| Learning modern deployment | Vercel |
| Next.js optimization | Vercel |
| Supabase integration | Vercel (common pairing) |

---

## Recommendation

### For This Project: **Use Vercel**

Reasoning:

1. **Next.js is already chosen** — Vercel is the optimal deployment target
2. **Supabase is already chosen** — Common, well-documented pairing
3. **Zero-config deployment** — Git push and done
4. **Preview deployments** — Valuable for testing features
5. **Free tier sufficient** — No cost for personal use
6. **VPS role simplifies** — Only runs Telegram bot now

The main trade-off (split architecture) is acceptable because:
- Each service is specialized and reliable
- The integration patterns are well-established
- Debugging tools are good on all platforms

---

## References

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel + Next.js](https://vercel.com/docs/frameworks/nextjs)
- [Vercel + Supabase Integration](https://vercel.com/integrations/supabase)
- [Vercel Pricing](https://vercel.com/pricing)
