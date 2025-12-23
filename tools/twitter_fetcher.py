"""
Fetch Twitter/X posts and threads using free APIs.

Uses FxTwitter/FixupX API which provides:
- Tweet content
- Author info
- Thread detection and fetching
- Media URLs
"""

import re
import time
import logging
from typing import Optional, List
from dataclasses import dataclass, field
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

# FxTwitter API endpoint (free, no auth required)
FXTWITTER_API = "https://api.fxtwitter.com"

# Fallback: vxtwitter
VXTWITTER_API = "https://api.vxtwitter.com"


@dataclass
class Tweet:
    """Represents a single tweet."""
    id: str
    url: str
    text: str
    author_handle: str
    author_name: str
    created_at: str
    media: List[dict] = field(default_factory=list)
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    views: int = 0
    is_quote: bool = False
    quoted_tweet: Optional['Tweet'] = None


@dataclass
class Thread:
    """Represents a thread of tweets."""
    tweets: List[Tweet]
    author_handle: str
    author_name: str
    total_count: int

    @property
    def main_tweet(self) -> Tweet:
        return self.tweets[0] if self.tweets else None

    @property
    def full_text(self) -> str:
        """Combine all tweets into full thread text."""
        parts = []
        for i, tweet in enumerate(self.tweets, 1):
            if len(self.tweets) > 1:
                parts.append(f"[{i}/{len(self.tweets)}] {tweet.text}")
            else:
                parts.append(tweet.text)
        return "\n\n".join(parts)


