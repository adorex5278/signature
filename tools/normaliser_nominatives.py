#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normaliser_nominatives.py
-------------------------
Traite en lot les GIF nominatifs fournis par le marketing :
  - renomme en prenom.gif (minuscules, sans accent ni espace)
  - force le gabarit 1108 x 277
  - optimise (Canva sort du GIF non compresse : ~340 Ko -> ~150 Ko)
  - refuse de publier un fichier hors gabarit

Usage :
    python normaliser_nominatives.py dossier_source/ -o nominatives/
    python normaliser_nominatives.py input/ -o nominatives/ --max-ko 200
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import unicodedata

# ============================================================
#  GABARIT — doit correspondre a width/height dans les signatures
# ============================================================
LARGEUR = 1108
HAUTEUR = 277
MAX_KO_DEFAUT = 200
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


def traiter(source, destination, max_octets):
    """Sous-echantillonne si besoin, redimensionne si besoin, puis compresse
    jusqu'a tenir dans le budget."""
    tmp_ech = destination + ".ech.gif"
    src_travail, allege = sous_echantillonner_si_besoin(source, tmp_ech)

    (w, h), _ = dimensions(src_travail)
    besoin_resize = (w, h) != (LARGEUR, HAUTEUR)

    base = ["gifsicle", "--careful", "-O3"]
    if besoin_resize:
        base += [f"--resize={LARGEUR}x{HAUTEUR}"]

    resultat = None
    for couleurs, lossy in ((255, 30), (255, 60), (192, 60), (128, 80), (96, 100), (64, 140)):
        cmd = base + [f"--colors={couleurs}", f"--lossy={lossy}", src_travail, "-o", destination]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(destination):
            resultat = (os.path.getsize(destination), couleurs, lossy, besoin_resize, allege)
            if resultat[0] <= max_octets:
                break

    if os.path.exists(tmp_ech):
        os.remove(tmp_ech)

    if resultat is None:
        raise RuntimeError("gifsicle n'a rien produit")
    return resultat


def main():
    p = argparse.ArgumentParser(description="Normalise les GIF nominatifs en lot")
    p.add_argument("source", help="dossier contenant les GIF fournis")
    p.add_argument("-o", "--out", default="nominatives", help="dossier de sortie")
    p.add_argument("--max-ko", type=int, default=MAX_KO_DEFAUT)
    args = p.parse_args()

    if not shutil.which("gifsicle"):
        sys.exit("gifsicle introuvable.\nWindows : choco install gifsicle")
    if not os.path.isdir(args.source):
        sys.exit(f"Dossier introuvable : {args.source}")

    os.makedirs(args.out, exist_ok=True)
    fichiers = sorted(f for f in os.listdir(args.source) if f.lower().endswith(".gif"))
    if not fichiers:
        sys.exit(f"Aucun .gif dans {args.source}")

    plafond = args.max_ko * 1024
    print(f"Gabarit {LARGEUR}x{HAUTEUR}  |  budget {args.max_ko} Ko  |  {len(fichiers)} fichiers\n")
    print(f"{'source':<38} {'->':^4} {'sortie':<16} {'avant':>8} {'apres':>8}  note")
    print("-" * 92)

    vus, alertes, gain = {}, [], 0

    for f in fichiers:
        src = os.path.join(args.source, f)
        prenom = prenom_depuis(f)

        if prenom in vus:
            suffixe = 2
            while f"{prenom}{suffixe}" in vus:
                suffixe += 1
            alertes.append(f"Doublon de prenom : '{f}' renomme en {prenom}{suffixe}.gif")
            prenom = f"{prenom}{suffixe}"
        vus[prenom] = f

        dst = os.path.join(args.out, f"{prenom}.gif")
        avant = os.path.getsize(src)
        try:
            apres, coul, lossy, resize, allege = traiter(src, dst, plafond)
        except Exception as e:
            alertes.append(f"ECHEC sur '{f}' : {e}")
            continue

        (w, h), n = dimensions(dst)
        note = []
        if allege:
            note.append(f"frames reduites")
        if resize:
            note.append("redimensionne")
        if apres > plafond:
            note.append(f"depasse {args.max_ko} Ko")
            alertes.append(f"'{prenom}.gif' fait {apres/1024:.0f} Ko malgre compression max — "
                            f"a verifier a la main")
        if (w, h) != (LARGEUR, HAUTEUR):
            note.append(f"HORS GABARIT {w}x{h}")
            alertes.append(f"HORS GABARIT : {prenom}.gif fait {w}x{h} — ne pas publier")

        gain += avant - apres
        print(f"{f[:37]:<38} {'->':^4} {prenom + '.gif':<16} "
              f"{avant/1024:>7.0f}K {apres/1024:>7.0f}K  {', '.join(note)}")

    print("-" * 92)
    print(f"\n{len(vus)} fichiers produits dans {args.out}/")
    print(f"Gain total : {gain/1024/1024:.2f} Mo")

    if alertes:
        print("\nA VERIFIER :")
        for a in alertes:
            print(f"  - {a}")
    else:
        print("\nTout est conforme au gabarit.")


if __name__ == "__main__":
    main()
