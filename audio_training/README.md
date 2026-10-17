# Alle's ClinX automated chapter audio

This is a scheduled production job, not a daily ChatGPT reminder. Once deployed, it converts approved Knowledge Library articles into privately stored MP3 chapter courses without routine operator involvement.

## Production rules

- Sources: article JSON files in `articles/`, only IDs listed in `production/live.json`.
- English is generated only when `editorial_status=english-locked`. Hindi requires `translation-locked` and is disabled in the initial workflow. Review-stage Hindi is excluded.
- Each eligible article is one course. The introduction and H2 sections become chapters.
- Reads existing source text without AI paraphrasing. Tables and reference bibliographies are omitted because speaking tabular content can be unsafe. Do not treat this as an exact recitation of product instructions, SDS, or dosage tables.
- Outputs: chapter MP3 files, chapter titles and transcript segments in a manifest, all stored in private S3.
- A stable manifest pointer appears only after every versioned audio file is uploaded.
- New or changed approved content is regenerated, but unchanged content is skipped using a content-and-voice hash.
- Default pace is up to two courses per day at approximately 10 AM India time.

## One-time setup (required before real audio generation)

1. Install a dedicated self-hosted Linux GitHub Actions runner with labels `self-hosted`, `linux`, `tts-gpu`, NVIDIA CUDA, Python 3.11 and FFmpeg.
2. Create a private AWS S3 bucket. Upload a short, consented/licensed Indian-English speaker reference WAV to `voices/english.wav`. For optional Hindi, provide a separate reference.
3. Configure a limited AWS GitHub OIDC IAM role (scoped to this repository's `main` branch; S3 access only to the chosen bucket and voice objects).
4. Set Actions repository variables: `AUDIO_AWS_REGION`, `AUDIO_AWS_ROLE_ARN`, `AUDIO_S3_BUCKET`, `AUDIO_VOICE_EN_KEY`. Optional Hindi: `AUDIO_VOICE_HI_KEY`.
5. The daily workflow always tests the parser and performs a lightweight source dry-run. After the runner, voice and bucket are tested, set `ENABLE_AUDIO_RENDER=true` to activate TTS and upload. No credentials or audio reference files belong in Git.
6. Start with a limited `workflow_dispatch` pilot and listen for pronunciation accuracy before enabling any audience-facing release.

## Commands

```bash
python -m unittest discover -s tests -p test_audio_training.py -v
python audio_training/pipeline.py --dry-run --max-courses 2
```

Live rendering uses `pip install -r audio_training/requirements-tts.txt`, Chatterbox Multilingual V3, a CUDA GPU and FFmpeg.

## Limits

- The workflow does not integrate with the public LMS/player yet; it only builds audio in private S3.
- Generated speech is not guaranteed free of hallucinated phonemes or mispronounced ratios. Product- or facility-specific safety training requires pronunciation/accuracy QA before distribution.
- GPU infrastructure and storage cost money; GitHub scheduled runs can be delayed.
- Voice recordings require consent and appropriate licensing.
- The pipeline is a pilot implementation. Actual TTS runtime and performance must be validated on the connected GPU runner.
