"""
Steam 패치노트 -> 디스코드 웹훅 알림 (GitHub Actions cron용, 상시구동 불필요)

동작
- Steam RSS를 확인해서 마지막으로 본 글(guid) 이후의 새 글을 찾음
- 새 글이 있으면 DISCORD_WEBHOOKS 에 등록된 모든 웹훅으로 임베드 전송
- 마지막으로 본 글의 guid를 last_guid.txt 에 기록 (워크플로우가 이 파일을 다시 커밋함)

환경 변수
- DISCORD_WEBHOOKS : 디스코드 웹훅 URL, 여러 개면 쉼표(,)로 구분
- STEAM_APPID      : (선택) 감시할 게임 appid. 기본값 1422450
- STATE_FILE        : (선택) 마지막 guid 저장 파일 경로. 기본값 last_guid.txt
"""

import os
import re
import sys
import time
import logging
from html import unescape

import feedparser
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("patchnote-to-discord")

STEAM_APPID = os.environ.get("STEAM_APPID", None)
STATE_FILE = "last_guid.txt"
RSS_URL = f"https://store.steampowered.com/feeds/news/app/{STEAM_APPID}/"

STEAM_BLUE = 0x1B2838
EMBED_DESC_LIMIT = 4000

TAG_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG_P_OPEN = re.compile(r"<p[^>]*>", re.IGNORECASE)
TAG_P_CLOSE = re.compile(r"</p>", re.IGNORECASE)
TAG_BOLD = re.compile(r"<b>(.*?)</b>", re.IGNORECASE | re.DOTALL)
TAG_ANY = re.compile(r"<[^>]+>")
MULTI_NEWLINE = re.compile(r"\n{3,}")


def html_to_discord_text(html: str, link: str) -> str:
    text = html or ""
    text = TAG_BR.sub("\n", text)
    text = TAG_P_OPEN.sub("\n", text)
    text = TAG_P_CLOSE.sub("", text)
    text = TAG_BOLD.sub(r"**\1**", text)
    text = TAG_ANY.sub("", text)
    text = unescape(text)
    text = MULTI_NEWLINE.sub("\n\n", text).strip()

    if len(text) > EMBED_DESC_LIMIT:
        text = text[:EMBED_DESC_LIMIT].rstrip() + f"\n\n...([Read more]({link}))"
    return text


def load_last_guid() -> str | None:
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        value = f.read().strip()
    return value or None


def save_last_guid(guid: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(guid)


def build_embed(entry) -> dict:
    link = entry.get("link", "")
    return {
        "title": (entry.get("title") or "(untitled)").strip()[:256],
        "url": link,
        "description": html_to_discord_text(entry.get("description", ""), link),
        "color": STEAM_BLUE,
    }


def send_to_webhooks(webhooks: list[str], embed: dict) -> None:
    payload = {"embeds": [embed]}
    for url in webhooks:
        url = url.strip()
        if not url:
            continue
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 1)
            log.warning("Ratelimit, waited for %s seconds", retry_after)
            time.sleep(float(retry_after) + 0.5)
            resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code >= 300:
            log.error("Failed to send webhooks (%s): %s", resp.status_code, resp.text[:300])
        else:
            log.info("Successful sending webhooks: %s...", url[:50])
        time.sleep(1)


def main() -> int:
    if not STEAM_APPID:
        log.error("STEAM_APPID env variable is empty.")
        return 1
    raw_webhooks = os.environ.get("DISCORD_WEBHOOKS", "")
    webhooks = [w for w in raw_webhooks.split(",") if w.strip()]
    if not webhooks:
        log.error("DISCORD_WEBHOOKS env secret is empty.")
        return 1

    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        log.warning("RSS has no item.: %s", RSS_URL)
        return 0

    last_guid = load_last_guid()

    if last_guid is None: #최초실행
        newest = feed.entries[0].guid
        save_last_guid(newest)
        log.info("Setting initial guid as %s", newest)
        if os.environ.get("DEBUG") == "true":
            log.info("sending last announcement as debug test") 
            send_to_webhooks(webhooks, build_embed(feed.entries[0]))
        return 0

    new_entries = []
    for entry in feed.entries:
        guid = entry.guid
        if guid == last_guid:
            break
        new_entries.append(entry)
    new_entries.reverse()  # 글 오래된 순으로 전송

    if not new_entries:
        log.info("No new updates.")
        return 0

    for entry in new_entries:
        send_to_webhooks(webhooks, build_embed(entry))

    newest_guid = feed.entries[0].guid
    save_last_guid(newest_guid)
    log.info("Successful sending new %d announcements.", len(new_entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
