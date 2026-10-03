"""Build the v2 release zip and the staging folder (dev tool, not published).

Usage: python publish.py   -> dist/cranomancie-vX.Y.Z.zip + .sha256, and staging/ (the files of the v2 branch)
"""
import hashlib
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
STAGING = HERE / "staging"
DIST = HERE / "dist"

RUNTIME_FILES = ["app.py", "library.py", "reading.py", "reading_view.py", "widgets.py", "title_art.py", "signs_text.py", "updater.py",
                 "data.json", "version.txt", "requirements.txt", "cranomancie.bat", "viktor/viktor_boule.png",
                 "fonts/CrimsonPro.ttf", "fonts/Italiana-Regular.ttf", "fonts/GeistMono.ttf"]


def main() -> None:
    version = (HERE / "version.txt").read_text(encoding="utf-8").strip()
    if STAGING.exists():
        shutil.rmtree(STAGING)
    for name in RUNTIME_FILES:
        target = STAGING / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / name, target)
    shutil.copy2(HERE / "README_REPO.md", STAGING / "README.md")
    (STAGING / ".gitignore").write_text("__pycache__/\ncrash.log\n_backup/\ndist/\n", encoding="utf-8")

    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"cranomancie-v{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in RUNTIME_FILES:
            archive.write(HERE / name, name)  # files at the archive root
        archive.write(HERE / "README_REPO.md", "README.md")
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (DIST / f"{zip_path.name}.sha256").write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    print(zip_path, digest)


if __name__ == "__main__":
    main()
