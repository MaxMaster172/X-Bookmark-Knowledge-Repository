# Telegram Markdown Parsing Bug

> Last updated: 2024-12-24
> Status: **Workaround Applied** - Needs proper fix when migrating to Supabase

## The Issue

When archiving X posts from users with underscores in their handle (e.g., `@zephyr_z9`), the Telegram bot crashed with:

```
Can't parse entities: can't find end of the entity starting at byte offset 27
```

## Root Cause

Telegram's Markdown parser interprets underscores (`_`) as italic text markers. When a username like `zephyr_z9` appears in a message with `parse_mode="Markdown"`, Telegram tries to parse `_z9` as the start of italic text but can't find the closing underscore.

Example message that fails:
```
⚡ *Quick Saved!*

@zephyr_z9's post archived.
```

The underscore at byte ~27 (`zephyr_z9`) triggers the parser to look for a closing `_`, which doesn't exist.

## Temporary Fix Applied

Removed `parse_mode="Markdown"` from all messages that include dynamic content (usernames, search results):

| Location | Change |
|----------|--------|
| Quick save success (line ~378) | Removed `parse_mode`, changed `*Quick Saved!*` to `Quick Saved!` |
| Full archive success (line ~461) | Removed `parse_mode`, changed `*Archived!*` to `Archived!` |
| Recent posts list (line ~145) | Removed `parse_mode`, changed `*Recent Archives:*` to `Recent Archives:` |
| Search results (line ~181) | Removed `parse_mode` |
| Keyword search results (line ~258) | Removed `parse_mode` |

Static messages (`/start`, `/help`, `/stats`) still use Markdown since they don't include dynamic content.

## Trade-off

We lose bold/italic formatting in confirmation messages. The messages still work fine, just look slightly less polished.

## Proper Solutions for Supabase Migration

When rebuilding the bot to write to Supabase, consider these approaches:

### Option 1: Escape Special Characters
```python
def escape_markdown(text: str) -> str:
    """Escape Markdown special characters."""
    for char in ['_', '*', '`', '[', ']', '(', ')']:
        text = text.replace(char, f'\\{char}')
    return text

# Usage:
f"@{escape_markdown(thread.author_handle)}'s post archived."
```

### Option 2: Use HTML Mode
```python
await query.edit_message_text(
    f"⚡ <b>Quick Saved!</b>\n\n"
    f"@{thread.author_handle}'s post archived.",
    parse_mode="HTML"
)
```
Note: HTML mode requires escaping `<`, `>`, `&` instead.

### Option 3: Use MarkdownV2
```python
def escape_markdown_v2(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special:
        text = text.replace(char, f'\\{char}')
    return text
```
More predictable than legacy Markdown but requires escaping many more characters.

## Recommendation

**Use HTML mode** when rebuilding for Supabase. Characters that need escaping (`<`, `>`, `&`) are rare in Twitter handles and content compared to underscores.

## Affected Usernames

Any X/Twitter handle containing:
- `_` (underscore) - very common
- `*` (asterisk) - rare but possible
- `` ` `` (backtick) - rare

## References

- [Telegram Bot API - Formatting](https://core.telegram.org/bots/api#formatting-options)
- [Telegram MarkdownV2 style](https://core.telegram.org/bots/api#markdownv2-style)
- Commit: `724dc87` - Original fix attempt
