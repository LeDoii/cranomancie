"""Pure logic of the skull reading: roll -> arcane, orientation, phrases."""
import json
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
ARCANES = DATA["arcanes"]
AXES = DATA["axes"]

MODE_A = "A"  # one roll per axis, /roll 1-44
MODE_B = "B"  # two rolls per axis, /roll 1-20 then /roll 1-6 (+ confirmation)


def _to_int(text: str, lo: int, hi: int, what: str) -> int:
    try:
        value = int(str(text).strip())
    except ValueError:
        raise ValueError(f"{what} : entrez un nombre entre {lo} et {hi}.") from None
    if not lo <= value <= hi:
        raise ValueError(f"{what} : le jet doit être entre {lo} et {hi}.")
    return value


def needs_confirmation(card_roll: str) -> bool:
    """Mode B: rolls 1 and 20 may open the borders of the tarot (Mat, Monde)."""
    try:
        return int(str(card_roll).strip()) in (1, 20)
    except ValueError:
        return False


def resolve_a(roll: str) -> tuple[int, bool]:
    """Mode A: 1-22 upright cards 0-21, 23-44 the same cards reversed."""
    value = _to_int(roll, 1, 44, "Jet")
    return (value - 1) % 22, value > 22


def resolve_b(card_roll: str, sense_roll: str, confirm_roll: str = "") -> tuple[int, bool]:
    """Mode B: d20 gives arcanes I-XX, d6 gives the sense (4-6 reversed).

    On a 1 or a 20 a confirmation d6 of 5-6 turns I into Le Mat (0)
    and XX into Le Monde (XXI): the two borders are rarer on purpose.
    """
    card = _to_int(card_roll, 1, 20, "Carte")
    sense = _to_int(sense_roll, 1, 6, "Sens")
    index = card
    if card in (1, 20):
        confirm = _to_int(confirm_roll, 1, 6, "Confirmation")
        if confirm >= 5:
            index = 0 if card == 1 else 21
    return index, sense >= 4


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def article_forms(name: str) -> tuple[str, str]:
    """Mid-sentence forms of an arcane name: ('le Pendu', 'du Pendu'), ('la Lune', 'de la Lune')..."""
    if name.startswith("Le "):
        return "le " + name[3:], "du " + name[3:]
    if name.startswith("La "):
        return "la " + name[3:], "de la " + name[3:]
    if name.startswith("L'"):
        return "l'" + name[2:], "de l'" + name[2:]
    return name, "de " + name


def read_axis(axis_index: int, arcane_index: int, reversed_: bool) -> dict:
    axis = AXES[axis_index]
    arcane = ARCANES[arcane_index]
    sense = arcane["rev"] if reversed_ else arcane["up"]
    template = axis["rev"] if reversed_ else axis["up"]
    with_article, de_form = article_forms(arcane["name"])
    phrase = template.format(
        arcane_l=with_article,
        de_arcane=de_form,
        sens=_lower_first(sense),
        renverse="renversée" if arcane["fem"] else "renversé",
    )
    return {
        "axis": axis["label"],
        "arcane": arcane,
        "reversed": reversed_,
        "sense": sense,
        "phrase": phrase,
    }


def synthesize(readings: list[dict]) -> str:
    """Closing sentence from the number of reversed cards (+ repeated arcane)."""
    reversed_count = sum(1 for r in readings if r["reversed"])
    text = DATA["synthesis"][str(reversed_count)]
    numbers = [r["arcane"]["n"] for r in readings]
    if len(set(numbers)) < len(numbers):
        text += " " + DATA["synthesis_repeat"]
    return text


if __name__ == "__main__":
    # Quick fairness check of both modes.
    from collections import Counter
    a = Counter(resolve_a(str(v)) for v in range(1, 45))
    assert len(a) == 44 and set(a.values()) == {1}
    b = Counter()
    for card in range(1, 21):
        for sense in range(1, 7):
            for confirm in range(1, 7):
                b[resolve_b(str(card), str(sense), str(confirm))] += 1
    assert {i for i, _ in b} == set(range(22))
    print("mode A uniform over 44 outcomes; mode B reaches all 22 arcanes")
    print("example:", read_axis(0, 0, False)["phrase"])
