"""Automatic narration of approved Alle's ClinX Knowledge articles into chapters."""
from __future__ import annotations

import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


ALLOWED = {"en": "english-locked", "hi-IN": "translation-locked"}
LANG = {"en": "en", "hi-IN": "hi"}


def clean(value):
    value = re.sub(r"\s+", " ", value)
    return re.sub(r"\s*\[\d+\]", "", value).strip()


class Sections(HTMLParser):
    """Keep narration verbatim, without tables, references or HTML."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = [["Introduction", []]]
        self.capture = None
        self.words = []
        self.skip = 0
        self.references = False

    def handle_starttag(self, tag, attrs):
        if tag in ("table", "script", "style"):
            self.skip += 1
        if self.skip or self.references:
            return
        if tag in ("h2", "h3", "p", "li") and self.capture is None:
            self.capture, self.words = tag, []

    def handle_endtag(self, tag):
        if self.skip:
            if tag in ("table", "script", "style"):
                self.skip -= 1
            return
        if self.references or self.capture != tag:
            return
        value = clean("".join(self.words))
        if value:
            if tag == "h2":
                if value.lower() in ("references", "sources", "further reading"):
                    self.references = True
                else:
                    self.sections.append([value, []])
            elif tag == "h3":
                self.sections[-1][1].append(value + ".")
            else:
                self.sections[-1][1].append(value)
        self.capture, self.words = None, []

    def handle_data(self, data):
        if self.capture and not self.skip and not self.references:
            self.words.append(data)


def chapters(article):
    parser = Sections()
    parser.feed(article["content_html"])
    return [{"title": name, "text": "\n\n".join(paras)}
            for name, paras in parser.sections if paras]


def split_chunks(text, maximum=220):
    output = []
    for sentence in re.split(r"(?<=[.!?।])\s+", clean(text)):
        current = ""
        for word in sentence.split():
            if len(word) > maximum:
                raise ValueError("Unusually long word in training narration")
            if len(current) + len(word) + 1 > maximum:
                if current:
                    output.append(current)
                current = word
            else:
                current = (current + " " + word).strip()
        if current:
            if output and len(output[-1]) + len(current) + 1 <= maximum:
                output[-1] += " " + current
            else:
                output.append(current)
    return output


def select(root, requested):
    live = set(json.loads((root / "production/live.json").read_text())["live_article_ids"])
    for file in sorted((root / "articles").glob("*/ACX-KB-*/??.json")):
        article = json.loads(file.read_text(encoding="utf-8"))
        locale = article.get("locale")
        if (locale in requested and article.get("article_id") in live
                and article.get("editorial_status") == ALLOWED.get(locale)
                and article.get("content_html")):
            article["_source_path"] = str(file)
            yield article


def package(article, voice):
    if not re.fullmatch(r"ACX-KB-[0-9]{4}", article["article_id"]):
        raise ValueError("Invalid article identifier")
    sections = chapters(article)
    if not sections:
        raise ValueError("No narratable text in approved article")
    signature = sha256(json.dumps({"source": sections, "voice": voice,
                                  "engine": "chatterbox-v3-pilot-v1",
                                  "article": article["article_id"],
                                  "locale": article["locale"]},
                                 ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {"article_id": article["article_id"], "title": article["title"],
            "locale": article["locale"], "source_path": article["_source_path"],
            "source_sha256": signature, "voice_id": voice,
            "status": "machine-narrated-preview", "chapters": sections}


def narrate(course, out, voice):
    import torch
    import torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    # Official Chatterbox supports CUDA, Apple Silicon MPS, or CPU.
    # Mac performance must be checked during the first-run pilot.
    device = ("cuda" if torch.cuda.is_available()
              else "mps" if torch.backends.mps.is_available()
              else "cpu")
    print("TTS device:", device)
    model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
    for i, chapter in enumerate(course["chapters"], 1):
        timeline, waveforms, elapsed = [], [], 0.0
        for chunk in split_chunks(chapter["title"] + ". " + chapter["text"]):
            audio = model.generate(chunk, language_id=LANG[course["locale"]],
                                   audio_prompt_path=str(voice)).detach().cpu().float()
            if audio.ndim == 1:
                audio = audio.unsqueeze(0)
            seconds = audio.shape[-1] / model.sr
            if not 0.1 < seconds < 240:
                raise ValueError("Abnormal speech duration: possible bad rendering")
            timeline.append({"start": round(elapsed, 3),
                             "end": round(elapsed + seconds, 3), "text": chunk})
            elapsed += seconds
            waveforms.extend([audio, torch.zeros((1, round(model.sr * 0.4)))])
            elapsed += 0.4
        if not waveforms:
            raise ValueError("Empty chapter output")
        stem = f"chapter-{i:02d}"
        wav = out / (stem + ".wav")
        mp3 = out / (stem + ".mp3")
        torchaudio.save(str(wav), torch.cat(waveforms, dim=-1), model.sr)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(wav), "-codec:a", "libmp3lame", "-b:a",
                        "128k", str(mp3)], check=True)
        wav.unlink()
        chapter.update({"file": mp3.name, "duration_seconds": round(elapsed, 2),
                        "segments": timeline})


def main():
    from contextlib import nullcontext
    from audio_training.hostinger_storage import HostingerStore

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--max-courses", type=int, default=2)
    ap.add_argument("--locales", nargs="+", default=["en"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.max_courses < 1:
        ap.error("max-courses must be positive")

    # The private Hostinger folder remains outside public_html. No AWS or S3.
    # The Mac runner holds its own SSH key and consented voice recordings.
    store_context = nullcontext(None) if args.dry_run else HostingerStore()
    archive_value = os.getenv("AUDIO_LOCAL_ARCHIVE_PATH", "")
    created, skipped = 0, 0
    with store_context as storage:
        for article in select(args.root, set(args.locales)):
            voice_var = ("AUDIO_VOICE_HI_PATH" if article["locale"] == "hi-IN"
                         else "AUDIO_VOICE_EN_PATH")
            voice_path = Path(os.getenv(voice_var, "")).expanduser()
            if not args.dry_run and not voice_path.is_file():
                raise RuntimeError(f"{voice_var} must point to a consented local WAV recording")
            voice_signature = (sha256(voice_path.read_bytes()).hexdigest()
                               if not args.dry_run else "dry-run")
            course = package(article, voice_signature)
            old = (storage.manifest(article["article_id"], article["locale"])
                   if storage else None)
            if old and old.get("source_sha256") == course["source_sha256"]:
                skipped += 1
                continue
            if args.dry_run:
                print(article["article_id"], "chapters:", len(course["chapters"]))
            else:
                with tempfile.TemporaryDirectory() as temporary:
                    folder = Path(temporary)
                    narrate(course, folder, voice_path)
                    # A local archive is optional, for restoring audio without re-rendering.
                    if archive_value:
                        import shutil
                        local_archive = (Path(archive_value).expanduser() /
                                         course["article_id"] / course["locale"] /
                                         course["source_sha256"][:20])
                        local_archive.mkdir(parents=True, exist_ok=True)
                        for chapter in course["chapters"]:
                            shutil.copy2(folder / chapter["file"], local_archive)
                    storage.publish(course, folder)
                print("Completed:", article["article_id"])
            created += 1
            if created >= args.max_courses:
                break
    print("Generated:", created, "Unchanged:", skipped)


if __name__ == "__main__":
    main()
