#!/usr/bin/env python3
"""Refresh Eleven's public episode shelf without depending on browser-side APIs.

The homepage remains useful if Apple or RSS.com is temporarily unreachable.
Run daily in GitHub Actions; only verified episodes replace the last good data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/assets/eleven-episodes.json"
HOME = ROOT / "docs/index.html"
SHOW_ID = "1875218821"
SHOW_URL = "https://podcasts.apple.com/us/podcast/eleven-by-alles-clinx/id" + SHOW_ID
APPLE_LOOKUP = "https://itunes.apple.com/lookup?id=" + SHOW_ID + "&entity=podcastEpisode&limit=100&country=us"
RSS_FALLBACK = "https://media.rss.com/eleven-by-allesclinx/feed.xml"
START = "<!-- eleven:episodes:start -->"
END = "<!-- eleven:episodes:end -->"
ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
    def handle_data(self, value: str) -> None:
        self.parts.append(value)


def summary(value: str, max_length: int = 176) -> str:
    parser = PlainText()
    parser.feed(unescape(value or ""))
    clean = " ".join(" ".join(parser.parts).split())
    if len(clean) <= max_length:
        return clean
    return clean[:max_length].rsplit(" ", 1)[0].rstrip(" .,;:") + "…"


def public_url(value: str, hosts: tuple[str, ...]) -> str:
    if not isinstance(value, str):
        return ""
    parts = urlparse(value)
    if parts.scheme != "https" or not parts.hostname:
        return ""
    host = parts.hostname.lower()
    return value if any(host == h or host.endswith("." + h) for h in hosts) else ""


def get_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "AlleClinx-Knowledge-PodcastSync/1.0", "Accept": "application/json, application/xml, text/xml, */*"})
    with urlopen(request, timeout=24) as response:
        content = response.read(5_000_001)
    if len(content) > 5_000_000:
        raise ValueError("Podcast metadata response too large")
    return content


def parse_datetime(raw: str) -> str:
    if not raw:
        return ""
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        try:
            value = parsedate_to_datetime(str(raw))
        except (ValueError, TypeError):
            return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    if value > datetime.now(timezone.utc):
        return ""
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def episode_number(value: object) -> int:
    try:
        n = int(value)
        return n if 1 <= n <= 10000 else 0
    except (TypeError, ValueError):
        return 0


def duration(value: object) -> int:
    if isinstance(value, int):
        return max(0, value)
    raw = str(value or "").strip()
    if raw.isdecimal():
        return int(raw)
    chunks = raw.split(":")
    if 2 <= len(chunks) <= 3 and all(part.isdecimal() for part in chunks):
        seconds = 0
        for part in chunks:
            seconds = seconds * 60 + int(part)
        return seconds
    return 0


def clean_episode(obj: dict) -> dict | None:
    title = " ".join(str(obj.get("title") or "").split())
    date = parse_datetime(str(obj.get("published") or ""))
    if not title or not date:
        return None
    url = public_url(str(obj.get("url") or ""), ("podcasts.apple.com", "rss.com")) or SHOW_URL
    return {
        "number": episode_number(obj.get("number")),
        "title": title[:190],
        "published": date,
        "duration_seconds": duration(obj.get("duration_seconds")),
        "description": summary(str(obj.get("description") or "")),
        "url": url,
        "artwork": public_url(str(obj.get("artwork") or ""), ("mzstatic.com", "rss.com")),
        "audio_url": public_url(str(obj.get("audio_url") or ""), ("rss.com", "rsscdn.com")),
    }


def from_apple(payload: dict) -> tuple[list[dict], str]:
    results = payload.get("results", [])
    show = next((item for item in results if item.get("collectionId") == int(SHOW_ID) and item.get("kind") != "podcast-episode"), {})
    if show:
        name = str(show.get("collectionName", "")).lower()
        if "eleven" not in name or "clinx" not in name:
            raise ValueError("Apple lookup returned a different show")
    feed = public_url(str(show.get("feedUrl") or ""), ("rss.com",))
    output = []
    for item in results:
        if item.get("kind") != "podcast-episode" and item.get("wrapperType") != "podcastEpisode":
            continue
        if int(item.get("collectionId", 0) or 0) != int(SHOW_ID):
            continue
        ep = clean_episode({
            "number": item.get("episodeNumber") or item.get("trackNumber") or 0,
            "title": item.get("trackName", ""),
            "published": item.get("releaseDate", ""),
            "duration_seconds": int(item.get("trackTimeMillis") or 0) // 1000,
            "description": item.get("description") or item.get("shortDescription") or "",
            "url": item.get("trackViewUrl", ""),
            "artwork": item.get("artworkUrl600") or item.get("artworkUrl160") or "",
        })
        if ep:
            output.append(ep)
    return output, feed


def from_rss(raw: bytes, previous: list[dict]) -> list[dict]:
    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Podcast RSS is missing its channel")
    name = str(channel.findtext("title") or "").lower()
    if "eleven" not in name or "clinx" not in name:
        raise ValueError("RSS is not the Eleven by Alle's ClinX show")
    fallback_image = (channel.find(ITUNES + "image") or ET.Element("image")).get("href", "")
    indexed = {ep.get("title", "").casefold(): ep for ep in previous}
    output = []
    for item in channel.findall("item"):
        title = item.findtext("title") or ""
        prior = indexed.get(title.casefold(), {})
        image_node = item.find(ITUNES + "image")
        enclosure = item.find("enclosure")
        enclosure_url = enclosure.get("url", "") if enclosure is not None and (enclosure.get("type","").startswith("audio/") or enclosure.get("url","").lower().endswith((".mp3",".m4a"))) else ""
        ep = clean_episode({
            "number": item.findtext(ITUNES + "episode") or prior.get("number", 0),
            "title": title,
            "published": item.findtext("pubDate") or "",
            "duration_seconds": duration(item.findtext(ITUNES + "duration")),
            "description": item.findtext("description") or "",
            "url": prior.get("url") or item.findtext("link") or SHOW_URL,
            "artwork": (image_node.get("href", "") if image_node is not None else "") or fallback_image,
            "audio_url": enclosure_url or prior.get("audio_url", ""),
        })
        if ep:
            output.append(ep)
    return output


def normalized(episodes: list[dict]) -> list[dict]:
    unique = {}
    for item in episodes:
        ep = clean_episode(item)
        if not ep:
            continue
        key = ep["published"] + "|" + ep["title"].casefold()
        unique[key] = ep
    return sorted(unique.values(), key=lambda ep: ep["published"], reverse=True)[:12]


def card(ep: dict, index: int) -> str:
    title = escape(ep["title"], quote=True)
    description = escape(ep.get("description", ""), quote=True)
    number = "Episode " + str(ep["number"]).zfill(2) if ep["number"] else "New episode"
    mins = round(ep.get("duration_seconds", 0) / 60)
    duration_text = f" · {mins} min" if mins else ""
    timestamp = ep["published"][:10]
    date = datetime.fromisoformat(timestamp).strftime("%d %b %Y").lstrip("0")
    art = ep.get("artwork") or ""
    if art:
        cover = '<img src="' + escape(art, quote=True) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">'
    else:
        cover = '<span aria-hidden="true">11</span>'

    audio = ep.get("audio_url", "")
    if audio:
        play_control = (
            '<button class="eleven-play" type="button" data-audio-src="' + escape(audio, quote=True) +
            '" data-duration-seconds="' + str(ep.get("duration_seconds", 0)) + '" aria-label="Play ' + title + '" aria-pressed="false" title="Play episode">' +
            '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
            '<path class="eleven-icon-play" d="m9 6 9 6-9 6V6Z"/>' +
            '<path class="eleven-icon-pause" d="M9 6v12M15 6v12"/></svg></button>' +
            '<span class="eleven-play-label">Play episode</span>'
        )
        progress = (
            '\n          <div class="eleven-progress" hidden>' +
            '<label class="eleven-sr-only" for="eleven-seek-' + str(index) + '">Playback position for ' + title + '</label>' +
            '<input class="eleven-seek" id="eleven-seek-' + str(index) + '" type="range" min="0" max="1000" value="0" aria-label="Seek within ' + title + '"/>' +
            '<span class="eleven-play-time">0:00 / ' + str(mins) + ':00</span></div>'
        )
    else:
        play_control = '<span class="eleven-unavailable">Listen on Apple Podcasts</span>'
        progress = ""

    return (
        '      <article class="eleven-episode' + (' eleven-episode-featured' if index == 0 else '') + '">' +
        '\n        <div class="eleven-cover">' + cover + '</div>' +
        '\n        <div class="eleven-episode-body"><span class="eleven-episode-meta">' + escape(number + duration_text) + '</span>' +
        '\n          <h3>' + title + '</h3>' +
        '\n          <p>' + description + '</p>' +
        '\n          <time datetime="' + timestamp + '">' + date + '</time>' +
        '\n          <div class="eleven-episode-actions">' + play_control +
        '<a class="eleven-source-link" href="' + escape(ep["url"], quote=True) + '" target="_blank" rel="noopener noreferrer" aria-label="Listen to ' + title + ' on Apple Podcasts">Apple Podcasts</a></div>' +
        progress + '</div>\n      </article>'
    )


def main() -> None:
    old_data = json.loads(DATA.read_text(encoding="utf-8"))
    previous = normalized(old_data.get("episodes", []))
    if not previous:
        raise ValueError("The verified fallback podcast list is missing")
    found = []
    feed_url = ""
    try:
        found, feed_url = from_apple(json.loads(get_bytes(APPLE_LOOKUP)))
        if found:
            print(f"Apple catalogue: {len(found)} episodes")
    except Exception as error:
        print("Apple catalogue temporarily unavailable:", error)
    # RSS contains the audio enclosure URL, which the Apple catalogue does not.
    # Always read the first-party publisher feed even when catalogue metadata exists.
    rss_episodes = []
    for source in dict.fromkeys((feed_url, RSS_FALLBACK)):
        if not source:
            continue
        try:
            rss_episodes = from_rss(get_bytes(source), previous)
            if rss_episodes:
                print(f"Podcast RSS: {len(rss_episodes)} episodes, {sum(bool(e.get('audio_url')) for e in rss_episodes)} audio enclosures")
                break
        except Exception as error:
            print("Podcast RSS unavailable:", error)
    if not found and rss_episodes:
        found = rss_episodes
    if found:
        updated = normalized(found)
        # Prefer verified earlier per-episode Apple links over generic show links.
        previous_by_title = {p["title"].casefold(): p for p in previous}
        rss_by_title = {p["title"].casefold(): p for p in normalized(rss_episodes)}
        for ep in updated:
            past = previous_by_title.get(ep["title"].casefold(), {})
            publisher = rss_by_title.get(ep["title"].casefold(), {})
            if ep["url"] == SHOW_URL and past.get("url", "").startswith(SHOW_URL):
                ep["url"] = past["url"]
            if not ep["number"]:
                ep["number"] = past.get("number", 0)
            if not ep["artwork"]:
                ep["artwork"] = past.get("artwork", "")
            if not ep["description"]:
                ep["description"] = past.get("description", "")
            ep["audio_url"] = publisher.get("audio_url") or past.get("audio_url", "")
        # Avoid accidentally erasing published episodes if a source is partial.
        if len(updated) >= min(3, len(previous)):
            previous = updated
        else:
            print("Source returned a partial episode list; retaining verified data")
    else:
        print("No fresh metadata; retaining verified published episodes")

    existing_html = HOME.read_text(encoding="utf-8")
    if existing_html.count(START) != 1 or existing_html.count(END) != 1:
        raise ValueError("Homepage episode markers are absent or duplicated")
    render = "\n".join(card(ep, i) for i, ep in enumerate(previous[:3]))
    a = existing_html.index(START) + len(START)
    b = existing_html.index(END, a)
    rendered_html = existing_html[:a] + "\n" + render + "\n    " + existing_html[b:]
    output = {
        "show": "Eleven by Alle's ClinX",
        "show_url": SHOW_URL,
        "source": "Apple Podcasts catalogue / published podcast RSS",
        "episodes": previous,
    }
    updated_json = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if updated_json != DATA.read_text(encoding="utf-8"):
        DATA.write_text(updated_json, encoding="utf-8")
    if rendered_html != existing_html:
        HOME.write_text(rendered_html, encoding="utf-8")
    print("Homepage Eleven shelf:", ", ".join(ep["title"] for ep in previous[:3]))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Podcast sync failed:", error, file=sys.stderr)
        sys.exit(1)
