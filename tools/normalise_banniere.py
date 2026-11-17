#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalise_banniere.py
---------------------
Normalise n'importe quel visuel (GIF, PNG, JPG, MP4, WEBP...) en un GIF
aux dimensions FIGEES attendues par les signatures Outlook.

Usage :
    python normalise_banniere.py visuel_noel.mp4
    python normalise_banniere.py visuel.png --fit cover
    python normalise_banniere.py visuel.gif --out banniere.gif --max-mo 1.5

Le fichier produit doit ensuite etre pousse sur GitHub SOUS LE MEME NOM
que le precedent : les signatures Outlook ne sont jamais retouchees.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# ============================================================
#  REGLAGES — a modifier seulement si tes signatures changent
# ============================================================
TARGET_W = 1108          # doit correspondre a width="..." dans la signature
TARGET_H = 277           # doit correspondre a height="..." dans la signature
BG_COLOR = "white"       # fond des bandes de remplissage en mode "contain"
DEFAULT_FPS = 20
DEFAULT_MAX_MO = 2.5
# ============================================================


def a_outil(nom):
    return shutil.which(nom) is not None


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def filtre_cadrage(fit):
    """Construit le filtre ffmpeg qui force TARGET_W x TARGET_H."""
    if fit == "cover":
        # remplit tout le cadre, rogne ce qui depasse
        return (f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={TARGET_W}:{TARGET_H}")
    if fit == "stretch":
        # deforme pour remplir — a eviter
        return f"scale={TARGET_W}:{TARGET_H}:flags=lanczos"
    # contain (defaut) : visuel entier, bandes de remplissage
    return (f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color={BG_COLOR}")


def construire_gif(src, dst, fps, couleurs, fit):
    vf = (f"fps={fps},{filtre_cadrage(fit)},split[s0][s1];"
          f"[s0]palettegen=max_colors={couleurs}:stats_mode=diff[p];"
          f"[s1][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
    r = run(["ffmpeg", "-v", "error", "-i", src, "-vf", vf, "-loop", "0", "-y", dst])
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg a echoue :\n{r.stderr}")


def poster_et_compresser(src, dst, lossy, tmp):
    """
    Place la derniere image en tete (Outlook classique n'affiche que la 1re),
    puis optimise. Retourne la taille du fichier produit.
    """
    from PIL import Image

    propre = os.path.join(tmp, "propre.gif")
    run(["gifsicle", "--colors=255", src, "-o", propre])
    if not os.path.exists(propre):
        propre = src

    n = Image.open(propre).n_frames
    if n <= 1:
        run(["gifsicle", "-O3", f"--lossy={lossy}", "--careful", propre, "-o", dst])
        return os.path.getsize(dst)

    tete = os.path.join(tmp, "tete.gif")
    corps = os.path.join(tmp, "corps.gif")
    run(["gifsicle", "-U", propre, f"#{n-1}", "-o", tete])
    run(["gifsicle", "-U", propre, "-o", corps])

    im = Image.open(propre)
    im.seek(1)
    delai = max(2, round((im.info.get("duration") or 50) / 10))

    run(["gifsicle", "-d2", tete, f"-d{delai}", corps,
         "-O3", f"--lossy={lossy}", "--careful", "--loopcount=forever", "-o", dst])
    return os.path.getsize(dst)


def verifier(chemin):
    from PIL import Image
    im = Image.open(chemin)
    return im.size, getattr(im, "n_frames", 1)


def main():
    p = argparse.ArgumentParser(description="Normalise un visuel en GIF de signature")
    p.add_argument("source", help="fichier d'entree (gif, png, jpg, mp4, webp...)")
    p.add_argument("--out", default="banniere_signature.gif", help="fichier de sortie")
    p.add_argument("--fit", choices=["contain", "cover", "stretch"], default="contain",
                   help="contain = visuel entier + bandes (defaut) | "
                        "cover = remplit et rogne | stretch = deforme")
    p.add_argument("--fps", type=int, default=DEFAULT_FPS)
    p.add_argument("--max-mo", type=float, default=DEFAULT_MAX_MO,
                   help="poids maximum vise en Mo")
    args = p.parse_args()

    if not os.path.exists(args.source):
        sys.exit(f"Introuvable : {args.source}")

    manquants = [o for o in ("ffmpeg", "gifsicle") if not a_outil(o)]
    if manquants:
        sys.exit("Outil(s) manquant(s) : " + ", ".join(manquants) +
                 "\nWindows : winget install ffmpeg  /  choco install gifsicle")

    plafond = args.max_mo * 1024 * 1024
    print(f"Cible : {TARGET_W}x{TARGET_H}  |  cadrage {args.fit}  |  max {args.max_mo} Mo\n")

    with tempfile.TemporaryDirectory() as tmp:
        # on desserre progressivement jusqu'a tenir dans le budget
        essais = [(200, 25), (160, 40), (128, 60), (96, 90), (64, 120), (48, 160)]
        retenu = None

        for couleurs, lossy in essais:
            brut = os.path.join(tmp, "brut.gif")
            construire_gif(args.source, brut, args.fps, couleurs, args.fit)
            taille = poster_et_compresser(brut, args.out, lossy, tmp)
            mo = taille / 1048576
            etat = "OK" if taille <= plafond else "trop lourd"
            print(f"  {couleurs:>3} couleurs / lossy {lossy:>3}  ->  {mo:5.2f} Mo   {etat}")
            if taille <= plafond:
                retenu = (couleurs, lossy, mo)
                break

        if retenu is None:
            print("\nBudget non atteint meme au reglage minimal.")
            print("Baisse --fps (12 ou 15) ou augmente --max-mo.")
            sys.exit(1)

    dims, frames = verifier(args.out)
    print(f"\n{args.out}")
    print(f"  {dims[0]}x{dims[1]}  |  {frames} images  |  {retenu[2]:.2f} Mo")

    if dims != (TARGET_W, TARGET_H):
        sys.exit(f"\nALERTE : dimensions {dims} != cible attendue. Ne pas publier.")

    print(f"\nDimensions conformes. Pousse ce fichier sur GitHub sous le nom")
    print(f"deja reference dans tes signatures — rien a modifier dans Outlook.")


if __name__ == "__main__":
    main()
