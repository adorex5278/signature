#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normaliser_nominatives.py
-------------------------
Traite en lot les GIF nominatifs fournis par le marketing :
  - renomme en prenom.gif (minuscules, sans accent ni espace) ; une source FIXE
    (.jpg/.png) sort en prenom.jpg, JPEG 4:4:4 a la qualite max qui tient
    dans le budget (pas de palette GIF 256 couleurs, qui degrade)
  - force la LARGEUR 1108 (meme largeur que le bandeau evenement) ; la
    hauteur suit le ratio de la source, sans deformation
    (4:1 -> 1108x277, 600x250 -> 1108x462, etc.)
  - optimise (Canva sort du GIF non compresse : ~340 Ko -> ~150 Ko)
  - affiche en fin de run la hauteur a mettre dans le HTML de chaque
    signature (attribut height de la balise <img>), puisqu'elle peut varier
    d'un fichier a l'autre

Usage :
    python normaliser_nominatives.py dossier_source/ -o nominatives/
    python normaliser_nominatives.py input/ -o nominatives/ --max-ko 200
    python normaliser_nominatives.py input/ -o nominatives/ --strict
        (ancien mode : tout force en 1108x277, deforme si le ratio differe)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import unicodedata

# ============================================================
#  GABARIT — la largeur doit correspondre a width dans les signatures
# ============================================================
LARGEUR = 1108
HAUTEUR = 277            # hauteur de reference (ratio 4:1) : budget Ko et mode --strict
RATIO_MIN, RATIO_MAX = 1.5, 6.0   # largeur/hauteur plausible ; hors bornes = probable mauvais fichier
MAX_KO_DEFAUT = 200      # budget pour du 1108x277 ; proportionnel a la hauteur sinon
MAX_FRAMES = 30          # au-dela, on sous-echantillonne avant redimension
# ============================================================

# Mots de remplissage a retirer des noms de fichiers fournis
PARASITES = ("gif", "ok", "resize", "ezgif", "com", "final", "def", "v1", "v2")

# Artefacts d'encodage observes sur des exports (#U00e9 -> e accent aigu)
# Exactement 4 chiffres hexa (BMP standard) : evite d'avaler un 'e' ou 'f'
# de trop si le caractere suivant est lui-meme un chiffre hexadecimal valide.
_ENTITE_HEX = re.compile(r"#[Uu]\+?([0-9a-fA-F]{4})")


def reparer_entites(texte):
    """'Elys#U00e9e' -> 'Elysée' (artefact d'encodage repere sur les zips Canva)."""
    return _ENTITE_HEX.sub(lambda m: chr(int(m.group(1), 16)), texte)


def sans_accent(texte):
    texte = reparer_entites(texte)
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def prenom_depuis(nom_fichier):
    """'sEB NIETCHE GIF OK.gif' -> 'seb'   |   'Elysee Da Costa.gif' -> 'elysee'"""
    base = os.path.splitext(os.path.basename(nom_fichier))[0]
    base = sans_accent(base).lower()
    morceaux = re.split(r"[\s\-_.]+", base)
    utiles = [m for m in morceaux if m and m not in PARASITES and not m.isdigit()]
    if not utiles:
        return re.sub(r"[^a-z0-9]", "", base) or "sans_nom"
    return re.sub(r"[^a-z0-9]", "", utiles[0])


def dimensions(chemin):
    from PIL import Image
    im = Image.open(chemin)
    return im.size, getattr(im, "n_frames", 1)


def cible_pour(w, h, strict=False):
    """Dimensions finales : largeur fixe LARGEUR, hauteur proportionnelle au
    ratio de la source (ou 1108x277 force en mode strict)."""
    if strict:
        return LARGEUR, HAUTEUR
    return LARGEUR, max(1, round(LARGEUR * h / w))