def extract_tweet_id(url: str) -> Optional[str]:
    """Extract tweet ID from various X/Twitter URL formats."""
    patterns = [
        r'(?:twitter|x)\.com/\w+/status/(\d+)',
        r'(?:twitter|x)\.com/i/web/status/(\d+)',
        r'(?:fxtwitter|vxtwitter|fixupx)\.com/\w+/status/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_handle(url: str) -> Optional[str]:
    """Extract handle from URL."""
    match = re.search(r'(?:twitter|x|fxtwitter|vxtwitter)\.com/(\w+)/status/', url)
    if match:
        handle = match.group(1)
        if handle not in ('i', 'intent', 'share'):
            return handle
    return None


def fetch_tweet_fxtwitter(tweet_id: str, handle: str = "i") -> Optional[dict]:
    """Fetch tweet data from FxTwitter API."""
    url = f"{FXTWITTER_API}/{handle}/status/{tweet_id}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                return data.get("tweet")
    except Exception as e:
        logger.warning(f"FxTwitter API error: {e}")

    return None


def fetch_tweet_vxtwitter(tweet_id: str, handle: str = "i") -> Optional[dict]:
    """Fallback: Fetch from VxTwitter API."""
    url = f"{VXTWITTER_API}/{handle}/status/{tweet_id}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"VxTwitter API error: {e}")

    return None


def parse_tweet_data(data: dict, source: str = "fxtwitter") -> Tweet:
    """Parse API response into Tweet object."""

    if source == "fxtwitter":
        # Parse media
        media = []
        if data.get("media"):
            for m in data["media"].get("all", []):
                media.append({
                    "type": m.get("type", "image"),
                    "url": m.get("url", ""),
                })

        # Handle quoted tweet
        quoted = None
        if data.get("quote"):
            quoted = parse_tweet_data(data["quote"], source)

        return Tweet(
            id=data.get("id", ""),
            url=data.get("url", ""),
            text=data.get("text", ""),
            author_handle=data.get("author", {}).get("screen_name", ""),
            author_name=data.get("author", {}).get("name", ""),
            created_at=data.get("created_at", ""),
            media=media,
            likes=data.get("likes", 0),
            retweets=data.get("retweets", 0),
            replies=data.get("replies", 0),
            views=data.get("views", 0),
            is_quote=bool(data.get("quote")),
            quoted_tweet=quoted,
        )

    elif source == "vxtwitter":
        media = []
        if data.get("media_extended"):
            for m in data["media_extended"]:
                media.append({
                    "type": m.get("type", "image"),
                    "url": m.get("url", ""),
                })

        return Tweet(
            id=str(data.get("tweetID", "")),
            url=data.get("tweetURL", ""),
            text=data.get("text", ""),
            author_handle=data.get("user_screen_name", ""),
            author_name=data.get("user_name", ""),
            created_at=data.get("date", ""),
            media=media,
            likes=data.get("likes", 0),
            retweets=data.get("retweets", 0),
            replies=data.get("replies", 0),
        )

    return None


def fetch_thread(tweet_url: str, max_depth: int = 25) -> Optional[Thread]:
    """
    Fetch a complete thread starting from a tweet URL.

    Attempts to get:
    1. The shared tweet
    2. Parent tweets (if shared tweet is a reply in thread)
    3. Continuation tweets (same author replying to themselves)
    """
    tweet_id = extract_tweet_id(tweet_url)
    handle = extract_handle(tweet_url) or "i"

    if not tweet_id:
        logger.error(f"Could not extract tweet ID from: {tweet_url}")
        return None

    # Try FxTwitter first, fallback to VxTwitter
    data = fetch_tweet_fxtwitter(tweet_id, handle)
    source = "fxtwitter"

    if not data:
        data = fetch_tweet_vxtwitter(tweet_id, handle)
        source = "vxtwitter"

    if not data:
        logger.error(f"Could not fetch tweet {tweet_id}")
        return None

    main_tweet = parse_tweet_data(data, source)
    tweets = [main_tweet]
    author_handle = main_tweet.author_handle

    # FxTwitter provides thread info in the response
    if source == "fxtwitter" and data.get("thread"):
        thread_data = data["thread"]
        # Thread contains array of tweet objects
        for thread_tweet_data in thread_data.get("tweets", [])[1:]:  # Skip first, we have it
            if len(tweets) >= max_depth:
                break
            tweet = parse_tweet_data(thread_tweet_data, source)
            if tweet and tweet.author_handle.lower() == author_handle.lower():
                tweets.append(tweet)

    # Check for parent tweet (if this is a reply in a thread)
    if source == "fxtwitter" and data.get("replying_to"):
        parent_handle = data.get("replying_to")
        parent_id = data.get("replying_to_status")

        # Only fetch parent if same author (part of thread)
        if parent_handle and parent_handle.lower() == author_handle.lower() and parent_id:
            parent_data = fetch_tweet_fxtwitter(parent_id, parent_handle)
            if parent_data:
                parent_tweet = parse_tweet_data(parent_data, "fxtwitter")
                # Insert at beginning
                tweets.insert(0, parent_tweet)

                # Recursively check for more parents (up to limit)
                depth = 1
                current_data = parent_data
                while depth < max_depth:
                    if not current_data.get("replying_to_status"):
                        break
                    if current_data.get("replying_to", "").lower() != author_handle.lower():
                        break

                    grandparent_id = current_data["replying_to_status"]
                    grandparent_data = fetch_tweet_fxtwitter(grandparent_id, author_handle)

                    if not grandparent_data:
                        break

                    grandparent = parse_tweet_data(grandparent_data, "fxtwitter")
                    tweets.insert(0, grandparent)
                    current_data = grandparent_data
                    depth += 1

                    # Rate limiting - be nice to the API
                    time.sleep(0.2)

    return Thread(
        tweets=tweets,
        author_handle=author_handle,
        author_name=main_tweet.author_name,
        total_count=len(tweets),
    )


def fetch_single_tweet(tweet_url: str) -> Optional[Tweet]:
    """Fetch just a single tweet without thread context."""
    tweet_id = extract_tweet_id(tweet_url)
    handle = extract_handle(tweet_url) or "i"

    if not tweet_id:
        return None

    data = fetch_tweet_fxtwitter(tweet_id, handle)
    if data:
        return parse_tweet_data(data, "fxtwitter")

    data = fetch_tweet_vxtwitter(tweet_id, handle)
    if data:
        return parse_tweet_data(data, "vxtwitter")

    return None


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python twitter_fetcher.py <tweet_url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Fetching thread from: {url}\n")

    thread = fetch_thread(url)

    if thread:
        print(f"Author: @{thread.author_handle} ({thread.author_name})")
        print(f"Thread length: {thread.total_count} tweets")
        print("-" * 50)

        for i, tweet in enumerate(thread.tweets, 1):
            print(f"\n[{i}/{thread.total_count}]")
            print(f"ID: {tweet.id}")
            print(f"Text: {tweet.text[:200]}..." if len(tweet.text) > 200 else f"Text: {tweet.text}")
            if tweet.media:
                print(f"Media: {len(tweet.media)} items")
            if tweet.quoted_tweet:
                print(f"Quotes: @{tweet.quoted_tweet.author_handle}")
    else:
        print("Failed to fetch thread")
