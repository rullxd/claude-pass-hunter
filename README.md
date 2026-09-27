# Claude Referral & Guest Pass Multi-Agent Hunter

High-speed multi-threaded monitoring bot that detects, extracts, and validates Claude Pro / Claude Code 7-day trial referral links in real-time with instant Telegram alerts.

## About

Anthropic periodically provides eligible Claude Max / Claude Pro subscribers with single-use referral guest passes (`/passes` command in Claude Code). Each pass grants a recipient 7 days of full Claude Pro access (including Claude Code CLI, higher rate limits, and latest models).

Because these passes are non-replenishing and strictly first-come, first-served, whenever a user shares a link publicly on developer communities or subreddits (such as `r/ClaudeCode`, `r/ClaudeAI`, or `r/Anthropic`), the pass is usually claimed within seconds.

**Claude Pass Hunter** solves this latency problem:
- **Low-Latency Polling**: Deploys 4 specialized concurrent worker agents cycling every 2–5 seconds across high-traffic Reddit communities and search queries.
- **Proxy Rotation**: Routes requests through a residential / data center proxy pool to eliminate HTTP 429 rate limits and 403 geo-blocks.
- **Zero-Latency Alerting**: Fires a Telegram push alert the exact millisecond a referral URL format (`claude.ai/referral/<code_or_hash>`) is captured by the regex engine.
- **In-Place Live Verification**: Validates the link against Anthropic's official referral status API endpoint (`/api/referral/code/<code_or_hash>`) asynchronously and updates the Telegram message in-place via `editMessageText`, eliminating duplicate notification spam.

## Features

- **Concurrent Multi-Agent Architecture**: Dedicated background workers polling target sources (`r/ClaudeCode`, `r/ClaudeAI`, `r/Anthropic`, megathreads, global queries) with 2-5s interval.
- **Sub-Second Instant Alerting**: Sends Telegram notification immediately upon detection without waiting for network verification.
- **In-Place Message Editing**: Seamlessly transitions from pending verification to claimable/expired status inside the same Telegram bubble.
- **Anthropic API Verification**: Verifies referral validity concurrently via Anthropic's official referral status endpoint (`/api/referral/code/<code_or_hash>`).
- **Proxy Rotation**: Built-in rotating proxy pool support to bypass Reddit rate limits (429 / 403).
- **Thread-Safe Deduplication**: In-memory and file-backed history tracking prevents duplicate notifications.

## Installation

1. Clone repository:
```bash
git clone https://github.com/<your-username>/claude-pass-hunter.git
cd claude-pass-hunter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
```bash
cp .env.example .env
```
Fill in `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

4. (Optional) Setup proxies:
Add HTTP proxies into `proxies.txt` (format: `user:pass@ip:port` or `ip:port`, one per line).

## Usage

```bash
python hunter.py
```

## Architecture

```text
[Reddit Feeds & Search]
      │ (2-5s polling with proxy rotation)
      ▼
[4 Concurrent Workers]
      │ Regex link extraction
      ├───────────────────────────────┐
      ▼ (Instant <1s)                 ▼ (Async)
[Telegram Alert: New Link]      [Anthropic API Validator]
                                      │
                                      ▼
                                [Telegram In-Place Update: Valid / Expired]
```

## Disclaimer

This repository is for educational and research purposes only. All product names, logos, and brands are property of their respective owners.
