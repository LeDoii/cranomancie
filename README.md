# Cranomancie v2 : lecture du crâne chauve façon chiromancie

Petit outil de jeu de rôle pour **Elixir RP** : la lecture du crâne chauve selon Oswald Bald. Trois jets `/roll 1-20` (un par axe : Lignes, Imperfections, Forme) désignent chacun un signe, puis un jet de polarité décide si sa lecture est favorable ou défavorable.

Tout le contenu (guide d'Oswald Bald, signes, définitions, phrases) est de l'**invention**. Projet de joueur, sans lien officiel avec le serveur. La v1 (lecture façon tarot) reste disponible sur la branche `main`.

## Installation (Windows)

1. Téléchargez le zip `cranomancie-v2.x.y.zip` dans les [releases](../../releases) (choisissez une release « v2 ») et décompressez-le.
2. Double-cliquez sur `cranomancie.bat`.

Si Python est absent, `cranomancie.bat` propose de l'installer avec `winget`. La v2 n'a aucune autre dépendance. La fenêtre s'ouvre sans console ; en cas de plantage, la cause est écrite dans `crash.log`.

## Utilisation

- **Trois axes**, chacun avec son jet `/roll 1-20` : Lignes (le chemin), Imperfections (les marques), Forme (la nature). Un même numéro n'a pas la même définition d'un axe à l'autre.
- Chaque champ de jet a des flèches ▲▼ (ou les touches ↑↓←→, la molette) et un bouton 🎲.
- **Polarité** : le bouton « Lancer la polarité » de chaque axe fait un jet de 1 à 20 : pair = lecture favorable, impair = défavorable. Il peut être relancé. Avec la case **Polarité manuelle**, le jet est fait par un autre joueur en jeu et vous saisissez son résultat.
- **Aléatoire** (par axe) et **Tout tirer au hasard** tirent le jet et la polarité.
- **Conclusion** : selon le nombre d'axes favorables, avec le détail des axes favorables et défavorables.
- **Bibliothèque des signes** : les 60 signes, recherche (numéro, signe, mot-clé), volet de détail avec les deux définitions. Un clic sur un signe depuis la lecture y mène.
- **Copier la phrase** prépare le texte à dire en jeu. Avec l'option **Format /me**, la phrase est réécrite à la troisième personne et copiée avec `/me` devant : le jeu ajoute lui-même « l'individu ».

## En cas de problème

- **Windows affiche « Windows a protégé votre ordinateur » ou un avertissement de sécurité** en ouvrant `cranomancie.bat` : cliquez sur *Informations complémentaires*, puis *Exécuter quand même*. C'est un simple script texte, lisible avec le Bloc-notes.
- **« winget n'est pas disponible »** (Windows 10 ancien) : installez Python 3.12 depuis <https://www.python.org/downloads/> en cochant *Add python.exe to PATH* et l'option *tcl/tk and IDLE*, puis relancez `cranomancie.bat`.
- **Python vient d'être installé mais n'est pas détecté** : fermez la fenêtre et relancez `cranomancie.bat`.
- **`winget` demande une confirmation** de Windows : acceptez-la.
- **L'application se ferme aussitôt** : ouvrez `crash.log` (à côté de `app.py`).
- **Polices manquantes** : vérifiez que le dossier `fonts/` est bien à côté de `app.py`.

## Mises à jour

Au démarrage, l'application cherche une release plus récente de la série v2 (les releases v1 sont ignorées). Si elle en trouve une, un bandeau propose « Mettre à jour » : le zip est téléchargé depuis les releases de ce dépôt uniquement, son empreinte SHA-256 est vérifiée, l'ancienne version est copiée dans `_backup/`, puis l'application redémarre. Rien ne se fait sans votre clic.

## Polices

Italiana, Crimson Pro et Geist Mono (dossier `fonts/`), sous licence SIL Open Font License.
