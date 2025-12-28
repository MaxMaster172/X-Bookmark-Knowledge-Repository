# Supabase Setup Guide

This guide walks you through setting up Supabase for the X-Bookmark Knowledge Repository.

## Step 1: Create Supabase Account & Project

1. Go to [supabase.com](https://supabase.com) and sign up (free tier is sufficient)
2. Click "New Project"
3. Choose a name (e.g., "x-bookmark-archive")
4. Set a strong database password (save this!)
5. Select a region close to you
6. Click "Create new project"

Wait 2-3 minutes for the project to be ready.

## Step 2: Run Database Schema

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **New Query**
3. Copy the contents of `deploy/sql/001_initial_schema.sql`
4. Paste into the SQL Editor
5. Click **Run** (or Ctrl+Enter)
6. Verify you see "Success. No rows returned" (this is expected)

To verify the tables were created:
- Go to **Table Editor** in the sidebar
- You should see tables: `posts`, `post_media`, `sessions`, `entity_categories`, `entities`, `theses`, etc.

## Step 3: Get API Keys

1. Go to **Project Settings** (gear icon in sidebar)
2. Click **API** in the left menu
3. Copy these values:

| Value | Where to find it |
|-------|------------------|
| **Project URL** | Under "Project URL" |
| **Service Role Key** | Under "Project API keys" → `service_role` (click to reveal) |

> **Security Note**: The `service_role` key has full access. Never expose it in frontend code. We use it server-side only.

## Step 4: Set Environment Variables

### On your local machine (for testing):

**Windows (PowerShell):**
```powershell
$env:SUPABASE_URL = "https://your-project-id.supabase.co"
$env:SUPABASE_SERVICE_KEY = "your-service-role-key"
```

**Windows (Command Prompt):**
```cmd
set SUPABASE_URL=https://your-project-id.supabase.co
set SUPABASE_SERVICE_KEY=your-service-role-key
```

**Linux/macOS:**
```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-role-key"
```

### On your VPS (for production):

Add to your `.bashrc` or create a `.env` file:
```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-role-key"
```

## Step 5: Run the Migration

Once environment variables are set:

```bash
# Preview what will be migrated
python scripts/migrate_to_supabase.py --dry-run

# Execute the migration
python scripts/migrate_to_supabase.py
```

The migration will:
1. Read all posts from `archive/posts/**/*.md`
2. Generate embeddings using the BGE model
3. Insert posts with embeddings into Supabase

## Step 6: Verify Migration

1. Go to your Supabase **Table Editor**
2. Click on the `posts` table
3. You should see your migrated posts with all metadata
4. Check that the `embedding` column has data (shows as `[...]`)

## Troubleshooting

### "Supabase credentials required" error
Make sure environment variables are set in your current terminal session.

### "relation does not exist" error
The schema hasn't been created. Run `001_initial_schema.sql` in SQL Editor.

### Connection timeout
Check your internet connection and that the Supabase project URL is correct.

### Embedding model loading slowly
The BGE model downloads on first run (~130MB). This is normal.

## Next Steps

After migration:
1. Update the Telegram bot to write to Supabase (Phase 2)
2. Test search functionality
3. Build the Next.js frontend (Phase 4)

---

## Reference: Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Your project URL | Yes |
| `SUPABASE_SERVICE_KEY` | Service role key (server-side only) | Yes |
| `SUPABASE_ANON_KEY` | Anonymous key (for frontend, later) | For web app |
