"""Dessine un carrousel Instagram (JPEG 1080 x 1350) aux couleurs de La Rochelle Travail.

    python outils/generer.py posts/2026-11-24/post.json

Le fichier JSON décrit les images ; elles sont écrites à côté de lui (01.jpg, 02.jpg…).
Dans les titres, *mot* passe le mot en italique de couleur accent.

Types d'images :
  couverture  sur, titre, texte
  liste       sur, titre, elements [{jour, num, titre, detail}]  (jour vide = puce numérotée)
  texte       sur, titre, paragraphes [..], encadre {titre, texte}
  fin         sur, titre, texte, appel
Chaque image peut préciser "classe" : papier, marine, rouille ou nuit.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
L, H = 1080, 1350
MARGE = 84
HAUT_CORPS, BAS_CORPS = 190, H - 180

COULEURS = {
    "papier": dict(fond="#f6f1e7", txt="#0f2230", acc="#b5482b", doux="#5f6d74", logo="sombre"),
    "marine": dict(fond="#12384f", txt="#f6f1e7", acc="#f08a63", doux="#b9cdd6", logo="clair"),
    "rouille": dict(fond="#b5482b", txt="#fff8ef", acc="#ffd27a", doux="#f6d8c8", logo="clair"),
    "nuit": dict(fond="#0c1a23", txt="#f1ece2", acc="#ee8a66", doux="#8fa0a6", logo="clair"),
    # Couleur des fêtes : fond vert sapin, accent doré.
    "sapin": dict(fond="#1d4434", txt="#f6f1e7", acc="#e3a83b", doux="#b8cfc4", logo="clair"),
}
POLICES = {
    "titre": RACINE / "polices/fraunces-latin-wght-normal.ttf",
    "titre-i": RACINE / "polices/fraunces-latin-wght-italic.ttf",
    "texte": RACINE / "polices/figtree-latin-wght-normal.ttf",
}
_cache = {}


def police(nom, taille, graisse):
    cle = (nom, int(taille), graisse)
    if cle not in _cache:
        f = ImageFont.truetype(str(POLICES[nom]), int(taille))
        f.set_variation_by_axes([graisse])
        _cache[cle] = f
    return _cache[cle]


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def melange(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(rgb(a), rgb(b)))


def mots(texte):
    """« Un *mot*. » -> [[(« Un », False)], [(« mot », True), (« . », False)]] : chaque mot est une suite de
    segments, pour qu'une ponctuation reste collée au mot en italique qui la précède."""
    resultat, mot, accent = [], [], False
    segment = ""
    for car in texte + " ":
        if car == "*":
            if segment: mot.append((segment, accent))
            segment, accent = "", not accent
        elif car.isspace():
            if segment: mot.append((segment, accent))
            if mot: resultat.append(mot)
            segment, mot = "", []
        else:
            segment += car
    return resultat


def largeur_mot(mot, f_normal, f_accent):
    return sum((f_accent if a else f_normal).getlength(s) for s, a in mot)


def lignes(texte, f_normal, f_accent, largeur):
    """Découpe en lignes de mots tenant dans la largeur."""
    espace = f_normal.getlength(" ")
    resultat, courante, l_courante = [], [], 0.0
    for mot in mots(texte):
        w = largeur_mot(mot, f_normal, f_accent)
        ajout = w if not courante else l_courante + espace + w
        if courante and ajout > largeur:
            resultat.append(courante)
            courante, l_courante = [mot], w
        else:
            courante.append(mot)
            l_courante = ajout
    if courante:
        resultat.append(courante)
    return resultat


class Toile:
    """Mesure (dessin=None) ou dessine un bloc de texte, et renvoie la hauteur occupée."""

    def __init__(self, dessin, c):
        self.d, self.c = dessin, c

    def paragraphe(self, x, y, largeur, texte, f, f_acc, couleur, interligne=1.3, couleur_acc=None):
        h_ligne = f.size * interligne
        for ligne in lignes(texte, f, f_acc, largeur):
            cx = x
            for mot in ligne:
                for segment, accent in mot:
                    fo = f_acc if accent else f
                    if self.d:
                        self.d.text((cx, y), segment, font=fo, fill=(couleur_acc or couleur) if accent else couleur)
                    cx += fo.getlength(segment)
                cx += f.getlength(" ")
            y += h_ligne
        return y


