# Alle's ClinX — unattended chapter audio training

This repository contains a daily scheduled audio production pipeline for approved Knowledge Library content. It is designed for **your existing Mac plus your 50 GB Hostinger hosting space**. No S3 bucket, AWS IAM role, Cloudflare R2, paid remote GPU, or daily ChatGPT interaction is needed.

## Flow

1. GitHub Actions checks approved, currently live articles in `production/live.json` every day at approximately 10:00 AM India time.
2. Each article becomes one narrated course, with an introduction and its H2 sections becoming separate chapters. The text is extracted without LLM rewriting.
3. Only `editorial_status=english-locked` (English) and `translation-locked` (Hindi, future) are eligible. Review-stage Hindi is excluded. The initial scheduled job generates **English only**.
4. A consented local Indian-accent voice reference is used by the Chatterbox Multilingual V3 model on the Mac. The model runs on Apple Silicon MPS where available, otherwise CPU; actual performance and compatibility must be verified on your Mac.
5. The MP3 chapters and JSON manifest are uploaded via authenticated **SFTP to a private directory outside `public_html`** on Hostinger. The final manifest is published only after all audio files upload.
6. Existing content-and-voice hashes are compared against the Hostinger manifest. Unchanged courses are skipped. Up to two new or changed courses are handled per day.
7. Optionally keep a local MP3 archive on the Mac using `AUDIO_LOCAL_ARCHIVE_PATH` to avoid depending on the hosting account as the only copy.

## One-time setup on your Mac

1. Install Python 3.11 and FFmpeg. Make sure `python3.11` is visible to the GitHub runner's account. Verify `ffmpeg -version`.
2. Open GitHub repository > Settings > Actions > Runners, add a **self-hosted macOS runner**, and follow the supplied Mac registration commands. Give it the custom label `clinx-audio`. Install it as an automatic service using the runner directory's `./svc.sh install` and `./svc.sh start`. Keep the Mac awake, connected and logged in as needed.
3. Record or license a suitable clean Indian-English voice reference WAV (with speaker consent) and store it outside the repository at a stable local path, for example `~/clinx-private/voices/en-reference.wav`.
4. In Hostinger hPanel, check that the plan provides SSH/SFTP access. Hostinger commonly uses SFTP port 65002, but configure the actual port shown by hPanel. Enable SSH/SFTP, create an SSH key on your Mac, register the public key with Hostinger, and **verify the server's host key fingerprint** before adding it to the Mac runner user's `~/.ssh/known_hosts`. Do not place passwords or private keys in GitHub.
5. Choose a directory in the Hostinger account's private home space, for example `clinx-training-audio`. It must be writable via SFTP and **outside `public_html`**. This keeps unreviewed training previews non-public.
6. Set these **GitHub Actions repository variables** (not secrets):
   - `HOSTINGER_SFTP_HOST`: hPanel's SSH/SFTP hostname or IP
   - `HOSTINGER_SFTP_USER`: hosting SSH username
   - `HOSTINGER_SFTP_PORT`: typically `65002`
   - `HOSTINGER_SSH_KEY_PATH`: path to the Mac runner user's private SSH key
   - `HOSTINGER_AUDIO_PATH`: private remote directory, e.g. `clinx-training-audio`
   - `AUDIO_VOICE_EN_PATH`: absolute path to the Mac's consented English reference WAV
   - optional `AUDIO_LOCAL_ARCHIVE_PATH`: path for a Mac-side MP3 backup folder
7. Run a **one-off pilot** and listen for Indian-accent naturalness, chemical names, numerical ratios and other operational terms. Review output for safety before public course release. Check actual Mac CPU/MPS performance before depending on unattended output.
8. Merge the PR after validation. Set `ENABLE_AUDIO_RENDER=true` only after the Mac and Hostinger SFTP connection are working. Unset it to pause all synthesis.

## Quick testing

From the repository root:

```bash
python3.11 -m unittest discover -s tests -p 'test_audio_training.py' -v
python3.11 audio_training/pipeline.py --dry-run --max-courses 2
```

The scheduled workflow automatically installs requirements in the Mac user's `~/.clinx-audio-venv`. It does not access AWS or other cloud storage APIs. To produce audio, invoke the workflow manually from GitHub Actions for a first pass, after all variables, SSH keys and voice recording have been configured.

## Limitations and safeguards

- SFTP remote access depends on your Hostinger plan. The 50 GB figure is the total plan allocation, **not guaranteed free space**; reserve capacity for website files, backups and email if they share a quota.
- Mac sleep, shutdown, lost internet, broken SSH access, or unavailable model dependencies can delay production. GitHub may also delay cron jobs.
- Chatterbox voice cloning and pronunciation are imperfect. This prototype skips HTML tables and references in audio narration, so it **must not be used as the sole presentation** of concentration, dilution, dosage or safety-critical operating instructions.
- This stage **stores private audio previews**, not public streaming courses. An approved player/publishing integration and validation of audio quality are still needed.
- The job is a pilot implementation. It has not yet been end-to-end tested on your Mac.
- Keep local SSH private keys, your reference voice and Hostinger account details out of the repository.
