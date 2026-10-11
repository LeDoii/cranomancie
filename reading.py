"""Pure logic of the v2 skull reading: d20 per axis -> sign, UI polarity roll -> phrases."""
import copy
import json
import os
import random
import sys
from pathlib import Path

from signs_text import with_article

DATA = json.loads((Path(__file__).parent / "data.json").read_text(encoding="utf-8"))
AXES = DATA["axes"]
ORIGINAL = copy.deepcopy(AXES)  # the shipped definitions: the target of "Réinitialiser"
FIELDS = ("sign", "sign_art", "fav", "unf")
OVERRIDES: dict = {}  # {"lignes": {"5": {"fav": "mon texte"}}}: only the fields the user changed


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
    """One axis of the conclusion, for the chat: 'Lignes : ligne brisée, favorable, une rupture salutaire.'
    (the polarity roll itself is not repeated: the axis panel shows it)."""
    polarity = "favorable" if r["favorable"] else "défavorable"
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


def conclusion_items(readings: list[dict]) -> list[dict]:
    """The conclusion split in four lines (tone, then one per axis), each copiable on its own.

    display: text on screen (no polarity wording, the colour says it); favorable: None for the tone;
    spoken: chat text; me: /me text (the game prepends "l'individu").
    """
    tone_text = tone(readings)
    items = [{"display": tone_text, "favorable": None, "spoken": tone_text,
              "me": DATA["me_synthesis_prefix"] + _lower_first(tone_text)}]
    for r_, (display, favorable) in zip(readings, display_lines(readings)):
        items.append({"display": display, "favorable": favorable, "spoken": detail_line(r_),
                      "me": "précise : " + detail_line(r_)})
    return items


def synthesize_me(spoken: str) -> str:
    """Third-person version for /me (the game prepends "l'individu")."""
    return DATA["me_synthesis_prefix"] + _lower_first(spoken)


# --- user customisation --------------------------------------------------------------------
# Edits live in the user's data folder, outside the application folder, so that updates and fresh
# downloads never erase them. Only the changed fields are stored: unchanged fields keep following
# the shipped definitions when an update improves them.
def data_dir() -> Path:
    custom = os.environ.get("CRANOMANTIE_DATA_DIR")  # tests
    if custom:
        return Path(custom)
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "Cranomancie"
    return Path.home() / ".cranomancie"


def overrides_path() -> Path:
    return data_dir() / "custom_signs.json"


def _apply(axis_index: int, n: int) -> None:
    """Shipped definition + this sign's overrides, in place (the lists in AXES are shared by the whole app)."""
    sign = AXES[axis_index]["signs"][n - 1]
    sign.update({k: v for k, v in ORIGINAL[axis_index]["signs"][n - 1].items() if k in FIELDS})
    sign.update(OVERRIDES.get(AXES[axis_index]["id"], {}).get(str(n), {}))


def load_overrides() -> None:
    """Read the user's edits (a missing or unreadable file means no edits) and apply them."""
    OVERRIDES.clear()
    try:
        stored = json.loads(overrides_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stored = {}
    for axis_index, axis in enumerate(AXES):
        for n_text, fields in (stored.get(axis["id"], {}) if isinstance(stored, dict) else {}).items():
            if n_text.isdigit() and 1 <= int(n_text) <= 20 and isinstance(fields, dict):
                clean = {k: v for k, v in fields.items() if k in FIELDS and isinstance(v, str) and v.strip()}
                if clean:
                    OVERRIDES.setdefault(axis["id"], {})[n_text] = clean
                    _apply(axis_index, int(n_text))


def _write_overrides() -> None:
    path = overrides_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(OVERRIDES, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)  # atomic: an interrupted save never leaves a half-written file


def is_customized(axis_index: int, n: int) -> bool:
    return bool(OVERRIDES.get(AXES[axis_index]["id"], {}).get(str(n)))


def original_sign(axis_index: int, n: int) -> dict:
    return ORIGINAL[axis_index]["signs"][n - 1]


def save_sign(axis_index: int, n: int, sign: str, sign_art: str, fav: str, unf: str) -> None:
    """Store the user's version of a sign; fields equal to the shipped ones are not stored."""
    sign, sign_art, fav, unf = (value.strip() for value in (sign, sign_art, fav, unf))
    if not (sign and fav and unf):
        raise ValueError("Le nom et les deux définitions ne peuvent pas être vides.")
    sign_art = sign_art or with_article(sign, strict=False)
    original = original_sign(axis_index, n)
    changed = {key: value for key, value in
               (("sign", sign), ("sign_art", sign_art), ("fav", fav), ("unf", unf)) if value != original[key]}
    axis_id = AXES[axis_index]["id"]
    if changed:
        OVERRIDES.setdefault(axis_id, {})[str(n)] = changed
    else:
        OVERRIDES.get(axis_id, {}).pop(str(n), None)
    _apply(axis_index, n)
    _write_overrides()


def reset_sign(axis_index: int, n: int) -> None:
    """Back to the shipped definition of this sign."""
    OVERRIDES.get(AXES[axis_index]["id"], {}).pop(str(n), None)
    _apply(axis_index, n)
    _write_overrides()


load_overrides()

if __name__ == "__main__":
    # Fairness of the polarity roll and sample phrases.
    from collections import Counter
    counts = Counter(roll_polarity(random.Random(i))[1] for i in range(2000))
    print("favorable share:", round(counts[True] / 2000, 2))
    for axis in range(3):
        print(read_axis(axis, 5 + axis * 6, axis != 1)["phrase"])
        print("l'individu", read_axis(axis, 5 + axis * 6, axis != 1)["me_phrase"])