def sous_echantillonner_si_besoin(source, tmp_path):
    """
    Si la source a beaucoup plus de frames que necessaire (ex: export ezgif
    a 150 images pour 5s), on n'en garde qu'une partie AVANT le redimensionnement.
    Sans ca, agrandir 150 frames coute une fortune en poids pour un gain de
    fluidite invisible sur une signature.
    Retourne le chemin a utiliser pour la suite (source ou tmp_path).
    """
    (w, h), n = dimensions(source)
    if n <= MAX_FRAMES:
        return source, False

    pas = max(1, round(n / MAX_FRAMES))
    indices = list(range(0, n, pas))
    selection = " ".join(f"#{i}" for i in indices)
    cmd = ["gifsicle", source] + selection.split() + ["-o", tmp_path]
    subprocess.run(cmd, capture_output=True)
    return (tmp_path if os.path.exists(tmp_path) else source), True


def traiter(source, destination, max_ko, strict=False):
    """Sous-echantillonne si besoin, redimensionne si besoin, puis compresse
    jusqu'a tenir dans le budget (max_ko pour du 1108x277, proportionnel a la
    hauteur finale sinon).
    Retourne (octets, couleurs, lossy, resize, allege, cible, plafond_octets)."""
    tmp_ech = destination + ".ech.gif"
    src_travail, allege = sous_echantillonner_si_besoin(source, tmp_ech)

    (w, h), _ = dimensions(src_travail)
    cible = cible_pour(w, h, strict)
    besoin_resize = (w, h) != cible
    max_octets = int(max_ko * 1024 * cible[1] / HAUTEUR)

    base = ["gifsicle", "--careful", "-O3"]
    if besoin_resize:
        base += [f"--resize={cible[0]}x{cible[1]}"]

    resultat = None
    for couleurs, lossy in ((255, 30), (255, 60), (192, 60), (128, 80), (96, 100), (64, 140)):
        cmd = base + [f"--colors={couleurs}", f"--lossy={lossy}", src_travail, "-o", destination]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(destination):
            resultat = (os.path.getsize(destination), couleurs, lossy, besoin_resize,
                        allege, cible, max_octets)
            if resultat[0] <= max_octets:
                break

    if os.path.exists(tmp_ech):
        os.remove(tmp_ech)

    if resultat is None:
        raise RuntimeError("gifsicle n'a rien produit")
    return resultat


def traiter_statique(source, destination, max_ko, strict=False):
    """Source fixe (JPEG / PNG) : PAS de passage par une palette GIF de 256
    couleurs (bandes, perte nette). On sort un JPEG 4:4:4 a la qualite la plus
    haute qui tient dans le budget.
    Meme tuple de retour que traiter() : (octets, qualite, 0, resize, False,
    cible, plafond_octets)."""
    from PIL import Image
    im = Image.open(source).convert("RGB")
    cible = cible_pour(im.width, im.height, strict)
    resize = im.size != cible
    if resize:
        im = im.resize(cible, Image.LANCZOS)
    plafond = int(max_ko * 1024 * cible[1] / HAUTEUR)

    for q in range(98, 59, -1):          # plus haute qualite qui rentre dans le budget
        im.save(destination, "JPEG", quality=q, subsampling=0, optimize=True)
        if os.path.getsize(destination) <= plafond:
            break
    return os.path.getsize(destination), q, 0, resize, False, cible, plafond


