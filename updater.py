"""Self-update from GitHub Releases for the v2 line (standard library only).

Only releases tagged v2.x are considered, so the v1 application (tags v1.x) and this one never
mix. Flow: check in the background, ask the user, download the zip from this repository's release
assets only, verify its SHA-256, back up the current files, copy the new ones, install the
requirements (if any), then restart.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

REPO = "LeDoii/cranomancie"
MAJOR = 2
APP_DIR = Path(__file__).resolve().parent
# Test hooks (see test_update.py): a local server can stand in for GitHub. Never set in normal use.
API_RELEASES = os.environ.get("CRANOMANTIE_UPDATE_API") or f"https://api.github.com/repos/{REPO}/releases?per_page=50"
ALLOWED_PREFIX = os.environ.get("CRANOMANTIE_UPDATE_ALLOW") or f"https://github.com/{REPO}/releases/download/"
BACKUP_DIR = APP_DIR / "_backup"
PENDING_DIR = APP_DIR / "_pending"  # files locked by the running app (the fonts), applied at the next start
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW (Windows)
TIMEOUT = 10


def local_version() -> str:
    try:
        return (APP_DIR / "version.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


def parse_version(text: str) -> tuple[int, ...]:
    """'v2.1.0' / '2.0.0-dev' -> (2, 1, 0) / (2, 0, 0)."""
    core = re.split(r"[-+]", text.strip().lstrip("v"))[0]
    return tuple(int(part) for part in core.split("."))


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "cranomancie-updater",
                                                   "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def check_latest() -> dict | None:
    """Return release info if a newer v2.x release exists, else None (also None when offline)."""
    try:
        candidates = []
        for release in json.loads(_get(API_RELEASES)):
            if release.get("draft"):
                continue
            version = parse_version(release["tag_name"])
            if version[0] == MAJOR:
                candidates.append((version, release))
        if not candidates:
            return None
        version, release = max(candidates, key=lambda item: item[0])
        if version <= parse_version(local_version()):
            return None
        assets = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}
        zip_name = next(n for n in assets if n.endswith(".zip"))
        return {"version": release["tag_name"].lstrip("v"), "zip_url": assets[zip_name],
                "sha_url": assets.get(zip_name + ".sha256", ""), "notes": release.get("body") or ""}
    except Exception:
        return None


def check_async(result: dict) -> None:
    """Run check_latest in a thread; the outcome lands in result['info'] and result['done']."""
    def work() -> None:
        result["info"] = check_latest()
        result["done"] = True
    threading.Thread(target=work, daemon=True).start()


def _download(url: str, dest: Path) -> None:
    if not url.startswith(ALLOWED_PREFIX):
        raise ValueError(f"URL refusée (hors du dépôt {REPO}) : {url}")
    dest.write_bytes(_get(url))


def _safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    root = target.resolve()
    for member in archive.namelist():
        if not (target / member).resolve().is_relative_to(root):
            raise ValueError(f"Chemin suspect dans l'archive : {member}")
    archive.extractall(target)


def install_requirements() -> None:
    """pip install -r requirements.txt when it lists packages (no console window)."""
    requirements = APP_DIR / "requirements.txt"
    if not requirements.exists() or not any(
            line.strip() and not line.strip().startswith("#") for line in requirements.read_text(encoding="utf-8").splitlines()):
        return
    exe = Path(sys.executable)
    python = exe.with_name("python.exe") if exe.with_name("python.exe").exists() else exe
    subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements)],
                   check=True, capture_output=True, creationflags=NO_WINDOW if sys.platform == "win32" else 0)


def apply_update(info: dict) -> None:
    """Download, verify and install the release. Raises on any problem, leaving the app untouched."""
    if not info["sha_url"]:
        raise ValueError("Empreinte SHA-256 absente de la release : mise à jour refusée.")
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        archive_path = tmp / "update.zip"
        _download(info["zip_url"], archive_path)
        expected = _get(info["sha_url"]).decode("utf-8").split()[0].lower()
        if hashlib.sha256(archive_path.read_bytes()).hexdigest() != expected:
            raise ValueError("Empreinte SHA-256 incorrecte : mise à jour annulée.")
        extracted = tmp / "new"
        with zipfile.ZipFile(archive_path) as archive:
            _safe_extract(archive, extracted)

        # Back up every file about to be replaced, then copy the new files over. Identical files are
        # skipped: the fonts are locked by the running app and almost never change. A locked file that
        # did change is staged in _pending and applied by apply_pending() at the next start.
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        if PENDING_DIR.exists():
            shutil.rmtree(PENDING_DIR, ignore_errors=True)
        for source in extracted.rglob("*"):
            if source.is_dir():
                continue
            relative = source.relative_to(extracted)
            current = APP_DIR / relative
            if current.exists():
                if current.stat().st_size == source.stat().st_size and current.read_bytes() == source.read_bytes():
                    continue
                (BACKUP_DIR / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current, BACKUP_DIR / relative)
            current.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(source, current)
            except OSError:  # locked by this process (Windows): finish it at the next start
                (PENDING_DIR / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, PENDING_DIR / relative)
    install_requirements()


def apply_pending() -> None:
    """At startup, before the fonts are loaded: move the files staged by the last update into place."""
    if not PENDING_DIR.exists():
        return
    for _ in range(10):  # the previous window may still be closing: retry for a few seconds
        left = False
        for source in list(PENDING_DIR.rglob("*")):
            if source.is_dir():
                continue
            target = APP_DIR / source.relative_to(PENDING_DIR)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                source.unlink()
            except OSError:
                left = True
        if not left:
            shutil.rmtree(PENDING_DIR, ignore_errors=True)
            return
        time.sleep(0.5)


def restart() -> None:
    """Start a fresh copy of the app; the caller closes the current window."""
    subprocess.Popen([sys.executable, str(APP_DIR / "app.py")], cwd=str(APP_DIR))
