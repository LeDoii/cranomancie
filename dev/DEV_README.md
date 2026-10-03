> Outils et sources du mainteneur (sauvegarde). Ils se lancent depuis le dossier de travail du projet, à côté des fichiers de l'application, pas depuis ce dossier `dev/`. Le contenu est de l'invention (guide d'Oswald Bald).

# Cranomancie v2 : lecture du crâne chauve façon chiromancie (brouillon)

Fork de la v1 (`../CraneChauve/`, laissée intacte). Contenu **inventé** (guide d'Oswald Bald).

- **Mécanique :** 3 jets `/roll 1-20` en jeu, un par axe (Lignes, Imperfections, Forme). Chaque résultat désigne un signe différent selon l'axe ; un jet de polarité fait par l'interface (bouton par axe, relançable, pair = favorable, impair = défavorable) choisit la définition. Le bouton « Aléatoire » d'un axe tire aussi sa polarité. 3 × 20 × 2 = 120 définitions.
- **Sources de données :** `DEFINITIONS_v1.md` (validé : « on garde tout, je remplacerai plus tard ») → `python build_data.py` → `data.json`.
- **Code :** `reading.py` (logique), `app.py` (fenêtre, vue Lecture), `library.py` (Bibliothèque des 60 signes, recherche, volet de détail).
- **Lancement de test :** `python app.py`.
- **Illustrations :** aucune (décision de l'utilisateur).
- **Lanceur et mise à jour :** `cranomancie.bat` (installe Python via winget si besoin) et `updater.py` (ne regarde que les releases `v2.x`).

## Tester la mise à jour

- `python test_update.py` : test réel. Une copie de l'application se déclare en v2.0.0 dans `%TEMP%\cranomancie_update_test` ; le bandeau « Mise à jour disponible » propose la dernière release v2.x de GitHub. Cliquer, laisser télécharger et redémarrer.
- `python test_update.py --fake` : test sans GitHub. Un petit serveur local sert une fausse release v2.99.0 dont le sous-titre se termine par « MISE À JOUR DE TEST INSTALLÉE ».
- Dans les deux cas, modifier un signe dans la copie avant la mise à jour permet de vérifier que la modification survit (elle est stockée dans `%APPDATA%\Cranomancie\custom_signs.json`). Entrée dans la console pour supprimer la copie.
- Détails techniques : un fichier identique n'est pas recopié ; un fichier verrouillé par l'application (les polices) qui aurait changé est mis de côté dans `_pending/` et appliqué au prochain démarrage. L'ancienne version est sauvegardée dans `_backup/`.

## Publication (GitHub)

Branche `v2` de https://github.com/LeDoii/cranomancie (worktree local `../Cranomancie_repo_v2`, branche orpheline : seuls les fichiers d'exécution). Nouvelle version : modifier `version.txt` -> `python publish.py` (crée `staging/` et `dist/cranomancie-vX.Y.Z.zip` + `.sha256`) -> copier `staging/` dans `../Cranomancie_repo_v2`, commit et push `v2` -> `gh release create vX.Y.Z <zip> <sha256> --repo LeDoii/cranomancie --target v2 --latest=false`. Le `--latest=false` est indispensable : la v1 lit `releases/latest` et ne doit jamais voir une release v2.
