"""Build the public repo folder and the release zip (dev tool, not published).

Usage: python publish.py   -> ../Cranomancie_repo/ (git working tree) and dist/ (zip + sha256)
"""
import hashlib
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
REPO_DIR = HERE.parent / "Cranomancie_repo"
DIST = HERE / "dist"

RUNTIME_FILES = ["app.py", "collection.py", "cards.py", "reading.py", "updater.py", "data.json",
                 "version.txt", "requirements.txt", "cranomancie.bat",
                 "fonts/CrimsonPro.ttf", "fonts/Italiana-Regular.ttf", "fonts/GeistMono.ttf",
                 "emblems/wendelhart_blason.png", "emblems/azuralys.png", "emblems/felora.png",
                 "emblems/ferrox.png", "emblems/oragonn.png",
                 "illustrations/morzhul.png"]


def main() -> None:
    version = (HERE / "version.txt").read_text(encoding="utf-8").strip()
    REPO_DIR.mkdir(exist_ok=True)
    for name in RUNTIME_FILES:
        target = REPO_DIR / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / name, target)
    shutil.copy2(HERE / "README_REPO.md", REPO_DIR / "README.md")
    (REPO_DIR / ".gitignore").write_text("__pycache__/\ncrash.log\n_backup/\ndist/\n", encoding="utf-8")

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
