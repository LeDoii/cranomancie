"""Build data.json for the Cranomancie v2 GUI (palmistry-style skull reading).

The 120 definitions are parsed from DEFINITIONS_v1.md (single source of truth);
axes, phrase intros and the synthesis table are declared here. All content is invented.
"""
import json
import re
from pathlib import Path

from signs_text import with_article

HERE = Path(__file__).parent

META = {
    "title": "CRANOMANTIE 2000",
    "subtitle": "La lecture du crâne chauve selon Oswald Bald",
}

# id, label, name, what Viktor looks at, question, spoken intro, /me action
AXES = [
    {"id": "lignes", "label": "Lignes", "with_article": "les Lignes", "nom": "Le Chemin",
     "observe": "Sutures, plis et sillons de la peau du crâne",
     "question": "D'où vient la personne, où va sa route ?",
     "spoken": "Sur les lignes de votre crâne",
     "me": "suit du doigt les lignes du crâne et relève"},
    {"id": "imperfections", "label": "Imperfections", "with_article": "les Imperfections", "nom": "Les Marques",
     "observe": "Cicatrices, grains de beauté, bosses, taches, reliefs",
     "question": "Quels dons et quelles faiblesses porte la personne ?",
     "spoken": "Parmi les marques de votre crâne",
     "me": "examine les marques du crâne et relève"},
    {"id": "forme", "label": "Forme", "with_article": "la Forme", "nom": "La Nature",
     "observe": "Contour général, proportions, symétrie",
     "question": "Qui est la personne au fond, vers quoi tend-elle ?",
     "spoken": "Dans la forme de votre crâne",
     "me": "observe la forme du crâne et relève"},
]

SYNTHESIS = {
    3: "Les trois signes sont favorables : le présage est très favorable, les signes s'accordent.",
    2: "Deux signes sont favorables : le présage est favorable, avec un point de vigilance sur le signe défavorable.",
    1: "Un seul signe est favorable : le présage est mitigé, ce signe est un appui et les deux autres demandent de la prudence.",
    0: "Aucun signe n'est favorable : le crâne parle avec gravité, mais ce n'est qu'un avertissement.",
}
ME_SYNTHESIS_PREFIX = "conclut sa lecture : "


def parse_signs(path: Path) -> list[list[dict]]:
    """Return three lists of 20 signs, in axis order."""
    axes: list[list[dict]] = []
    active = False  # only the three numbered sections hold sign tables
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            active = bool(re.match(r"^## \d\. ", line))
            if active:
                axes.append([])
        elif active and re.match(r"^\|\s*\d+\s*\|", line):
            n, sign, fav, unf = [c.strip() for c in line.strip().strip("|").split(" | ")]
            axes[-1].append({"n": int(n), "sign": sign, "sign_art": with_article(sign), "fav": fav, "unf": unf})
    if [len(a) for a in axes] != [20, 20, 20]:
        raise SystemExit(f"expected 3 axes of 20 signs, got {[len(a) for a in axes]}")
    return axes


def main() -> None:
    signs = parse_signs(HERE / "DEFINITIONS_v1.md")
    axes = [dict(axis, signs=signs[i]) for i, axis in enumerate(AXES)]
    data = {"meta": META, "axes": axes, "synthesis": {str(k): v for k, v in SYNTHESIS.items()},
            "me_synthesis_prefix": ME_SYNTHESIS_PREFIX}
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("data.json written: 3 axes x 20 signs")


if __name__ == "__main__":
    main()
