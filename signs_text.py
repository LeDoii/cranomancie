"""Text helpers for sign names (shared by build_data.py and the application)."""

# Indefinite article by first word of a sign ("" = keep as is, "l'" = elided definite article).
ARTICLES = {
    "ligne": "une", "deux": "", "cicatrice": "une", "grain": "un", "bosse": "une", "creux": "un",
    "taches": "des", "veine": "une", "peau": "une", "petite": "une", "petit": "un", "grand": "un",
    "pli": "un", "coupure": "une", "tache": "une", "double": "une", "marque": "une",
    "trace": "une", "crâne": "un", "front": "un", "sommet": "un", "nuque": "une", "arrière": "l'",
    "tempes": "des", "arcades": "des", "contour": "un", "profil": "un",
}


def with_article(sign: str, strict: bool = True) -> str:
    """'Ligne brisée' -> 'une ligne brisée', 'Arrière du crâne plat' -> "l'arrière du crâne plat".

    Unknown first word: ValueError when strict, else the lowercased name without article (the user can
    then type the article by hand when editing a sign).
    """
    sign = sign.strip()
    lowered = sign[:1].lower() + sign[1:]
    first = sign.split()[0].lower() if sign else ""
    if first not in ARTICLES:
        if strict:
            raise ValueError(f"no article rule for sign: {sign}")
        return lowered
    article = ARTICLES[first]
    if article == "l'":
        return "l'" + lowered
    return f"{article} {lowered}" if article else lowered
