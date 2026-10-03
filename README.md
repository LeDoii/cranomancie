# Cranomancie

Petit outil de jeu de rôle pour **Elixir RP** : la lecture du crâne chauve selon Oswald Bald, un tirage de trois cartes (les 22 arcanes du tarot de Marseille) à partir de jets de `/roll`.

Tout le contenu (guide d'Oswald Bald, sens des arcanes, phrases) est de l'**invention**. Il n'accorde aucun bonus de jeu et reste du background tant que le staff ne l'a pas validé. Projet de fan, sans lien officiel avec le serveur.

## Installation (Windows)

1. Téléchargez le dernier zip dans [Releases](../../releases/latest) et décompressez-le.
2. Double-cliquez sur `lancer.bat`.

Au premier lancement, `lancer.bat` installe seul ce qui manque :
- **Python** (proposition d'installation via `winget` s'il est absent) ;
- **Pillow** (`requirements.txt`).

La fenêtre s'ouvre sans console. En cas de plantage, la cause est écrite dans `crash.log`.

## Utilisation

- Trois axes : Lignes (le chemin), Bosses (les dons), Forme (la nature). Saisissez le résultat de vos jets : chaque axe se lit dès que ses jets sont valides.
- **Mode A** : un jet `/roll 1-44` par axe. **Mode B** : `/roll 1-20` puis `/roll 1-6` (jet de confirmation sur un 1 ou un 20).
- Chaque champ a des flèches ▲▼ (ou les touches ↑↓←→, la molette) et un bouton 🎲. Boutons « Aléatoire » par axe et général.
- « Collection des cartes » : recherche (nom, numéro `11` ou `XI`, mot-clé), flèches du clavier pour naviguer, volet de détail.
- « Copier la phrase » prépare le texte à dire en jeu (option : préfixe `/me`).

## Mises à jour

Au démarrage, l'application vérifie s'il existe une nouvelle release de ce dépôt. Si oui, un bandeau propose « Mettre à jour » : le zip est téléchargé depuis les releases de ce dépôt uniquement, son empreinte SHA-256 est vérifiée, l'ancienne version est copiée dans `_backup/`, les dépendances manquantes sont installées, puis l'application redémarre. Rien ne se fait sans votre clic.

## Polices

Italiana, Crimson Pro et Geist Mono (dossier `fonts/`), sous licence SIL Open Font License.
