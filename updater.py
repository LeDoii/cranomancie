"""Self-update from GitHub Releases (standard library only).

Flow: check the latest release in the background, ask the user, download the zip
from this repository's release assets only, verify its SHA-256, back up the current
files, copy the new ones, install the requirements, then restart.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

REPO = "LeDoii/cranomancie"
APP_DIR = Path(__file__).resolve().parent
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
ALLOWED_PREFIX = f"https://github.com/{REPO}/releases/download/"
BACKUP_DIR = APP_DIR / "_backup"
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW (Windows)
TIMEOUT = 10
OBSOLETE_FILES = ["lancer.bat"]  # renamed in 1.0.1 (cranomancie.bat)


def local_version() -> str:
    try:
        return (APP_DIR / "version.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.strip().lstrip("v").split("."))


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "cranomancie-updater",
                                                   "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def check_latest() -> dict | None:
    """Return release info if a newer version exists, else None (also None when offline)."""
    try:
        release = json.loads(_get(API_LATEST))
        version = release["tag_name"].lstrip("v")
        if parse_version(version) <= parse_version(local_version()):
            return None
        assets = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}
        zip_name = next(n for n in assets if n.endswith(".zip"))
        return {"version": version, "zip_url": assets[zip_name],
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
    """pip install -r requirements.txt with the interpreter running the app (no console window)."""
    exe = Path(sys.executable)
    python = exe.with_name("python.exe") if exe.with_name("python.exe").exists() else exe
    subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                    "-r", str(APP_DIR / "requirements.txt")],
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

        # Back up every file about to be replaced, then copy the new files over.
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        for source in extracted.rglob("*"):
            if source.is_dir():
                continue
            relative = source.relative_to(extracted)
            current = APP_DIR / relative
            if current.exists():
                (BACKUP_DIR / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current, BACKUP_DIR / relative)
            current.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, current)
    for name in OBSOLETE_FILES:
        (APP_DIR / name).unlink(missing_ok=True)
    install_requirements()


def restart() -> None:
    """Start a fresh copy of the app; the caller closes the current window."""
    subprocess.Popen([sys.executable, str(APP_DIR / "app.py")], cwd=str(APP_DIR))
