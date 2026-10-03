"""Try the automatic update safely, in a throwaway copy of the application (dev tool, not published).

    python test_update.py          real test: the copy claims to be v2.0.0, so the update banner offers the
                                   latest real v2.x release from GitHub; click "Mettre à jour".
    python test_update.py --fake   fake test: a local server serves a fake v2.99.0 (the subtitle changes, so
                                   you can see the update happened). Nothing is downloaded from GitHub.

The copy lives in %TEMP%/cranomancie_update_test and is deleted when you press Enter. Your edits of the
signs (stored outside the application folder) are shared with the copy: edit a sign in it, update, and
check that your edit is still there.
"""
import hashlib
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import zipfile
from pathlib import Path

from publish import RUNTIME_FILES

HERE = Path(__file__).parent
FAKE_TAG = "2.99.0"  # a fake v2.x release, newer than any real one


def copy_app(target: Path, version: str) -> None:
    if target.exists():
        shutil.rmtree(target)
    for name in RUNTIME_FILES:
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / name, dest)
    (target / "version.txt").write_text(version + "\n", encoding="utf-8")


def build_fake_release(directory: Path) -> tuple[Path, str]:
    """A zip of the current app, as version 2.99.0, with a visible change (the subtitle)."""
    stage = directory / "stage"
    copy_app(stage, FAKE_TAG)
    data = json.loads((stage / "data.json").read_text(encoding="utf-8"))
    data["meta"]["subtitle"] += " — MISE À JOUR DE TEST INSTALLÉE"
    (stage / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = directory / f"cranomancie-v{FAKE_TAG}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in RUNTIME_FILES:
            archive.write(stage / name, name)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (directory / f"{zip_path.name}.sha256").write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    return zip_path, digest


def serve(directory: Path, port_holder: list) -> socketserver.TCPServer:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, *args):  # keep the console quiet
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    port_holder.append(server.server_address[1])
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> None:
    fake = "--fake" in sys.argv
    work = Path(tempfile.gettempdir()) / "cranomancie_update_test"
    app_dir = work / "app"
    work.mkdir(exist_ok=True)
    copy_app(app_dir, "2.0.0")
    env = dict(os.environ)
    server = None
    if fake:
        www = work / "www"
        www.mkdir(exist_ok=True)
        zip_path, _ = build_fake_release(www)
        ports: list = []
        server = serve(www, ports)
        base = f"http://127.0.0.1:{ports[0]}/"
        release = [{"tag_name": f"v{FAKE_TAG}", "draft": False, "body": "Release de test locale",
                    "assets": [{"name": zip_path.name, "browser_download_url": base + zip_path.name},
                               {"name": zip_path.name + ".sha256", "browser_download_url": base + zip_path.name + ".sha256"}]}]
        (www / "releases").write_text(json.dumps(release), encoding="utf-8")
        env["CRANOMANTIE_UPDATE_API"] = base + "releases"
        env["CRANOMANTIE_UPDATE_ALLOW"] = base
        print(f"Serveur de test local : {base} (fausse release v{FAKE_TAG})")
    else:
        print("Test réel : la copie se déclare en v2.0.0, elle proposera la dernière release v2.x de GitHub.")
    subprocess.Popen([sys.executable, str(app_dir / "app.py")], cwd=str(app_dir), env=env)
    print(f"\nCopie de test : {app_dir}\n"
          "1. Dans la fenêtre, un bandeau orange « Mise à jour disponible » doit apparaître en haut.\n"
          "2. Cliquez sur « Mettre à jour » : téléchargement, vérification, installation, redémarrage.\n"
          + ("3. Le sous-titre doit se terminer par « MISE À JOUR DE TEST INSTALLÉE ».\n" if fake else
             "3. Le titre de la fenêtre doit afficher la nouvelle version.\n")
          + "4. Le dossier _backup de la copie contient les anciens fichiers.\n")
    input("Appuyez sur Entrée pour arrêter le test et supprimer la copie... ")
    if server:
        server.shutdown()
    shutil.rmtree(work, ignore_errors=True)
    print("Copie de test supprimée.")


if __name__ == "__main__":
    main()