def corps(t, s, c, e, y0):
    """Contenu d'une image, à l'échelle e. Renvoie le y final."""
    x, larg = MARGE, L - 2 * MARGE
    y = y0
    typ = s.get("type", "texte")
    if s.get("sur"):
        f = police("texte", 27 * e, 800)
        if t.d:
            t.d.text((x, y), s["sur"].upper(), font=f, fill=c["acc"])
        y += 27 * e * 1.9
    taille = {"couverture": 112, "fin": 98}.get(typ, 82) * e
    y = t.paragraphe(x, y, larg, s.get("titre", ""), police("titre", taille, 700), police("titre-i", taille, 500),
                     c["txt"], 1.04, c["acc"])
    f_txt = police("texte", 38 * e, 450)

    if typ in ("couverture", "fin", "texte") and s.get("texte"):
        y = t.paragraphe(x, y + 26 * e, larg, s["texte"], f_txt, police("texte", 38 * e, 700), c["txt"], 1.32, c["acc"])
    for p in s.get("paragraphes", []):
        y = t.paragraphe(x, y + 22 * e, larg, p, f_txt, police("texte", 38 * e, 700), c["txt"], 1.32, c["acc"])

    if typ == "liste":
        y += 26 * e
        cote = 112 * e
        for el in s.get("elements", []):
            haut = y + 18 * e
            xt = x + cote + 28 * e
            yt = t.paragraphe(xt, haut, larg - cote - 28 * e, el.get("titre", ""), police("titre", 36 * e, 650),
                              police("titre-i", 36 * e, 500), c["txt"], 1.12, c["acc"])
            if el.get("detail"):
                yt = t.paragraphe(xt, yt + 4 * e, larg - cote - 28 * e, el["detail"], police("texte", 27 * e, 450),
                                  police("texte", 27 * e, 700), c["doux"], 1.28)
            bas = max(yt, haut + cote) + 18 * e
            if t.d:
                cy = (haut + max(yt, haut + cote)) / 2 - cote / 2
                t.d.rounded_rectangle((x, cy, x + cote, cy + cote), radius=22 * e, fill=c["acc"])
                if el.get("jour"):
                    fj, fn = police("texte", 20 * e, 800), police("titre", 50 * e, 700)
                    t.d.text((x + cote / 2, cy + cote * .3), el["jour"].upper(), font=fj, fill=c["fond"], anchor="mm")
                    t.d.text((x + cote / 2, cy + cote * .64), str(el.get("num", "")), font=fn, fill=c["fond"], anchor="mm")
                else:
                    t.d.text((x + cote / 2, cy + cote / 2), str(el.get("num", "")), font=police("titre", 46 * e, 700),
                             fill=c["fond"], anchor="mm")
                t.d.line((x, bas, x + larg, bas), fill=melange(c["fond"], c["txt"], .16), width=2)
            y = bas

    if s.get("encadre"):
        enc = s["encadre"]
        haut = y + 34 * e

        def contenu(toile):
            yi = haut + 26 * e
            if enc.get("titre"):
                yi = toile.paragraphe(x + 40 * e, yi, larg - 70 * e, enc["titre"], police("titre-i", 36 * e, 650),
                                      police("titre-i", 36 * e, 650), c["acc"], 1.2)
            yi = toile.paragraphe(x + 40 * e, yi + 4 * e, larg - 70 * e, enc.get("texte", ""), police("texte", 34 * e, 450),
                                  police("texte", 34 * e, 700), c["txt"], 1.32, c["acc"])
            return yi + 22 * e

        # Mesure d'abord, pour poser le fond de l'encadré avant d'écrire dessus.
        y = contenu(Toile(None, c))
        if t.d:
            t.d.rectangle((x, haut, x + larg, y), fill=melange(c["fond"], c["txt"], .07))
            t.d.rectangle((x, haut, x + 8, y), fill=c["acc"])
            contenu(t)

    if typ == "fin" and s.get("appel"):
        y = t.paragraphe(x, y + 34 * e, larg, s["appel"], police("texte", 36 * e, 700), police("texte", 36 * e, 800),
                         c["acc"], 1.3)
    return y


