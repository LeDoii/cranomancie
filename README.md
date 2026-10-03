# Cranomancie

Petit outil de jeu de rôle pour **Elixir RP** : la lecture du crâne chauve selon Oswald Bald, un tirage de trois cartes (les 22 arcanes du tarot de Marseille) à partir de jets de `/roll`.

Tout le contenu (guide d'Oswald Bald, sens des arcanes, phrases) est de l'**invention**. Projet de joueur, sans lien officiel avec le serveur.

> **Nouveau : la v2** (lecture du crâne façon chiromancie, trois jets `/roll 1-20` et jet de polarité) est sur la branche [`v2`](../../tree/v2). Téléchargez son zip dans la release « Cranomancie v2.x ». Cette page décrit la v1 (lecture façon tarot).

## Installation (Windows)

1. Téléchargez le dernier zip dans [Releases](../../releases/latest) et décompressez-le.
2. Double-cliquez sur `cranomancie.bat`.

Au premier lancement, `cranomancie.bat` installe seul ce qui manque :
- **Python** (proposition d'installation via `winget` s'il est absent) ;
- **Pillow** (`requirements.txt`).

La fenêtre s'ouvre sans console. En cas de plantage, la cause est écrite dans `crash.log`.

## Utilisation

- Trois axes : Lignes (le chemin), Bosses (les dons), Forme (la nature). Saisissez le résultat de vos jets : chaque axe se lit dès que ses jets sont valides.
- **Mode A** : un jet `/roll 1-44` par axe. **Mode B** : `/roll 1-20` puis `/roll 1-6` (jet de confirmation sur un 1 ou un 20).
- Chaque champ a des flèches ▲▼ (ou les touches ↑↓←→, la molette) et un bouton 🎲. Boutons « Aléatoire » par axe et général.
- « Collection des cartes » : recherche (nom, numéro `11` ou `XI`, mot-clé), flèches du clavier pour naviguer, volet de détail.
- « Copier la phrase » prépare le texte à dire en jeu. Avec l'option **Format /me**, la phrase est réécrite à la troisième personne et copiée avec `/me` devant : le jeu ajoute lui-même « l'individu » (ex. `/me suit une ligne du crâne du doigt : …` s'affiche « l'individu suit une ligne du crâne du doigt : … »). L'aperçu à l'écran montre le rendu exact du chat.

## En cas de problème

- **Windows affiche « Windows a protégé votre ordinateur » ou un avertissement de sécurité** en ouvrant `cranomancie.bat` : cliquez sur *Informations complémentaires*, puis *Exécuter quand même*. Le fichier est un simple script texte que vous pouvez ouvrir avec le Bloc-notes.
- **« winget n'est pas disponible »** (Windows 10 ancien) : installez Python 3.12 depuis <https://www.python.org/downloads/> en cochant *Add python.exe to PATH* et l'option *tcl/tk and IDLE*, puis relancez `cranomancie.bat`.
- **Python vient d'être installé mais n'est pas détecté** : fermez la fenêtre et relancez `cranomancie.bat`.
- **Échec de l'installation de Pillow ou de Python** : vérifiez votre connexion internet, puis relancez.
- **`winget` demande une confirmation** de Windows : acceptez-la.
- **L'application se ferme aussitôt** : ouvrez `crash.log` (à côté de `app.py`) pour voir la cause.
- **« Aucune carte ne s'affiche » ou polices manquantes** : vérifiez que le dossier `fonts/` est bien présent à côté de `app.py` (ne déplacez pas les fichiers séparément).

## Mises à jour

Au démarrage, l'application vérifie s'il existe une nouvelle release de ce dépôt. Si oui, un bandeau propose « Mettre à jour » : le zip est téléchargé depuis les releases de ce dépôt uniquement, son empreinte SHA-256 est vérifiée, l'ancienne version est copiée dans `_backup/`, les dépendances manquantes sont installées, puis l'application redémarre. Rien ne se fait sans votre clic.

## Emblèmes

Les blasons des maisons et des Wendelhart (dossier `emblems/`) viennent de la page lore du wiki du serveur (<https://wiki.elixirrp.fr/fr/lore>) et appartiennent à leurs auteurs. Si l'un d'eux manque, la carte affiche un sceau géométrique à la place.

## Illustrations

L'illustration de Morzhul (carte XX, dossier `illustrations/`) est un fan art validé sur le Discord du serveur, publié ici avec l'accord de son auteur.

## Polices

Italiana, Crimson Pro et Geist Mono (dossier `fonts/`), sous licence SIL Open Font License.
