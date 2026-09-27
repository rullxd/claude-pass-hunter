import os
import re
import time
import random
import threading
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PROXY_URL = os.getenv("PROXY_URL", "").strip()
PROXIES_FILE = os.getenv("PROXIES_FILE", "proxies.txt").strip()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_passes.txt")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
LINK_RE = re.compile(r"https?://(?:www\.)?claude\.ai/referral/([a-zA-Z0-9_\-]+)", re.IGNORECASE)

seen_lock = threading.Lock()
file_lock = threading.Lock()

def load_proxies():
    proxies = []
    if PROXY_URL:
        proxies.append(PROXY_URL.replace("http://", "").replace("https://", ""))
    target_path = os.path.join(BASE_DIR, PROXIES_FILE) if not os.path.isabs(PROXIES_FILE) else PROXIES_FILE
    if os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip()
                if item and not item.startswith("#"):
                    proxies.append(item.replace("http://", "").replace("https://", ""))
    return list(dict.fromkeys(proxies))

PROXIES = load_proxies()

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return {line.strip().split('/')[-1] for line in f if line.strip()}

SEEN = load_seen()

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": "false"}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception as e:
        print(f"[!] Telegram send error: {e}", flush=True)
        return False

def check_anthropic_api(code):
    url = f"https://claude.ai/api/referral/code/{code}"
    for _ in range(2):
        p = random.choice(PROXIES) if PROXIES else None
        proxies = {"http": f"http://{p}", "https": f"http://{p}"} if p else None
        try:
            r = requests.get(url, impersonate="chrome", proxies=proxies, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    return data.get("is_valid") is True, data
                return False, data
        except Exception:
            continue
    return False, None

def dispatch_match(code, source_name):
    with seen_lock:
        if code in SEEN:
            return
        SEEN.add(code)

    with file_lock:
        with open(SEEN_FILE, "a", encoding="utf-8") as f:
            f.write(f"{code}\n")

    link = f"https://claude.ai/referral/{code}"
    print(f"[{source_name}] New link detected: {link}", flush=True)
    send_telegram(f"⚡ CLAUDE REFERRAL DETECTED!\n\nLink: {link}\nSource: {source_name}\n\nVerifying validity...")

    is_valid, data = check_anthropic_api(code)
    status_str = "🔥 VALID & READY TO CLAIM!" if is_valid else "⚠️ ALREADY CLAIMED / EXPIRED"
    update_msg = f"Status Update: {status_str}\nLink: {link}\nDetails: {data}"
    send_telegram(update_msg)
    print(f"[{source_name}] {code} -> {status_str}", flush=True)

def fetch_feed(feed_url):
    for _ in range(3):
        p = random.choice(PROXIES) if PROXIES else None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": f"http://{p}", "https": f"http://{p}"})) if p else urllib.request.build_opener()
        req = urllib.request.Request(feed_url, headers=HEADERS)
        try:
            with opener.open(req, timeout=6) as r:
                return r.read()
        except Exception:
            continue
    return None

def agent_worker(name, feeds, poll_interval):
    print(f"[*] Agent '{name}' active. Poll interval: {poll_interval}s", flush=True)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    while True:
        for feed in feeds:
            raw = fetch_feed(feed)
            if not raw:
                continue
            try:
                root = ET.fromstring(raw)
                for entry in root.findall("atom:entry", ns):
                    c = entry.find("atom:content", ns)
                    txt = c.text if c is not None else ""
                    for code in LINK_RE.findall(txt):
                        dispatch_match(code, name)
            except Exception:
                for code in LINK_RE.findall(raw.decode("utf-8", errors="ignore")):
                    dispatch_match(code, name)
        time.sleep(poll_interval)

def main():
    print(f"[*] Starting Multi-Agent Claude Referral Hunter (Proxies: {len(PROXIES)})...", flush=True)

    agents = [
        ("Agent-ClaudeCode", [
            "https://www.reddit.com/r/ClaudeCode/comments.rss?limit=50",
            "https://www.reddit.com/r/ClaudeCode/new.rss?limit=50"
        ], 2),
        ("Agent-ClaudeAI", [
            "https://www.reddit.com/r/ClaudeAI/comments.rss?limit=50",
            "https://www.reddit.com/r/ClaudeAI/new.rss?limit=50",
            "https://www.reddit.com/r/ClaudeAI/comments/1pnj9zd.rss?sort=new&limit=50"
        ], 3),
        ("Agent-Anthropic", [
            "https://www.reddit.com/r/Anthropic/comments.rss?limit=50",
            "https://www.reddit.com/r/Anthropic/new.rss?limit=50"
        ], 4),
        ("Agent-GlobalSearch", [
            "https://www.reddit.com/search.rss?q=claude.ai%2Freferral&sort=new&limit=50",
            "https://www.reddit.com/search.rss?q=%22guest+pass%22+claude&sort=new&limit=50"
        ], 5),
    ]

    threads = []
    for name, feeds, interval in agents:
        t = threading.Thread(target=agent_worker, args=(name, feeds, interval), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
