# Task 01: Install Anthropic SDK

**Completed:** 2026-01-02
**Status:** Done

## What Was Done

1. **Installed `@anthropic-ai/sdk`** (v0.71.2)
   - Ran `npm install @anthropic-ai/sdk` in `web/` directory
   - Package added to dependencies in `package.json`

2. **Created `.env.example`**
   - No `.env.example` existed previously
   - Created `web/.env.example` with template for:
     - `NEXT_PUBLIC_SUPABASE_URL`
     - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
     - `ANTHROPIC_API_KEY` (new)

## Files Modified

- `web/package.json` - Added `@anthropic-ai/sdk` dependency

## Files Created

- `web/.env.example` - Environment variable template

## Notes for Next Task

- The Anthropic SDK is ready to use
- Users must add `ANTHROPIC_API_KEY` to their `.env.local`
- SDK docs: https://github.com/anthropics/anthropic-sdk-typescript

## Next Task

Task 02: Create Chat API Route - Build the `/api/chat` endpoint with streaming support.
