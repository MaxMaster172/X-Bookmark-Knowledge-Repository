#!/usr/bin/env python3
"""
Telegram bot for archiving X/Twitter posts.

Share a post from X to this bot, and it will:
1. Fetch the full thread (if applicable)
2. Ask for tags, topics, and notes
3. Archive it to the repository
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path

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

from twitter_fetcher import fetch_thread, extract_tweet_id, Thread
from utils import (
    get_post_path,
    load_index,
    save_index,
    load_tags,
    save_tags,
    ARCHIVE_DIR,
)

import yaml

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_URL, CONFIRM_CONTENT, ADD_TAGS, ADD_TOPICS, ADD_NOTES, SET_IMPORTANCE = range(6)

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
        "📚 *X/Twitter Archive Bot*\n\n"
        "Share a post from X/Twitter with me and I'll archive it for you.\n\n"
        "You can:\n"
        "• Share directly from the X app\n"
        "• Paste a tweet URL\n"
        "• Send me a link\n\n"
        "I'll fetch the full thread and ask you for tags.",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/stats - Show archive statistics\n"
        "/recent - Show recently archived posts\n"
        "/cancel - Cancel current operation\n\n"
        "*Usage:*\n"
        "Just share or paste an X/Twitter link!",
        parse_mode="Markdown"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show archive statistics."""
    if not is_allowed(update.effective_user.id):
        return

    index = load_index()
    tag_data = load_tags()

    post_count = len(index.get("posts", {}))
    tag_count = len(tag_data.get("tags", {}))
    topic_count = len(tag_data.get("topics", {}))

    await update.message.reply_text(
        f"📊 *Archive Statistics*\n\n"
        f"Total posts: {post_count}\n"
        f"Unique tags: {tag_count}\n"
        f"Unique topics: {topic_count}",
        parse_mode="Markdown"
    )


async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recently archived posts."""
    if not is_allowed(update.effective_user.id):
        return

    index = load_index()
    posts = list(index.get("posts", {}).items())

    # Sort by archived date
    posts.sort(key=lambda x: x[1].get("archived_at", ""), reverse=True)

    if not posts:
        await update.message.reply_text("No posts archived yet!")
        return

    lines = ["📝 *Recent Archives:*\n"]
    for post_id, info in posts[:5]:
        author = info.get("author", "unknown")
        tags = ", ".join(info.get("tags", [])) or "no tags"
        lines.append(f"• @{author} - {tags}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


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
        thread_info = f"\n\n🧵 *Thread: {thread.total_count} posts*"

    keyboard = [
        [
            InlineKeyboardButton("✅ Archive This", callback_data="confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"*@{thread.author_handle}*{thread_info}\n\n"
        f"{preview}\n\n"
        "Archive this post?",
        parse_mode="Markdown",
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

    # Ask for tags
    await query.edit_message_text(
        "📏 *Add Tags*\n\n"
        "What tags describe why you're saving this?\n"
        "Examples: insight, reference, tutorial, funny, thread\n\n"
        "Send comma-separated tags, or /skip to skip.",
        parse_mode="Markdown"
    )
    return ADD_TAGS


async def add_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tags input."""
    text = update.message.text.strip()

    if text.lower() == "/skip":
        context.user_data["tags"] = []
    else:
        tags = [t.strip().lower() for t in text.split(",") if t.strip()]
        context.user_data["tags"] = tags

    await update.message.reply_text(
        "📚 *Add Topics*\n\n"
        "What is this post about?\n"
        "Examples: ai, programming, startups, design, crypto\n\n"
        "Send comma-separated topics, or /skip to skip.",
        parse_mode="Markdown"
    )
    return ADD_TOPICS