def dessiner(s, n, total, sortie, saison=None):
    c = COULEURS.get(s.get("classe", "papier"), COULEURS["papier"])
    img = Image.new("RGB", (L, H), rgb(c["fond"]))
    d = ImageDraw.Draw(img)

    # En-tête : logo, nom du site, pagination.
    variante = f"noel-{c['logo']}" if saison == "noel" else c["logo"]
    logo = Image.open(RACINE / f"images/logo-{variante}.png").convert("RGBA").resize((58, 58), Image.LANCZOS)
    img.paste(logo, (MARGE, 66), logo)
    d.text((MARGE + 74, 95), "La Rochelle", font=police("titre", 31, 500), fill=c["txt"], anchor="lm")
    w = police("titre", 31, 500).getlength("La Rochelle ")
    d.text((MARGE + 74 + w, 95), "Travail", font=police("titre-i", 31, 750), fill=c["acc"], anchor="lm")
    d.text((L - MARGE, 95), f"{n:02d} / {total:02d}", font=police("texte", 26, 700), fill=c["doux"], anchor="rm")

    # Corps : on réduit l'échelle jusqu'à ce que tout tienne, puis on centre verticalement si c'est une couverture.
    e = 1.0
    while e > .55 and corps(Toile(None, c), s, c, e, HAUT_CORPS) > BAS_CORPS:
        e -= .04
    hauteur = corps(Toile(None, c), s, c, e, 0)
    if hauteur > BAS_CORPS - HAUT_CORPS:
        raise SystemExit(f"Image {n} : texte trop long même réduit. Raccourcis-le.")
    y0 = BAS_CORPS - hauteur if s.get("type") in ("couverture", "fin") else HAUT_CORPS
    corps(Toile(d, c), s, c, e, y0)

    # Pied : compte, et invitation à glisser ou adresse du site sur la dernière image.
    d.line((MARGE, H - 128, L - MARGE, H - 128), fill=melange(c["fond"], c["txt"], .18), width=2)
    d.text((MARGE, H - 84), "@larochelletravail", font=police("texte", 26, 700), fill=c["doux"], anchor="lm")
    if n == total:
        d.text((L - MARGE, H - 84), "la-rochelle-travail.fr", font=police("texte", 30, 800), fill=c["acc"], anchor="rm")
    else:
        # La police du site n'a pas de flèche : elle est dessinée.
        fin = L - MARGE
        d.line((fin - 34, H - 84, fin, H - 84), fill=c["acc"], width=4)
        d.line((fin - 13, H - 96, fin, H - 84), fill=c["acc"], width=4)
        d.line((fin - 13, H - 72, fin, H - 84), fill=c["acc"], width=4)
        d.text((fin - 48, H - 84), "Glissez", font=police("texte", 30, 800), fill=c["acc"], anchor="rm")
    if s.get("type") == "couverture":
        for i in range(0, L, 160):
            d.rectangle((i, H - 16, i + 80, H), fill=rgb("#b5482b"))
            d.rectangle((i + 80, H - 16, i + 160, H), fill=rgb("#d9a23a"))
    if saison == "noel" and s.get("type") in ("couverture", "fin"):
        # L'illustration occupe le haut, vide sur ces images : du dessous de la guirlande jusqu'au texte.
        img = hiver(img, c, n, illustration="sapin" if s["type"] == "couverture" else "cadeaux", espace=(200, y0 - 40))

    img.save(sortie, "JPEG", quality=90, optimize=True, progressive=True)


def flocon(d, x, y, r, couleur):
    """Flocon à six branches, chaque branche avec deux petites ramures."""
    import math
    for k in range(6):
        a = k * math.pi / 3
        bx, by = x + r * math.cos(a), y + r * math.sin(a)
        d.line((x, y, bx, by), fill=couleur, width=2)
        for t, sens in ((.55, 1), (.55, -1)):
            mx, my = x + r * t * math.cos(a), y + r * t * math.sin(a)
            b = a + sens * math.pi / 4
            d.line((mx, my, mx + r * .3 * math.cos(b), my + r * .3 * math.sin(b)), fill=couleur, width=2)


