> Outils et sources du mainteneur (sauvegarde). Ils se lancent depuis le dossier de travail du projet, à côté des fichiers de l'application, pas depuis ce dossier `dev/`. Le contenu est de l'invention (guide d'Oswald Bald).

# Cranomancie — divination sur crâne chauve (v1, brouillon)

Contenu **inventé** (guide d'Oswald Bald, aucune source). Seuls les ancrages lore sont sourcés (`Data/Livre premiere année/`). Le nom « Cranomancie » est celui choisi par l'utilisateur.

## Fichiers

- `ARCANES_v1.md` : 22 sens de base (validés par l'utilisateur) ; source du JSON.
- `FILTRES_v2.md` : axes Lignes / Bosses / Forme (remplace `FILTRES_v1.md`).
- `build_data.py` : lit `ARCANES_v1.md` + axes et phrases, écrit `data.json`.
- `reading.py` : logique pure (jet -> arcane, sens, phrase, conclusion). `python reading.py` vérifie les deux modes.
- `cards.py` : cartes dessinées par script (provisoires, en attente de références). `python cards.py` produit `cards_contact.png`.
- `app.py` : interface (tkinter + Pillow, aucune dépendance en plus). Lancement : `cranomancie.bat` ou `python app.py`.

## Modes de jet

- **Mode A** : 1 jet par axe, `/roll 1-44`. 1 à 22 : arcane 0 à 21 à l'endroit ; 23 à 44 : le même arcane à l'envers. Tirage équitable.
- **Mode B** : `/roll 1-20` (arcane I à XX) puis `/roll 1-6` (4 à 6 : à l'envers). Sur un 1 ou un 20, un jet de confirmation `/roll 1-6` : 5 ou 6 donne Le Mat (0) ou Le Monde (XXI), qui sont donc plus rares.

Après modification de `ARCANES_v1.md` ou des phrases : relancer `python build_data.py`.

## Interface

- Une seule fenêtre, ouverte en grand (maximisée), redimensionnable : polices, cartes et textes s'adaptent à la taille.
- Deux vues, au choix dans la barre du haut : « Lecture » et « Collection des cartes » (pas de nouvelle fenêtre).
- Collection : grille qui se réorganise selon la largeur, recherche par nom, numéro (`11` ou `XI`, `0` pour Le Mat), mot-clé ou lore. Un clic sur une carte ouvre un volet sur le côté (carte à l'endroit/à l'envers, sens, ancrage, lectures par axe) ; « Fermer » le replie.
- Boutons « Aléatoire » par axe et « Tout tirer au hasard » : remplissent les jets du mode courant.
- Chaque champ de jet : flèches ▲▼ cliquables, touches ↑/→ (+1) et ↓/← (−1), molette, et bouton 🎲 pour tirer ce champ seul (dans la plage permise).
- Collection : les 4 flèches déplacent la sélection dans la grille (le volet suit), Échap ferme le volet. La carte fait partie du contenu défilant du volet.

## Publication (GitHub)

Dépôt public : https://github.com/LeDoii/cranomancie (dossier local `../Cranomancie_repo`, copie des fichiers d'exécution seulement ; `Data/`, les brouillons de lore et les captures n'y vont jamais).

Nouvelle version : modifier `version.txt` → `python publish.py` (copie dans `../Cranomancie_repo`, crée `dist/cranomancie-vX.Y.Z.zip` et son `.sha256`) → commit et push dans `../Cranomancie_repo` → `gh release create vX.Y.Z dist/<zip> dist/<zip>.sha256 --repo LeDoii/cranomancie`. L'application des utilisateurs propose alors la mise à jour (téléchargement vérifié par SHA-256, sauvegarde dans `_backup/`, `pip install -r requirements.txt`, redémarrage).
