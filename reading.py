"""Pure logic of the v2 skull reading: d20 per axis -> sign, UI polarity roll -> phrases."""
import json
import random
from pathlib import Path

DATA = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
AXES = DATA["axes"]


def parse_roll(text: str) -> int:
    """Validate a /roll 1-20 result typed by the user."""
    try:
        value = int(str(text).strip())
    except ValueError:
        raise ValueError("Jet : entrez un nombre entre 1 et 20.") from None
    if not 1 <= value <= 20:
        raise ValueError("Jet : le jet doit être entre 1 et 20.")
    return value


def get_sign(axis_index: int, roll: int) -> dict:
    return AXES[axis_index]["signs"][roll - 1]


def roll_polarity(rng: random.Random | None = None) -> tuple[int, bool]:
    """The UI roll: 1-20, even = favorable, odd = unfavorable."""
    value = (rng or random).randint(1, 20)
    return value, value % 2 == 0


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def sign_preview(axis_index: int, roll: int) -> dict:
    """What is known before the polarity roll: the observed sign only."""
    sign = get_sign(axis_index, roll)
    return {"axis": AXES[axis_index]["label"], "sign": sign, "roll": roll}


def read_axis(axis_index: int, roll: int, favorable: bool, polarity_value: int | None = None) -> dict:
    axis = AXES[axis_index]
    sign = get_sign(axis_index, roll)
    meaning = _lower_first(sign["fav"] if favorable else sign["unf"])
    polarity = "favorable" if favorable else "défavorable"
    phrase = f"{axis['spoken']}, je vois {sign['sign_art']} : signe {polarity}, {meaning}."
    me_phrase = f"{axis['me']} {sign['sign_art']} : signe {polarity}, {meaning}."
    return {"axis": axis["label"], "index": axis_index, "roll": roll, "sign": sign, "favorable": favorable,
            "polarity_value": polarity_value,
            "meaning": sign["fav"] if favorable else sign["unf"],
            "phrase": phrase, "me_phrase": me_phrase}


def detail_line(r: dict) -> str:
    """One axis of the conclusion: 'Lignes : ligne brisée, favorable (polarité 14, pair), une rupture salutaire.'"""
    polarity = "favorable" if r["favorable"] else "défavorable"
    if r["polarity_value"] is not None:
        polarity += f" (polarité {r['polarity_value']}, {'pair' if r['polarity_value'] % 2 == 0 else 'impair'})"
    return f"{r['axis']} : {_lower_first(r['sign']['sign'])}, {polarity}, {_lower_first(r['meaning'])}."


def tone(readings: list[dict]) -> str:
    return DATA["synthesis"][str(sum(1 for r in readings if r["favorable"]))]


def synthesize(readings: list[dict]) -> str:
    """Tone sentence + the detail of every axis (sign, polarity, definition), on a single line (to copy)."""
    return " ".join([tone(readings)] + [detail_line(r) for r in readings])


def display_lines(readings: list[dict]) -> list[tuple[str, bool]]:
    """Screen lines of the conclusion, without the polarity wording (the colour says it): (text, favorable)."""
    return [(f"{r['axis']} : {_lower_first(r['sign']['sign'])}, {_lower_first(r['meaning'])}.", r["favorable"])
            for r in readings]


def synthesize_me(spoken: str) -> str:
    """Third-person version for /me (the game prepends "l'individu")."""
    return DATA["me_synthesis_prefix"] + _lower_first(spoken)


if __name__ == "__main__":
    # Fairness of the polarity roll and sample phrases.
    from collections import Counter
    counts = Counter(roll_polarity(random.Random(i))[1] for i in range(2000))
    print("favorable share:", round(counts[True] / 2000, 2))
    for axis in range(3):
        print(read_axis(axis, 5 + axis * 6, axis != 1)["phrase"])
        print("l'individu", read_axis(axis, 5 + axis * 6, axis != 1)["me_phrase"])
