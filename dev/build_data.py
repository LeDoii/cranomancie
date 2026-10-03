"""Build data.json for the skull divination GUI.

Arcane meanings are parsed from ARCANES_v1.md (single source of truth);
axes, phrase templates and the synthesis table come from FILTRES_v2.md
and are declared here. Everything is invented content (see README.md).
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent

META = {
    "title": "Cranomancie",  # name chosen by the user
    "subtitle": "La lecture du crâne chauve selon Oswald Bald",
    "author": "Oswald Bald",
}

AXES = [
    {
        "id": "lignes",
        "label": "Lignes",
        "nom": "Le Chemin",
        "observe": "Sutures, plis et sillons du cuir chevelu",
        "question": "D'où vient la personne, où va sa route ?",
        "temps": "Passé et destin",
        "anchor": "Lignes de Ley (livre des créatures magiques, Goblin des montagnes)",
        "up": "Suivez cette ligne : elle porte {arcane_l}. Votre chemin est marqué par : {sens}.",
        "rev": "La ligne se brise ici, sous {arcane_l} {renverse}. Votre route a été troublée par : {sens}.",
    },
    {
        "id": "bosses",
        "label": "Bosses",
        "nom": "Les Dons",
        "observe": "Reliefs et protubérances du crâne, zone par zone",
        "question": "De quoi est-elle capable, qu'est-ce qui l'attire ?",
        "temps": "Présent",
        "anchor": "Les quatre maisons fondées par les Wendelhart : Azuralys, Felora, Ferrox, Oragonn (Guide de Rivenguard, p. 3) : un don propre à chaque maison",
        "up": "Cette bosse trahit {arcane_l} : vous avez un don pour : {sens}.",
        "rev": "Cette bosse est trompeuse, sous {arcane_l} {renverse} : votre don risque de virer à : {sens}.",
    },
    {
        "id": "forme",
        "label": "Forme",
        "nom": "La Nature",
        "observe": "Contour général, proportions, symétrie",
        "question": "Qui est-elle au fond, vers quoi tend-elle ?",
        "temps": "Fond durable et avenir",
        "anchor": "",  # removed on request: the houses anchor the Bosses axis
        "up": "La forme de ce crâne parle {de_arcane} : vous êtes de ceux qui montrent : {sens}.",
        "rev": "Sous {arcane_l} {renverse}, cette forme révèle : {sens}. Méfiez-vous de ce penchant.",
    },
]

# /me variants: the game prints "l'individu <text>", so these are third-person actions without the subject.
ME_TEMPLATES = {
    "lignes": (
        "suit une ligne du crâne du doigt : elle porte {arcane_l}, un chemin marqué par : {sens}.",
        "suit une ligne du crâne du doigt : elle se brise sous {arcane_l} {renverse}, la route a été troublée par : {sens}.",
    ),
    "bosses": (
        "palpe une bosse du crâne : elle trahit {arcane_l}, un don pour : {sens}.",
        "palpe une bosse du crâne : elle est trompeuse, sous {arcane_l} {renverse}, le don risque de virer à : {sens}.",
    ),
    "forme": (
        "observe la forme du crâne : elle parle {de_arcane}, un caractère qui montre : {sens}.",
        "observe la forme du crâne : sous {arcane_l} {renverse}, elle révèle : {sens}, un penchant à surveiller.",
    ),
}
for _axis in AXES:
    _axis["me_up"], _axis["me_rev"] = ME_TEMPLATES[_axis["id"]]

ME_SYNTHESIS_PREFIX = "conclut sa lecture : "

FEMININE = {"L'Impératrice", "L'Étoile", "Tempérance"}

SYNTHESIS = {
    0: "Les trois signes s'accordent : le présage est favorable.",
    1: "Un seul signe est renversé : le présage est nuancé, avec un point de vigilance sur l'axe de la carte renversée.",
    2: "Deux signes sont renversés : les signes se contrarient, tout dépend de vos choix.",
    3: "Les trois signes sont renversés : le crâne parle avec gravité.",
}
SYNTHESIS_REPEAT = "Le signe se répète, il pèse deux fois."


def parse_arcanes(path: Path) -> list[dict]:
    """Parse the 22-row markdown table of ARCANES_v1.md."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*(0|[IVX]+)\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        numeral, name, up, rev, anchor = cells
        rows.append({
            "n": len(rows),
            "numeral": numeral,
            "name": name,
            "fem": name.startswith("La ") or name in FEMININE,
            "up": up,
            "rev": rev,
            "anchor": anchor,
        })
    if len(rows) != 22:
        raise SystemExit(f"expected 22 arcanes, got {len(rows)}")
    return rows


def main() -> None:
    data = {
        "meta": META,
        "axes": AXES,
        "arcanes": parse_arcanes(HERE / "ARCANES_v1.md"),
        "synthesis": {str(k): v for k, v in SYNTHESIS.items()},
        "synthesis_repeat": SYNTHESIS_REPEAT,
        "me_synthesis_prefix": ME_SYNTHESIS_PREFIX,
    }
    (HERE / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("data.json written:", len(data["arcanes"]), "arcanes")


if __name__ == "__main__":
    main()
