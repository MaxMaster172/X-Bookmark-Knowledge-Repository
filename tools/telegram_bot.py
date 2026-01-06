#!/usr/bin/env python3
"""
Telegram bot for archiving X/Twitter posts.

Share a post from X to this bot, and it will:
1. Fetch the full thread (if applicable)
2. Archive it to Supabase (PostgreSQL + pgvector)
3. Analyze with Claude for entities and theses (knowledge graph)

Environment variables required:
- TELEGRAM_BOT_TOKEN: Your Telegram bot token from @BotFather
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_SERVICE_KEY: Your Supabase service role key

Optional:
- ALLOWED_TELEGRAM_USERS: Comma-separated list of allowed user IDs
- ENABLE_KNOWLEDGE_GRAPH: Enable Claude analysis (default: true)
- ANTHROPIC_API_KEY: Required if ENABLE_KNOWLEDGE_GRAPH is true
"""

import os
import re
import sys
import html
import logging
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    # Look for .env in both current directory and parent directory
    env_paths = [
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not installed, use system environment variables

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Add directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # For src/
sys.path.insert(0, str(Path(__file__).parent))  # For twitter_fetcher

from twitter_fetcher import fetch_thread, extract_tweet_id, Thread
from src.supabase.client import get_supabase_client, SupabaseClient
from src.embeddings.service import get_embedding_service, EmbeddingService
from src.vision import get_image_extractor, ImageExtractor
from src.knowledge_graph import PostAnalyzer, get_post_analyzer, ANALYSIS_CONFIG

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Lazy-loaded singletons
_supabase_client: SupabaseClient = None
_embedding_service: EmbeddingService = None
_image_extractor: ImageExtractor = None
_post_analyzer: PostAnalyzer = None

# Image extraction settings
ENABLE_IMAGE_EXTRACTION = os.environ.get("ENABLE_IMAGE_EXTRACTION", "true").lower() == "true"
MAX_IMAGES_TO_EXTRACT = int(os.environ.get("MAX_IMAGES_TO_EXTRACT", "4"))


def get_db() -> SupabaseClient:
    """Get the Supabase client (lazy singleton)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client


def get_embeddings() -> EmbeddingService:
    """Get the embedding service (lazy singleton)."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = get_embedding_service()
    return _embedding_service


def get_vision() -> ImageExtractor:
    """Get the image extractor (lazy singleton)."""
    global _image_extractor
    if _image_extractor is None:
        try:
            _image_extractor = get_image_extractor()
        except ValueError as e:
            logger.warning(f"Image extraction disabled: {e}")
            return None
    return _image_extractor


def get_analyzer() -> PostAnalyzer:
    """Get the post analyzer (lazy singleton)."""
    global _post_analyzer
    if _post_analyzer is None:
        try:
            _post_analyzer = get_post_analyzer(get_db())
        except ValueError as e:
            logger.warning(f"Post analysis disabled: {e}")
            return None
    return _post_analyzer


def escape_html_text(text: str) -> str:
    """Escape text for Telegram HTML parse mode."""
    return html.escape(text)


async def reply_text(update: Update, text: str, **kwargs):
    """Reply to user in both message and callback query contexts.

    When called from a callback query handler, uses reply_text on the message.
    When called from a message handler, uses reply_text directly.
    """
    if update.callback_query:
        return await update.callback_query.message.reply_text(text, **kwargs)
    elif update.message:
        return await update.message.reply_text(text, **kwargs)
    else:
        raise ValueError("Update has neither callback_query nor message")


def check_duplicate_supabase(post_id: str) -> bool:
    """Check if a post already exists in Supabase."""
    try:
        return get_db().post_exists(post_id)
    except Exception as e:
        logger.warning(f"Failed to check duplicate in Supabase: {e}")
        return False


# Conversation states (simplified - removed ADD_TAGS, ADD_TOPICS, ADD_NOTES)
WAITING_FOR_URL, CONFIRM_CONTENT, REVIEW_ANALYSIS, EDIT_ANALYSIS = range(4)

# Knowledge graph analysis settings
ENABLE_KNOWLEDGE_GRAPH = os.environ.get("ENABLE_KNOWLEDGE_GRAPH", "true").lower() == "true"

# Get bot token from environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Allowed user IDs (optional security)
ALLOWED_USERS = os.environ.get("ALLOWED_TELEGRAM_USERS", "").split(",")
ALLOWED_USERS = [int(uid.strip()) for uid in ALLOWED_USERS if uid.strip()]


def is_allowed(user_id: int) -> bool:
    """Check if user is allowed to use the bot."""
    if not ALLOWED_USERS:
        return True  # No restrictions if not configured
    return user_id in ALLOWED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📚 <b>X/Twitter Archive Bot</b>\n\n"
        "Share a post from X/Twitter with me and I'll archive it for you.\n\n"
        "You can:\n"
        "• Share directly from the X app\n"
        "• Paste a tweet URL\n"
        "• Send me a link\n\n"
        "I'll fetch the full thread and ask you for tags.",
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "<b>Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - Show archive statistics\n"
        "/recent - Show recently archived posts\n"
        "/search &lt;query&gt; - Search your archive\n"
        "/cancel - Cancel current operation\n\n"
        "<b>Usage:</b>\n"
        "Just share or paste an X/Twitter link!",
        parse_mode="HTML"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show archive statistics from Supabase."""
    if not is_allowed(update.effective_user.id):
        return

    try:
        db_stats = get_db().get_stats()
        post_count = db_stats.get("total_posts", 0)
        author_count = db_stats.get("unique_authors", 0)
        tag_count = db_stats.get("unique_tags", 0)

        await update.message.reply_text(
            f"📊 <b>Archive Statistics</b>\n\n"
            f"Total posts: {post_count}\n"
            f"Unique authors: {author_count}\n"
            f"Unique tags: {tag_count}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        await update.message.reply_text(
            "❌ Failed to load statistics. Please try again."
        )


async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recently archived posts from Supabase."""
    if not is_allowed(update.effective_user.id):
        return

    try:
        posts = get_db().get_recent_posts(limit=5)

        if not posts:
            await update.message.reply_text("No posts archived yet!")
            return

        lines = ["📝 <b>Recent Archives:</b>\n"]
        for post in posts:
            author = escape_html_text(post.get("author_handle", "unknown"))
            tags_list = post.get("tags", []) or []
            tags = escape_html_text(", ".join(tags_list[:3])) if tags_list else "no tags"
            lines.append(f"• @{author} - {tags}")

        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to get recent posts: {e}")
        await update.message.reply_text(
            "❌ Failed to load recent posts. Please try again."
        )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search the archive using semantic vector search."""
    if not is_allowed(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "<b>Usage:</b> /search &lt;query&gt;\n\n"
            "Search your archive semantically.\n\n"
            "<b>Examples:</b>\n"
            "• /search machine learning tutorials\n"
            "• /search investment thesis\n"
            "• /search debugging tips",
            parse_mode="HTML"
        )
        return

    query = " ".join(context.args)
    await semantic_search(update, query)


async def semantic_search(update: Update, query: str):
    """Perform semantic search using vector similarity."""
    try:
        # Generate query embedding
        query_embedding = get_embeddings().generate_for_query(query)

        # Search in Supabase
        results = get_db().search_posts(
            query_embedding=query_embedding,
            match_threshold=0.5,  # Lower threshold for more results
            match_count=10
        )

        if not results:
            await update.message.reply_text(
                f"No posts found matching '<b>{escape_html_text(query)}</b>'\n\n"
                "Try a different search term.",
                parse_mode="HTML"
            )
            return

        lines = [f"🔍 Found {len(results)} posts for '<b>{escape_html_text(query)}</b>':\n"]
        for post in results:
            author = escape_html_text(post.get("author_handle", "unknown"))
            similarity = post.get("similarity", 0)
            # Show similarity as percentage
            sim_pct = int(similarity * 100)

            # Get tags if available
            tags_list = post.get("tags", []) or []
            tags = escape_html_text(", ".join(tags_list[:2])) if tags_list else ""

            # Format: author (score%) - tags
            if tags:
                lines.append(f"• @{author} ({sim_pct}%) - {tags}")
            else:
                lines.append(f"• @{author} ({sim_pct}%)")

        await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        await update.message.reply_text(
            "❌ Search failed. Please try again.",
            parse_mode="HTML"
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation."""
    context.user_data.clear()
    await update.message.reply_text("Operation cancelled. Send me another link anytime!")
    return ConversationHandler.END


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming message that might contain a URL."""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return ConversationHandler.END

    message_text = update.message.text

    # Extract URL from message
    url_pattern = r'https?://(?:twitter|x|fxtwitter|vxtwitter)\.com/\w+/status/\d+'
    match = re.search(url_pattern, message_text)

    if not match:
        await update.message.reply_text(
            "I couldn't find an X/Twitter URL in that message.\n"
            "Please share a post from X or paste a tweet link."
        )
        return ConversationHandler.END

    url = match.group(0)
    # Normalize URL to x.com
    url = re.sub(r'(fxtwitter|vxtwitter|twitter)', 'x', url)

    # Check for duplicate in Supabase
    post_id = extract_tweet_id(url)
    if post_id and check_duplicate_supabase(post_id):
        await update.message.reply_text(
            "⚠️ This post is already in your archive!\n\n"
            "Send me a different link, or search with /search"
        )
        return ConversationHandler.END

    await update.message.reply_text("🔍 Fetching thread...")

    # Fetch the thread
    thread = fetch_thread(url)

    if not thread:
        await update.message.reply_text(
            "❌ Couldn't fetch that post. It might be:\n"
            "• Private or deleted\n"
            "• From a protected account\n"
            "• A temporary API issue\n\n"
            "Try again or paste the content manually."
        )
        return ConversationHandler.END

    # Store thread in context
    context.user_data["thread"] = thread
    context.user_data["url"] = url

    # Format preview
    preview = thread.full_text
    if len(preview) > 500:
        preview = preview[:500] + "..."

    thread_info = ""
    if thread.total_count > 1:
        thread_info = f"\n\n🧵 Thread: {thread.total_count} posts"

    keyboard = [
        [
            InlineKeyboardButton("✅ Archive", callback_data="quick"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use plain text to avoid markdown parsing issues
    await update.message.reply_text(
        f"@{thread.author_handle}{thread_info}\n\n"
        f"{preview}\n\n"
        "Archive this post?",
        reply_markup=reply_markup
    )

    return CONFIRM_CONTENT


async def confirm_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation button."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("Cancelled. Send me another link anytime!")
        return ConversationHandler.END

    # Quick save - skip all prompts
    if query.data == "quick":
        await query.edit_message_text("⚡ Quick saving...")

        context.user_data["tags"] = []
        context.user_data["topics"] = []
        context.user_data["notes"] = None

        try:
            post_id = save_archived_post(context.user_data)
            context.user_data["saved_post_id"] = post_id
            thread = context.user_data["thread"]

            await query.edit_message_text(
                f"⚡ Quick Saved!\n\n"
                f"@{thread.author_handle}'s post archived."
            )

            # Trigger knowledge graph analysis if enabled
            if ENABLE_KNOWLEDGE_GRAPH:
                return await analyze_post_for_knowledge_graph(update, context)

        except Exception as e:
            logger.error(f"Failed to save post: {e}")
            await query.edit_message_text(
                f"❌ Failed to save: {str(e)}\n\n"
                "Please try again or report this issue."
            )

        context.user_data.clear()
        return ConversationHandler.END


async def analyze_post_for_knowledge_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze the saved post for entities and theses.

    Works in both message and callback query contexts (quick save vs manual save).
    """
    analyzer = get_analyzer()

    if not analyzer:
        await reply_text(update, "Send me another link anytime!")
        context.user_data.clear()
        return ConversationHandler.END

    # Check rate limit
    if not get_db().check_analysis_limit(ANALYSIS_CONFIG["max_daily_analysis"]):
        await reply_text(
            update,
            "📊 Daily analysis limit reached. Post saved without knowledge graph analysis.\n\n"
            "Send me another link anytime!"
        )
        context.user_data.clear()
        return ConversationHandler.END

    await reply_text(update, "🔍 Analyzing for knowledge graph...")

    thread = context.user_data["thread"]
    content = thread.full_text

    try:
        # Analyze the post
        analysis = analyzer.analyze_post(
            content=content,
            author=thread.author_handle,
            tags=context.user_data.get("tags", []),
            topics=context.user_data.get("topics", []),
            notes=context.user_data.get("notes"),
        )

        context.user_data["analysis"] = analysis

        if not analysis.has_results:
            await reply_text(
                update,
                "No entities or theses detected in this post.\n\n"
                "Send me another link anytime!"
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Present analysis results with inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data="kg_accept"),
                InlineKeyboardButton("⏭️ Skip", callback_data="kg_skip"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await reply_text(
            update,
            f"📊 <b>Knowledge Graph Analysis:</b>\n\n"
            f"{analysis.to_display_text()}\n\n"
            f"Add these to your knowledge graph?",
            parse_mode="HTML",
            reply_markup=reply_markup
        )

        return REVIEW_ANALYSIS

    except Exception as e:
        logger.error(f"Knowledge graph analysis failed: {e}")
        await reply_text(
            update,
            "Knowledge graph analysis failed. Post saved without links.\n\n"
            "Send me another link anytime!"
        )
        context.user_data.clear()
        return ConversationHandler.END


async def handle_analysis_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Accept/Skip response for knowledge graph analysis."""
    query = update.callback_query

    # Check if we've already processed this callback (prevents double-processing)
    callback_id = query.id
    processed_callbacks = context.user_data.get("processed_callbacks", set())
    if callback_id in processed_callbacks:
        await query.answer()  # Acknowledge but don't reprocess
        return REVIEW_ANALYSIS  # Stay in same state

    # Mark this callback as processed
    processed_callbacks.add(callback_id)
    context.user_data["processed_callbacks"] = processed_callbacks

    # Answer the callback immediately to stop the "loading" state on button
    await query.answer()

    if query.data == "kg_skip":
        await query.edit_message_text(
            "⏭️ Skipped knowledge graph linking.\n\n"
            "Send me another link anytime!"
        )
        context.user_data.clear()
        return ConversationHandler.END

    if query.data == "kg_accept":
        analysis = context.user_data.get("analysis")
        post_id = context.user_data.get("saved_post_id")

        if not analysis or not post_id:
            await query.edit_message_text(
                "❌ Something went wrong. Post was saved but not linked.\n\n"
                "Send me another link anytime!"
            )
            context.user_data.clear()
            return ConversationHandler.END

        # Show immediate feedback that we're processing
        try:
            await query.edit_message_text("⏳ Updating knowledge graph...")
        except Exception:
            pass  # Message might already be edited, continue anyway

        try:
            # Apply the analysis
            analyzer = get_analyzer()
            result = analyzer.apply_analysis(post_id, analysis)

            created = result["created"]
            linked = result["linked"]

            summary_parts = []
            if created["entities"] > 0:
                summary_parts.append(f"{created['entities']} new entities")
            if created["theses"] > 0:
                summary_parts.append(f"{created['theses']} new theses")
            if linked["entities"] > 0:
                summary_parts.append(f"{linked['entities']} entity links")
            if linked["theses"] > 0:
                summary_parts.append(f"{linked['theses']} thesis links")

            summary = ", ".join(summary_parts) if summary_parts else "No changes"

            await query.edit_message_text(
                f"✅ Knowledge graph updated!\n\n"
                f"{summary}\n\n"
                f"Send me another link anytime!"
            )

        except Exception as e:
            logger.error(f"Failed to apply analysis: {e}")
            await query.edit_message_text(
                f"❌ Failed to update knowledge graph: {str(e)}\n\n"
                "Post was saved but not linked.\n"
                "Send me another link anytime!"
            )

    context.user_data.clear()
    return ConversationHandler.END


def save_archived_post(data: dict) -> str:
    """Save the post to Supabase with embedding."""
    thread: Thread = data["thread"]
    url = data["url"]

    post_id = extract_tweet_id(url)
    archived_at = datetime.now()

    # Build content - combine thread if multiple posts
    if thread.total_count > 1:
        content_parts = []
        for i, tweet in enumerate(thread.tweets, 1):
            content_parts.append(f"[{i}/{thread.total_count}]\n{tweet.text}")
        content = "\n\n---\n\n".join(content_parts)
    else:
        content = thread.tweets[0].text

    # Extract image descriptions if enabled
    image_descriptions = []
    image_extraction_results = {}  # url -> {description, category, extraction_model}

    if ENABLE_IMAGE_EXTRACTION:
        extractor = get_vision()
        if extractor:
            images_processed = 0
            for tweet in thread.tweets:
                for m in tweet.media:
                    if images_processed >= MAX_IMAGES_TO_EXTRACT:
                        break
                    if m.get("type") == "image" and m.get("url"):
                        try:
                            logger.info(f"Extracting description for image: {m.get('url')[:50]}...")
                            result = extractor.describe_image(
                                image_url=m.get("url"),
                                post_context=content[:500],  # First 500 chars as context
                            )
                            if result and result.get("description"):
                                image_extraction_results[m.get("url")] = result
                                image_descriptions.append(result["description"])
                                images_processed += 1
                                logger.info(f"Extracted {result['category']} description for image")
                        except Exception as e:
                            logger.warning(f"Image extraction failed: {e}")

    # Build embedding text (content + metadata for better search)
    embed_text = content
    if thread.author_handle:
        embed_text += f"\n\nAuthor: @{thread.author_handle}"
    if data.get("tags"):
        embed_text += f"\nTags: {', '.join(data['tags'])}"
    if data.get("topics"):
        embed_text += f"\nTopics: {', '.join(data['topics'])}"
    if data.get("notes"):
        embed_text += f"\nNotes: {data['notes']}"

    # Add image descriptions to embedding text
    if image_descriptions:
        embed_text += f"\n\nImage content: {' | '.join(image_descriptions)}"

    # Generate embedding
    try:
        embedding = get_embeddings().generate(embed_text)
        logger.info(f"Generated embedding for post {post_id}")
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        embedding = None

    # Handle quoted tweet
    quoted_post_id = None
    quoted_text = None
    quoted_author = None
    quoted_url = None
    for tweet in thread.tweets:
        if tweet.quoted_tweet:
            quoted_post_id = tweet.quoted_tweet.id
            quoted_url = tweet.quoted_tweet.url
            quoted_author = tweet.quoted_tweet.author_handle
            quoted_text = tweet.quoted_tweet.text[:200] if tweet.quoted_tweet.text else None
            break

    # Parse posted_at date
    posted_at = None
    if thread.tweets[0].created_at:
        try:
            # Handle various date formats
            posted_at_str = thread.tweets[0].created_at
            if isinstance(posted_at_str, str):
                posted_at = posted_at_str  # Let Supabase handle ISO format
        except Exception:
            posted_at = None

    # Insert into Supabase
    db = get_db()
    db.insert_post(
        post_id=post_id,
        url=url,
        content=content,
        author_handle=thread.author_handle,
        author_name=thread.author_name,
        posted_at=posted_at,
        archived_at=archived_at,
        archived_via="telegram",
        tags=data.get("tags", []),
        topics=data.get("topics", []),
        notes=data.get("notes"),
        is_thread=thread.total_count > 1,
        quoted_post_id=quoted_post_id,
        quoted_text=quoted_text,
        quoted_author=quoted_author,
        quoted_url=quoted_url,
        embedding=embedding,
    )
    logger.info(f"Saved post {post_id} to Supabase")

    # Insert media items with extraction results
    for tweet in thread.tweets:
        for m in tweet.media:
            try:
                media_url = m.get("url", "")
                extraction = image_extraction_results.get(media_url, {})
                db.insert_media(
                    post_id=post_id,
                    media_type=m.get("type", "image"),
                    url=media_url,
                    category=extraction.get("category"),
                    description=extraction.get("description"),
                    extraction_model=extraction.get("extraction_model"),
                )
            except Exception as e:
                logger.warning(f"Failed to insert media for {post_id}: {e}")

    return post_id


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("\nTo set up the bot:")
        print("1. Message @BotFather on Telegram")
        print("2. Create a new bot with /newbot")
        print("3. Copy the token and set it:")
        print("   export TELEGRAM_BOT_TOKEN='your-token-here'")
        print("\nOptionally restrict users:")
        print("   export ALLOWED_TELEGRAM_USERS='123456789,987654321'")
        return

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for archiving flow (simplified - no manual tags/topics/notes)
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url),
        ],
        states={
            CONFIRM_CONTENT: [CallbackQueryHandler(confirm_content)],
            REVIEW_ANALYSIS: [CallbackQueryHandler(handle_analysis_response)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("recent", recent))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(conv_handler)

    # Start polling
    print("🤖 Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
