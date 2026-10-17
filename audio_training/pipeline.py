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


def already_generated(s3, bucket, key, signature):
    try:
        saved = json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read())
        return saved.get("source_sha256") == signature
    except Exception as exc:
        if getattr(exc, "response", {}).get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return False
        raise


def narrate(course, out, voice):
    import torch
    import torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required for Chatterbox V3")
    model = ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3")
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


def publish(s3, bucket, prefix, course, out):
    base = "/".join([prefix.strip("/"), course["article_id"], course["locale"]])
    version = course["source_sha256"][:20]
    for chapter in course["chapters"]:
        key = f"{base}/versions/{version}/{chapter['file']}"
        s3.upload_file(str(out / chapter["file"]), bucket, key,
                       ExtraArgs={"ContentType": "audio/mpeg", "ServerSideEncryption": "AES256"})
        chapter["object_key"] = key
    # Publish manifest last so no reader observes incomplete audio.
    s3.put_object(Bucket=bucket, Key=f"{base}/manifest.json",
                  Body=json.dumps(course, ensure_ascii=False, indent=2).encode(),
                  ContentType="application/json", ServerSideEncryption="AES256")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--max-courses", type=int, default=2)
    ap.add_argument("--locales", nargs="+", default=["en"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.max_courses < 1:
        ap.error("max-courses must be positive")
    bucket = os.getenv("AUDIO_S3_BUCKET", "")
    prefix = os.getenv("AUDIO_S3_PREFIX", "audio-training/v1")
    if not args.dry_run and not bucket:
        ap.error("AUDIO_S3_BUCKET is required")
    if not args.dry_run:
        import boto3
        s3 = boto3.client("s3")
    created, skipped = 0, 0
    for article in select(args.root, set(args.locales)):
        voice_var = "VOICE_REFERENCE_HI_KEY" if article["locale"] == "hi-IN" else "VOICE_REFERENCE_EN_KEY"
        voice_key = os.getenv(voice_var, "")
        if not args.dry_run and not voice_key:
            raise RuntimeError(voice_var + " is required for Indian-accent narration")
        course = package(article, voice_key or "dry-run")
        manifest_key = "/".join([prefix.strip("/"), article["article_id"],
                                 article["locale"], "manifest.json"])
        if not args.dry_run and already_generated(s3, bucket, manifest_key, course["source_sha256"]):
            skipped += 1
            continue
        if args.dry_run:
            print(article["article_id"], "chapters:", len(course["chapters"]))
        else:
            with tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                reference = folder / "consented-reference.wav"
                s3.download_file(bucket, voice_key, str(reference))
                narrate(course, folder, reference)
                publish(s3, bucket, prefix, course, folder)
            print("Completed:", article["article_id"])
        created += 1
        if created >= args.max_courses:
            break
    print("Generated:", created, "Unchanged:", skipped)


if __name__ == "__main__":
    main()
