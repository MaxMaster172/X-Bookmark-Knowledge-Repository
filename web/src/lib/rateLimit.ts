/**
 * Client-side rate limiting for chat messages
 *
 * Uses localStorage to track message timestamps in a rolling window.
 * Default: 20 messages per hour, configurable via NEXT_PUBLIC_CHAT_RATE_LIMIT env var.
 */

const STORAGE_KEY = "chat_rate_limit_timestamps";
const WINDOW_MS = 60 * 60 * 1000; // 1 hour in milliseconds

/**
 * Get the rate limit from env var or use default
 */
export function getRateLimit(): number {
  if (typeof window === "undefined") {
    return 20;
  }
  const envLimit = process.env.NEXT_PUBLIC_CHAT_RATE_LIMIT;
  if (envLimit) {
    const parsed = parseInt(envLimit, 10);
    if (!isNaN(parsed) && parsed > 0) {
      return parsed;
    }
  }
  return 20; // Default: 20 messages per hour
}

/**
 * Get stored message timestamps from localStorage
 * Filters out expired timestamps (older than 1 hour)
 */
function getTimestamps(): number[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }

    const timestamps: number[] = JSON.parse(stored);
    const now = Date.now();
    const cutoff = now - WINDOW_MS;

    // Filter to only include timestamps within the rolling window
    return timestamps.filter((ts) => ts > cutoff);
  } catch {
    // If parsing fails, start fresh
    return [];
  }
}

/**
 * Save timestamps to localStorage
 */
function saveTimestamps(timestamps: number[]): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(timestamps));
  } catch {
    // localStorage might be full or disabled, ignore
  }
}

/**
 * Rate limit state returned by checkRateLimit
 */
export interface RateLimitState {
  /** Whether the user can send a message */
  canSend: boolean;
  /** Number of messages remaining in the current window */
  remaining: number;
  /** Total limit per hour */
  limit: number;
  /** Time in milliseconds until the oldest message expires (for reset) */
  resetInMs: number | null;
}

/**
 * Check if the user can send a message and get remaining count
 *
 * @returns Rate limit state with canSend, remaining, limit, and resetInMs
 */
export function checkRateLimit(): RateLimitState {
  const limit = getRateLimit();
  const timestamps = getTimestamps();
  const now = Date.now();

  const remaining = Math.max(0, limit - timestamps.length);
  const canSend = timestamps.length < limit;

  // Calculate time until oldest message expires (when a slot opens up)
  let resetInMs: number | null = null;
  if (timestamps.length > 0 && !canSend) {
    // Sort to get oldest timestamp
    const sortedTimestamps = [...timestamps].sort((a, b) => a - b);
    const oldestTimestamp = sortedTimestamps[0];
    const expiresAt = oldestTimestamp + WINDOW_MS;
    resetInMs = Math.max(0, expiresAt - now);
  }

  return {
    canSend,
    remaining,
    limit,
    resetInMs,
  };
}

/**
 * Record a new message being sent
 * Call this after a message is successfully sent
 */
export function recordMessage(): void {
  const timestamps = getTimestamps();
  timestamps.push(Date.now());
  saveTimestamps(timestamps);
}

/**
 * Clear all rate limit data (useful for testing or reset)
 */
export function clearRateLimit(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore errors
  }
}

/**
 * Format the reset time for display
 *
 * @param resetInMs - Milliseconds until reset
 * @returns Human-readable string like "45m" or "5m 30s"
 */
export function formatResetTime(resetInMs: number): string {
  if (resetInMs <= 0) {
    return "now";
  }

  const totalSeconds = Math.ceil(resetInMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes === 0) {
    return `${seconds}s`;
  }

  if (seconds === 0) {
    return `${minutes}m`;
  }

  return `${minutes}m ${seconds}s`;
}
