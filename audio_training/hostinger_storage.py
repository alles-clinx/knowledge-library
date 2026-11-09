"""Private SFTP chapter storage on the existing Hostinger hosting account.

Uses a locally held SSH private key and verified host key; no cloud provider needed.
"""
from __future__ import annotations

import json
import os
from pathlib import PurePosixPath

import paramiko


class HostingerStore:
    def __init__(self):
        self.host = os.environ["HOSTINGER_SFTP_HOST"]
        self.user = os.environ["HOSTINGER_SFTP_USER"]
        self.port = int(os.getenv("HOSTINGER_SFTP_PORT", "65002"))
        self.key = os.environ["HOSTINGER_SSH_KEY_PATH"]
        self.root = os.environ["HOSTINGER_AUDIO_PATH"].rstrip("/")
        # Explicitly keep generated training previews outside publicly served folders.
        parts = PurePosixPath(self.root).parts
        if not self.root or ".." in parts or any(
            part in ("public_html", "www") for part in parts
        ):
            raise ValueError("HOSTINGER_AUDIO_PATH must be private and outside public_html")
        self.client = None
        self.sftp = None

    def __enter__(self):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
        self.client.connect(
            self.host, port=self.port, username=self.user,
            key_filename=self.key, look_for_keys=False, allow_agent=False,
            timeout=30, auth_timeout=30,
        )
        self.sftp = self.client.open_sftp()
        return self

    def __exit__(self, *_):
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()

    def folder(self, article_id, locale):
        return f"{self.root}/{article_id}/{locale}"

    def manifest(self, article_id, locale):
        path = self.folder(article_id, locale) + "/manifest.json"
        try:
            with self.sftp.open(path, "rb") as file:
                return json.loads(file.read().decode("utf-8"))
        except FileNotFoundError:
            return None

    def _mkdirs(self, path):
        parts = PurePosixPath(path).parts
        current = "/" if path.startswith("/") else ""
        for part in parts:
            if part == "/":
                continue
            current = f"{current.rstrip('/')}/{part}" if current else part
            try:
                self.sftp.stat(current)
            except FileNotFoundError:
                self.sftp.mkdir(current)

    def publish(self, course, local_folder):
        base = self.folder(course["article_id"], course["locale"])
        version = course["source_sha256"][:20]
        self._mkdirs(f"{base}/versions/{version}")
        for chapter in course["chapters"]:
            remote = f"{base}/versions/{version}/{chapter['file']}"
            local = str(local_folder / chapter["file"])
            self.sftp.put(local, remote, confirm=True)
            chapter["remote_path"] = remote
        # Publish the manifest last; readers never see a partially uploaded course.
        temp = f"{base}/manifest.json.upload-{version}"
        data = json.dumps(course, ensure_ascii=False, indent=2).encode()
        with self.sftp.open(temp, "wb") as file:
            file.write(data)
        self.sftp.posix_rename(temp, f"{base}/manifest.json")
