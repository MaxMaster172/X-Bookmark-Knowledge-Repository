---
date: 2026-01-02T12:00:00+0100
type: plan
status: complete
plan_file: thoughts/shared/plans/PLAN-phase5-rag-chat.md
session_name: x-bookmark
---

# Plan Handoff: Phase 5 RAG Chat Interface

## Summary

Created implementation plan for Phase 5: RAG Chat Interface. The plan covers building a Claude-powered chat with streaming responses, source citations, and rate limiting. 8 tasks identified.

## Plan Created

`thoughts/shared/plans/PLAN-phase5-rag-chat.md`

## Key Technical Decisions

- **LLM**: Claude 4.5 Sonnet (`claude-sonnet-4-5-20250514`) via `@anthropic-ai/sdk` - latest model
- **Streaming**: Server-Sent Events via ReadableStream - simpler than WebSockets, native browser support
- **RAG Context**: Reuse existing `searchPosts()` + browser embeddings (no new infrastructure)
- **Rate Limiting**: 20 messages/hour, client-side localStorage tracking (simple, sufficient for personal use)
- **Citations**: Inline `[1]`, `[2]` markers replaced with clickable badges linking to posts

## Task Overview

1. **Install Anthropic SDK** - Add @anthropic-ai/sdk dependency
2. **Create Chat API Route** - `/api/chat` with streaming Claude calls
3. **Create Chat Types** - Message, ChatState, Source types
4. **Create useChat Hook** - React hook for streaming chat state
5. **Build Chat UI Components** - ChatMessage, ChatInput, SourceCitation, ContextSidebar
6. **Build Chat Page** - `/chat` route with full interface
7. **Add Chat Navigation** - Links in header, home, post detail
8. **Implement Rate Limiting** - Client-side message counting

## Research Findings

- Existing `searchPosts()` at `lib/queries/posts.ts:152-229` - reusable for RAG retrieval
- `useSearch` hook at `hooks/useSearch.ts` - pattern to follow for useChat
- Browser embeddings via Transformers.js already work - no server-side embedding needed
- Sessions table exists in DB schema (`types/database.ts:112-118`) - ready for conversation storage
- Server Components pattern with `force-dynamic` established - follow for chat page

## Assumptions Made

- Claude 3.5 Sonnet is the right model choice (verify cost is acceptable)
- 5 posts as RAG context is sufficient (can adjust later)
- Client-side rate limiting is acceptable (personal use, not protecting against abuse)
- Browser-side embedding generation for user messages is fast enough

## For Next Steps

1. User should review plan at: `thoughts/shared/plans/PLAN-phase5-rag-chat.md`
2. After approval, run `/implement_plan` with the plan path
3. Will need `ANTHROPIC_API_KEY` in `web/.env.local` before testing chat
