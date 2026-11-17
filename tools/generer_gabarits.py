#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generer_gabarits.py
-------------------
Regenere les gabarits HTML de signature (un par fichier de nominatives/) :
plus aucune edition a la main quand une image change de format ou de taille.

Dans les gabarits, AUCUN attribut height n'est ecrit (width seul + height:auto) :
la hauteur suit l'image servie, donc un visuel d'un autre ratio ne demande
pas de toucher au gabarit.

Deux modes d'URL :
  --worker https://xxx.workers.dev   URL stable sans extension (recommande) :
        bandeau -> <worker>/bandeau        nominatif -> <worker>/n/<prenom>
  (sans --worker)                    URL directes GitHub, avec extension reelle
        trouvee dans nominatives/ (ex: .../nominatives/adrien.jpg)

Usage :
    python tools/generer_gabarits.py --worker https://greype-sig.xxx.workers.dev -o gabarits/
    python tools/generer_gabarits.py -o gabarits/
"""

import argparse
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "https://raw.githubusercontent.com/adorex5278/signature/main/"
EXT_OK = (".gif", ".jpg", ".jpeg", ".png")
LARGEUR = 1108

STYLE = "display:block;border:0;outline:none;max-width:100%;height:auto;"

GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>Signature GREYPE</title></head>
<body style="margin:20px;background:#ffffff;">

<!-- ===== FORMULE DE POLITESSE — premiere ligne ===== -->
<p style="margin:0 0 12px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#000000;">Cordialement,</p>

<!-- ===== BANDEAU EVENEMENT — en haut, identique pour tout le monde ===== -->
<img src="{url_bandeau}" width="{largeur}" style="{style}" alt="">

<!-- ===== BLOC NOMINATIF — en dessous ===== -->
<img src="{url_nominatif}" width="{largeur}" style="{style}margin-top:8px;" alt="GREYPE FRANCE">

</body>
</html>
"""


def main():
    p = argparse.ArgumentParser(description="Genere les gabarits HTML de signature")
    p.add_argument("-o", "--out", default="gabarits", help="dossier de sortie")
    p.add_argument("--worker", help="URL du Worker Cloudflare (ex: https://greype-sig.xxx.workers.dev)")
    a = p.parse_args()

    dossier = os.path.join(RACINE, "nominatives")
    fichiers = sorted(f for f in os.listdir(dossier) if f.lower().endswith(EXT_OK))
    if not fichiers:
        sys.exit("Aucune image dans nominatives/")

    if a.worker:
        base = a.worker.rstrip("/")
        if not base.startswith("https://"):
            sys.exit("--worker doit commencer par https://")
        url_bandeau = base + "/bandeau"
    else:
        url_bandeau = RAW + "banniere_evenement_1108x277.gif"

    os.makedirs(a.out, exist_ok=True)
    vus = set()
    for f in fichiers:
        prenom, ext = os.path.splitext(f)
        if prenom in vus:
            print(f"ATTENTION : deux fichiers pour '{prenom}' dans nominatives/ — ignore {f}")
            continue
        vus.add(prenom)
        url_nom = f"{a.worker.rstrip('/')}/n/{prenom}" if a.worker else f"{RAW}nominatives/{f}"
        html = GABARIT.format(url_bandeau=url_bandeau, url_nominatif=url_nom,
                              largeur=LARGEUR, style=STYLE)
        with open(os.path.join(a.out, f"signature_{prenom}.html"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)

    mode = f"Worker {a.worker}" if a.worker else "URL directes GitHub"
    print(f"{len(vus)} gabarits ecrits dans {a.out}/  ({mode})")


if __name__ == "__main__":
    main()
