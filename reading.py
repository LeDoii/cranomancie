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


def read_axis(axis_index: int, roll: int, favorable: bool) -> dict:
    axis = AXES[axis_index]
    sign = get_sign(axis_index, roll)
    meaning = _lower_first(sign["fav"] if favorable else sign["unf"])
    polarity = "favorable" if favorable else "défavorable"
    phrase = f"{axis['spoken']}, je vois {sign['sign_art']} : signe {polarity}, {meaning}."
    me_phrase = f"{axis['me']} {sign['sign_art']} : signe {polarity}, {meaning}."
    return {"axis": axis["label"], "index": axis_index, "roll": roll, "sign": sign, "favorable": favorable,
            "meaning": sign["fav"] if favorable else sign["unf"],
            "phrase": phrase, "me_phrase": me_phrase}


def _join(names: list[str]) -> str:
    """'les Lignes', 'les Lignes et la Forme', 'les Lignes, les Imperfections et la Forme'."""
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " et " + names[-1]


def synthesize(readings: list[dict]) -> str:
    """Tone sentence + the detail of which axes came out favorable / unfavorable."""
    good = [AXES[r["index"]]["with_article"] for r in readings if r["favorable"]]
    bad = [AXES[r["index"]]["with_article"] for r in readings if not r["favorable"]]
    text = DATA["synthesis"][str(len(good))]
    if good:
        text += f" {'Axe favorable' if len(good) == 1 else 'Axes favorables'} : {_join(good)}."
    if bad:
        text += f" {'Axe défavorable' if len(bad) == 1 else 'Axes défavorables'} : {_join(bad)}."
    return text


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