def main():
    p = argparse.ArgumentParser(description="Normalise les GIF nominatifs en lot")
    p.add_argument("source", help="dossier contenant les GIF fournis")
    p.add_argument("-o", "--out", default="nominatives", help="dossier de sortie")
    p.add_argument("--max-ko", type=int, default=MAX_KO_DEFAUT,
                   help="budget pour du 1108x277 (proportionnel a la hauteur sinon)")
    p.add_argument("--strict", action="store_true",
                   help="force TOUT en 1108x277 (deforme si le ratio source differe)")
    args = p.parse_args()

    if not os.path.isdir(args.source):
        sys.exit(f"Dossier introuvable : {args.source}")

    os.makedirs(args.out, exist_ok=True)
    fichiers = sorted(f for f in os.listdir(args.source)
                      if f.lower().endswith((".gif", ".jpg", ".jpeg", ".png")))
    if not fichiers:
        sys.exit(f"Aucun .gif / .jpg / .png dans {args.source}")

    if any(f.lower().endswith(".gif") for f in fichiers) and not shutil.which("gifsicle"):
        sys.exit("gifsicle introuvable (necessaire pour les GIF).\nWindows : choco install gifsicle")

    mode = "strict 1108x277" if args.strict else f"largeur {LARGEUR}, hauteur selon ratio"
    print(f"Gabarit {mode}  |  budget {args.max_ko} Ko (a 277 px)  |  {len(fichiers)} fichiers\n")
    print(f"{'source':<38} {'->':^4} {'sortie':<16} {'avant':>8} {'apres':>8}  note")
    print("-" * 100)

    vus, alertes, gain, hauteurs = {}, [], 0, {}

    for f in fichiers:
        src = os.path.join(args.source, f)
        prenom = prenom_depuis(f)

        (sw, sh), _ = dimensions(src)
        ratio = sw / sh
        if not args.strict and not (RATIO_MIN <= ratio <= RATIO_MAX):
            alertes.append(f"'{f}' : ratio {ratio:.2f}:1 ({sw}x{sh}) inhabituel pour une "
                           f"signature — probablement pas le bon fichier, ignore")
            continue

        if prenom in vus:
            suffixe = 2
            while f"{prenom}{suffixe}" in vus:
                suffixe += 1
            alertes.append(f"Doublon de prenom : '{f}' renomme en {prenom}{suffixe}.gif")
            prenom = f"{prenom}{suffixe}"
        vus[prenom] = f

        est_gif = f.lower().endswith(".gif")
        ext = ".gif" if est_gif else ".jpg"     # source fixe -> JPEG haute qualite
        dst = os.path.join(args.out, f"{prenom}{ext}")
        avant = os.path.getsize(src)
        try:
            traitement = traiter if est_gif else traiter_statique
            apres, coul, lossy, resize, allege, cible, plafond = traitement(
                src, dst, args.max_ko, args.strict)
        except Exception as e:
            alertes.append(f"ECHEC sur '{f}' : {e}")
            continue

        (w, h), n = dimensions(dst)
        hauteurs[prenom + ext] = h
        note = []
        if allege:
            note.append("frames reduites")
        if resize:
            note.append("redimensionne")
        if sw < LARGEUR:
            alertes.append(f"'{prenom}{ext}' : source en {sw} px de large, agrandie a {LARGEUR} — "
                           f"risque de flou, redemander un export natif plus grand si possible")
        if apres > plafond:
            note.append(f"depasse {plafond // 1024} Ko")
            alertes.append(f"'{prenom}{ext}' fait {apres/1024:.0f} Ko malgre compression max "
                           f"(budget {plafond/1024:.0f} Ko) — a verifier a la main")
        if (w, h) != cible:
            note.append(f"HORS GABARIT {w}x{h}")
            alertes.append(f"HORS GABARIT : {prenom}{ext} fait {w}x{h} "
                           f"(attendu {cible[0]}x{cible[1]}) — ne pas publier")
        note.append(f"{w}x{h}")

        gain += avant - apres
        print(f"{f[:37]:<38} {'->':^4} {prenom + ext:<16} "
              f"{avant/1024:>7.0f}K {apres/1024:>7.0f}K  {', '.join(note)}")

    print("-" * 100)
    print(f"\n{len(hauteurs)} fichiers produits dans {args.out}/")
    print(f"Gain total : {gain/1024/1024:.2f} Mo")

    # Hauteur differente de 277 : a reporter dans <img height="..."> du HTML
    autres = {k: v for k, v in hauteurs.items() if v != HAUTEUR}
    if autres:
        print(f'\nHAUTEUR A METTRE DANS LE HTML (width="{LARGEUR}", height=... ; defaut 277) :')
        for k, v in sorted(autres.items()):
            print(f'  - {k} -> height="{v}"')

    if alertes:
        print("\nA VERIFIER :")
        for a in alertes:
            print(f"  - {a}")
    else:
        print("\nTout est conforme.")


if __name__ == "__main__":
    main()