def dessiner_sapin(d, cx, haut, bas):
    h = bas - haut
    w = h * .7
    d.rectangle((cx - h * .06, bas - h * .12, cx + h * .06, bas), fill=rgb("#7a4b2a"))
    etages = [(.05, .42, .5, "#2f7a55"), (.24, .66, .72, "#3f8a64"), (.44, .9, 1, "#2f7a55")]
    for sommet, base, largeur, couleur in reversed(etages):
        d.polygon([(cx, haut + h * sommet), (cx - w / 2 * largeur, haut + h * base), (cx + w / 2 * largeur, haut + h * base)], fill=rgb(couleur))
    boules = [(-.12, .36, "#e0613f"), (.1, .32, "#6cc0dc"), (-.2, .6, "#6cc0dc"), (.16, .56, "#e3a83b"), (0, .48, "#f6f1e7"),
              (-.28, .84, "#e3a83b"), (.06, .8, "#e0613f"), (.3, .82, "#f6f1e7")]
    for dx, dy, couleur in boules:
        x, y, r = cx + dx * w, haut + dy * h, h * .028
        d.ellipse((x - r, y - r, x + r, y + r), fill=rgb(couleur))
    import math
    R, rr, cy = h * .075, h * .03, haut + h * .05
    d.polygon([(cx + (R if i % 2 == 0 else rr) * math.cos(-math.pi / 2 + i * math.pi / 5),
                cy + (R if i % 2 == 0 else rr) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)], fill=rgb("#e3a83b"))


def dessiner_cadeaux(d, cx, bas, taille):
    for dx, l, h, boite, ruban in ((-1.05, 1, .8, "#e0613f", "#f6f1e7"), (.05, 1.25, 1.05, "#3f8a64", "#e3a83b"), (1.1, .85, .65, "#e3a83b", "#e0613f")):
        x0, x1 = cx + dx * taille - l * taille / 2, cx + dx * taille + l * taille / 2
        y0 = bas - h * taille
        d.rectangle((x0, y0, x1, bas), fill=rgb(boite))
        d.rectangle((x0 - 6, y0 - 14, x1 + 6, y0 + 8), fill=rgb(boite))
        m = (x0 + x1) / 2
        d.rectangle((m - 7, y0 - 14, m + 7, bas), fill=rgb(ruban))
        d.ellipse((m - 30, y0 - 38, m - 2, y0 - 12), outline=rgb(ruban), width=7)
        d.ellipse((m + 2, y0 - 38, m + 30, y0 - 12), outline=rgb(ruban), width=7)


