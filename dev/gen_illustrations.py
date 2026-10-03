"""Generate the Cranomancie card illustrations with ComfyUI (Outils/comfy.py).

Usage: python gen_illustrations.py [card numbers...]   (default: all missing cards)
Two house styles: "dark" (reference = Morzhul artwork) and "light" (book ink engraving).
Output: illustrations/src/NN_name_v1_sS.png, 3 seeds per card; the user validates one by one.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
COMFY = HERE.parents[2] / "Outils" / "comfy.py"
SRC = HERE / "illustrations" / "src"
SEEDS = ["1", "2", "3"]

STYLES = {
    "dark": ("illustrations/ref_dark.png",
             "Use the reference image only for its art style: dark gritty ink illustration, bold black linework, "
             "hand-engraved texture, muted brown and black palette with antique gold accents, dramatic lighting, "
             "swirling dark smoke. Create a NEW scene and do NOT copy the hooded figure, the scythe, the robe or any other subject of the reference image (no hooded reaper). Square composition, full scene filling the frame, "
             "no border. No text, no letters, no numbers, no runes, no symbols."),
    "light": ("illustrations/ref_light.png",
              "Use the reference image only for its art style: antique hand-engraved woodcut in the manner of old "
              "Tarot de Marseille, black ink outlines with hatching, flat muted colors (ochre, faded red, faded blue) "
              "on cream paper. Create a NEW scene and do NOT copy the vial or any other subject of the reference image. Square composition, full scene filling the frame, no border. "
              "No text, no letters, no numbers, no runes, no symbols."),
}

# number -> (file slug, style, subject)
CARDS = {
    0: ("mat", "light", "A lone traveller in a hooded cloak with a small bundle on a stick, seen from behind, walking toward a glowing arched stone portal in a ruined courtyard."),
    1: ("bateleur", "light", "Indoors in a dim wizard's study: a wooden table with a magic wand, a small iron cauldron and a stone mortar with pestle, a few dried herbs, a lit candle, a dark wooden wall and a shelf of books behind the table. No landscape, no hills, no outdoors. No person."),
    2: ("papesse", "light", "A heavy sealed door with iron bands and an enormous closed grimoire on a stone pedestal in front of it, dim mysterious library atmosphere. No person."),
    6: ("amoureux", "light", "A crossroads where four paths lead in four different directions between hills, a lone traveller seen from behind at the center, hesitating."),
    7: ("chariot", "light", "A weathered stone statue of a robed ancient figure standing in a village square with cobblestones, a medieval fantasy village gate behind it, daylight."),
    9: ("ermite", "dark", "A small timid green-skinned goblin with large yellow eyes and webbed feet holding a lantern in a deep cave, shy posture."),
    11: ("force", "dark", "A white-furred werewolf standing calm and powerful in a dark forest, jaws closed, one clawed hand lowered in restraint, tattered dark clothes."),
    12: ("pendu", "dark", "A floating island carrying an ornate gothic castle, seen from far below at a dramatic angle, roots and rocks hanging under it, stormy sky."),
    13: ("sans_nom", "dark", "An empty stone morgue with slabs covered by white sheets, a single burning candle, cold fog. No person."),
    14: ("temperance", "light", "Indoors in an alchemist's room with a stone wall behind: a hand pouring a glowing elixir from a glass vial into a bubbling cauldron, steam rising, herbs around. No landscape, no hills, no outdoors. The artwork fills the entire square canvas edge to edge with no paper margin."),
    15: ("diable", "dark", "A shiny gold coin lying on a hidden iron trap on dark ground, the glowing eyes of a small goblin watching greedily from the shadows."),
    16: ("maison_dieu", "dark", "A tall gothic academy tower splitting in two during an earthquake, stones falling, lightning, dust, tiny people fleeing."),
    17: ("etoile", "dark", "An enchanted brass compass glowing with blue light on a stone ledge under a vast starry night sky, a tiny village far below."),
    18: ("lune", "dark", "A dark forest at night under a pale full moon, twisted trees, a narrow path, mist, faint glowing eyes in the darkness."),
    19: ("soleil", "light", "A cheerful old confectionery shop front with a striped awning and shelves of colorful sweets in the window, bright sunshine, a plain wooden fascia with absolutely no signboard and no writing anywhere. No person."),
    21: ("monde", "light", "A grand neoclassical ministry building with tall columns at the center of a large oval laurel wreath, bright day."),
}


def main() -> None:
    wanted = [int(a) for a in sys.argv[1:]] or sorted(CARDS)
    SRC.mkdir(parents=True, exist_ok=True)
    for n in wanted:
        slug, style, subject = CARDS[n]
        ref, style_text = STYLES[style]
        version = {1: "v3", 14: "v4", 19: "v3"}.get(n, "v2" if style == "light" else "v1")  # light style regenerated with a square reference
        out = SRC / f"{n:02d}_{slug}_{version}.png"
        if all((SRC / f"{n:02d}_{slug}_{version}_s{s}.png").exists() for s in SEEDS):
            print("skip", n, slug, flush=True)
            continue
        prompt = f"{subject} {style_text}"
        cmd = [sys.executable, str(COMFY), "image", "--prompt", prompt, "--ref", str(HERE / ref),
               "--size", "1024x1024", "--seeds", *SEEDS, "--out", str(out)]
        print("generating", n, slug, style, flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout[-300:], result.stderr[-300:], flush=True)


if __name__ == "__main__":
    main()