async def add_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topics input."""
    text = update.message.text.strip()

    if text.lower() == "/skip":
        context.user_data["topics"] = []
    else:
        topics = [t.strip().lower() for t in text.split(",") if t.strip()]
        context.user_data["topics"] = topics

    await update.message.reply_text(
        "📝 *Add Notes*\n\n"
        "Any personal notes about this post?\n"
        "Why did you save it? What's the key takeaway?\n\n"
        "Send your notes, or /skip to skip.",
        parse_mode="Markdown"
    )
    return ADD_NOTES


async def add_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notes input."""
    text = update.message.text.strip()

    if text.lower() == "/skip":
        context.user_data["notes"] = None
    else:
        context.user_data["notes"] = text

    keyboard = [
        [
            InlineKeyboardButton("🔵 Low", callback_data="importance_low"),
            InlineKeyboardButton("🟢 Medium", callback_data="importance_medium"),
        ],
        [
            InlineKeyboardButton("🟡 High", callback_data="importance_high"),
            InlineKeyboardButton("🔴 Critical", callback_data="importance_critical"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⭐ *Set Importance*\n\n"
        "How important is this post to you?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return SET_IMPORTANCE


async def set_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle importance selection and save the post."""
    query = update.callback_query
    await query.answer()

    importance = query.data.replace("importance_", "")
    context.user_data["importance"] = importance

    await query.edit_message_text("💾 Saving to archive...")

    # Save the post
    try:
        file_path = save_archived_post(context.user_data)
        thread = context.user_data["thread"]

        await query.edit_message_text(
            f"✅ *Archived!*\n\n"
            f"@{thread.author_handle}'s post has been saved.\n\n"
            f"📏 Tags: {', '.join(context.user_data.get('tags', [])) or 'none'}\n"
            f"📚 Topics: {', '.join(context.user_data.get('topics', [])) or 'none'}\n"
            f"⭐ Importance: {importance}\n\n"
            f"Send me another link anytime!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to save post: {e}")
        await query.edit_message_text(
            f"❌ Failed to save: {str(e)}\n\n"
            "Please try again or report this issue."
        )

    context.user_data.clear()
    return ConversationHandler.END


def save_archived_post(data: dict) -> Path:
    """Save the post to the archive."""
    thread: Thread = data["thread"]
    url = data["url"]

    post_id = extract_tweet_id(url)
    archived_at = datetime.now()
    file_path = get_post_path(post_id, archived_at)

    # Build content - combine thread if multiple posts
    if thread.total_count > 1:
        content_parts = []
        for i, tweet in enumerate(thread.tweets, 1):
            content_parts.append(f"**[{i}/{thread.total_count}]**\n{tweet.text}")
        content = "\n\n---\n\n".join(content_parts)
    else:
        content = thread.tweets[0].text

    # Build metadata
    metadata = {
        "id": post_id,
        "url": url,
        "author": {
            "handle": thread.author_handle,
            "name": thread.author_name,
        },
        "content": content,
        "archived_at": archived_at.isoformat(),
        "importance": data.get("importance", "medium"),
        "archived_via": "telegram",
    }

    # Thread info
    if thread.total_count > 1:
        metadata["thread"] = {
            "is_thread": True,
            "total": thread.total_count,
            "tweet_ids": [t.id for t in thread.tweets],
        }

    # Optional fields
    if thread.tweets[0].created_at:
        metadata["posted_at"] = thread.tweets[0].created_at

    if data.get("tags"):
        metadata["tags"] = data["tags"]

    if data.get("topics"):
        metadata["topics"] = data["topics"]

    if data.get("notes"):
        metadata["notes"] = data["notes"]

    # Collect all media from thread
    all_media = []
    for tweet in thread.tweets:
        for m in tweet.media:
            all_media.append({
                "type": m.get("type", "image"),
                "url": m.get("url", ""),
            })
    if all_media:
        metadata["media"] = all_media

    # Check for quoted tweets
    for tweet in thread.tweets:
        if tweet.quoted_tweet:
            metadata["quotes"] = {
                "quoted_post_id": tweet.quoted_tweet.id,
                "quoted_url": tweet.quoted_tweet.url,
                "quoted_author": tweet.quoted_tweet.author_handle,
                "quoted_text": tweet.quoted_tweet.text[:200],
            }
            break

    # Write file
    with open(file_path, "w") as f:
        f.write("---\n")
        yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
        f.write("---\n\n")
        f.write(content)
        f.write("\n")

    # Update index
    index = load_index()
    index["posts"][post_id] = {
        "path": str(file_path.relative_to(ARCHIVE_DIR.parent.parent)),
        "author": thread.author_handle,
        "archived_at": archived_at.isoformat(),
        "tags": data.get("tags", []),
        "topics": data.get("topics", []),
        "importance": data.get("importance", "medium"),
        "is_thread": thread.total_count > 1,
    }
    save_index(index)

    # Update tags
    tag_data = load_tags()
    for tag in data.get("tags", []):
        if tag not in tag_data["tags"]:
            tag_data["tags"][tag] = []
        if post_id not in tag_data["tags"][tag]:
            tag_data["tags"][tag].append(post_id)

    for topic in data.get("topics", []):
        if topic not in tag_data["topics"]:
            tag_data["topics"][topic] = []
        if post_id not in tag_data["topics"][topic]:
            tag_data["topics"][topic].append(post_id)

    save_tags(tag_data)

    return file_path


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

    # Conversation handler for archiving flow
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url),
        ],
        states={
            CONFIRM_CONTENT: [CallbackQueryHandler(confirm_content)],
            ADD_TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tags)],
            ADD_TOPICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_topics)],
            ADD_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_notes)],
            SET_IMPORTANCE: [CallbackQueryHandler(set_importance)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("recent", recent))
    application.add_handler(conv_handler)

    # Start polling
    print("🤖 Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