def hiver(img, c, graine, y0=140, neige_zones=None, illustration=None, espace=None):
    """Décor de décembre : guirlande à la hauteur y0, flocons dans les bandes vides, et sur la couverture un
    sapin (sur la dernière image, des cadeaux) dans l'espace libre au-dessus du texte."""
    import random
    hasard = random.Random(graine)
    calque = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    neige = (255, 255, 255) if c["logo"] == "clair" else rgb("#9fbccc")
    if neige_zones is None:
        neige_zones = ((170, espace[1]),) if espace else ((150, H * .45),)
    for haut, bas in neige_zones:
        for _ in range(int(60 * max(0, bas - haut) / 460)):
            x, y = hasard.uniform(0, L), hasard.uniform(haut, bas)
            if hasard.random() < .3:
                flocon(d, x, y, hasard.uniform(8, 15), neige + (hasard.randint(120, 210),))
            else:
                r = hasard.uniform(2.5, 6)
                d.ellipse((x - r, y - r, x + r, y + r), fill=neige + (hasard.randint(90, 190),))
    if espace and espace[1] - espace[0] >= 220:
        haut, bas = espace[0], espace[1]
        taille = min(bas - haut, 420)
        if illustration == "sapin":
            dessiner_sapin(d, L - MARGE - taille * .36, bas - taille, bas)
        elif illustration == "cadeaux":
            dessiner_cadeaux(d, L - MARGE - taille * .55, bas, min(taille * .38, 120))
    # Guirlande : un fil en arcs, une ampoule au creux de chaque arc.
    couleurs = ["#e0613f", "#e3a83b", "#6cc0dc", "#74c79b", "#f6f1e7"]
    pas = 120
    fil = neige + (150,)
    for i in range(0, L // pas + 1):
        x = i * pas
        points = [(x + pas * t / 20, y0 + 26 * 4 * (t / 20) * (1 - t / 20)) for t in range(21)]
        d.line(points, fill=fil, width=2)
        cx, cy = x + pas / 2, y0 + 26
        d.rectangle((cx - 4, cy, cx + 4, cy + 7), fill=rgb("#5f6d74") + (255,))
        d.ellipse((cx - 8, cy + 6, cx + 8, cy + 28), fill=rgb(couleurs[i % len(couleurs)]) + (255,))
    return Image.alpha_composite(img.convert("RGBA"), calque).convert("RGB")


def story(spec_chemin, couverture, saison):
    """Story verticale (1080 x 1920) qui annonce le post : la couverture du carrousel, encadrée."""
    premiere = json.loads(spec_chemin.read_text(encoding="utf-8"))["images"][0]
    # Fond contrasté avec la couverture, pour que la vignette se détache.
    c = COULEURS["papier"] if premiere.get("classe", "marine") in ("marine", "nuit", "rouille", "sapin") else COULEURS["marine"]
    img = Image.new("RGB", (L, 1920), rgb(c["fond"]))
    d = ImageDraw.Draw(img)
    d.text((L / 2, 190), "Nouveau post", font=police("titre-i", 78, 650), fill=c["acc"], anchor="mm")
    d.text((L / 2, 270), "sur @larochelletravail", font=police("texte", 36, 700), fill=c["txt"], anchor="mm")
    vignette = Image.open(couverture).resize((864, 1080), Image.LANCZOS)
    masque = Image.new("L", vignette.size, 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, *vignette.size), radius=36, fill=255)
    ombre = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rounded_rectangle((108 + 18, 360 + 22, 108 + 864 + 18, 360 + 1080 + 22), radius=36, fill=(0, 0, 0, 70))
    img = Image.alpha_composite(img.convert("RGBA"), ombre).convert("RGB")
    img.paste(vignette, (108, 360), masque)
    d = ImageDraw.Draw(img)
    d.text((L / 2, 1560), "Tout est gratuit et sans compte", font=police("texte", 38, 700), fill=c["txt"], anchor="mm")
    d.text((L / 2, 1630), "la-rochelle-travail.fr", font=police("titre", 52, 700), fill=c["acc"], anchor="mm")
    if saison == "noel":
        # La couverture a déjà sa guirlande : ici, une seule en haut, et la neige autour du texte, jamais dessus.
        img = hiver(img, c, 99, y0=24, neige_zones=((96, 140), (310, 350), (1690, 1900)))
    sortie = spec_chemin.parent / "story.jpg"
    img.save(sortie, "JPEG", quality=90, optimize=True, progressive=True)
    return sortie


def main():
    spec_chemin = Path(sys.argv[1])
    spec = json.loads(spec_chemin.read_text(encoding="utf-8"))
    images = spec["images"]
    if not 2 <= len(images) <= 10:
        raise SystemExit("Un carrousel compte de 2 à 10 images.")
    saison = spec.get("saison")
    for n, s in enumerate(images, 1):
        sortie = spec_chemin.parent / f"{n:02d}.jpg"
        dessiner(s, n, len(images), sortie, saison)
        taille = sortie.stat().st_size
        if taille > 8 * 1024 * 1024:
            raise SystemExit(f"{sortie.name} dépasse 8 Mo.")
        print(f"{sortie} ({taille // 1024} Ko)")
    print(f"{story(spec_chemin, spec_chemin.parent / '01.jpg', saison)} (story)")


if __name__ == "__main__":
    main()
