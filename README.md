# Claude Referral & Guest Pass Multi-Agent Hunter

High-speed multi-threaded monitoring bot that detects, extracts, and validates Claude Pro / Claude Code 7-day trial referral links in real-time with instant Telegram alerts.

## Features

- **Concurrent Multi-Agent Architecture**: Dedicated background workers polling target sources (`r/ClaudeCode`, `r/ClaudeAI`, `r/Anthropic`, megathreads, global queries) with 2-5s interval.
- **Sub-Second Instant Alerting**: Sends Telegram notification immediately upon detection without waiting for network verification.
- **Anthropic API Verification**: Verifies referral validity concurrently via Anthropic's official referral status endpoint (`/api/referral/code/<code_or_hash>`).
- **Proxy Rotation**: Built-in rotating proxy pool support to bypass Reddit rate limits (429 / 403).
- **Deduplication Engine**: Thread-safe history tracking prevents duplicate notifications.

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
                                [Telegram Alert: Claim Status]
```

## Disclaimer

This repository is for educational and research purposes only. All product names, logos, and brands are property of their respective owners.
