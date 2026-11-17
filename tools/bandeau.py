#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bandeau.py — interrupteur du bandeau evenement
----------------------------------------------
Les signatures Outlook pointent toutes vers la meme URL :
    .../main/banniere_evenement_1108x277.gif
Allumer / eteindre le bandeau = changer le CONTENU de ce fichier sur GitHub.
Rien a modifier sur les postes (ni dans Outlook, ni dans les signatures).

  eteint : le fichier servi est bandeau/veille_1108x1.gif (GIF transparent
           1108 x 1 px) -> le bandeau disparait, sans trou
  allume : le fichier servi est bandeau/evenement_courant.gif

Usage (depuis la racine du depot) :
    python tools/bandeau.py status
    python tools/bandeau.py off   [--push]
    python tools/bandeau.py on    [--push]
    python tools/bandeau.py nouveau visuel.gif [--push]   # remplace le bandeau
                                                           # courant ET l'allume
--push : git add + commit + push sur la branche courante.
Sans --push : le fichier est mis a jour en local, a toi de pousser.

Delai de prise en compte : ~5 min (cache raw.githubusercontent.com), plus
longtemps dans les mails deja ouverts (cache du proxy Gmail).
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys

LARGEUR = 1108
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVI = os.path.join(RACINE, "banniere_evenement_1108x277.gif")   # NE JAMAIS RENOMMER
ACTIF = os.path.join(RACINE, "bandeau", "evenement_courant.gif")
VEILLE = os.path.join(RACINE, "bandeau", "veille_1108x1.gif")


def empreinte(chemin):
    if not os.path.exists(chemin):
        return None
    with open(chemin, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def etat():
    h = empreinte(SERVI)
    if h is None:
        return "absent"
    if h == empreinte(VEILLE):
        return "eteint"
    if h == empreinte(ACTIF):
        return "allume"
    return "inconnu"      # fichier servi different des deux sources


def dimensions(chemin):
    from PIL import Image
    return Image.open(chemin).size


def git(*args):
    r = subprocess.run(["git", "-C", RACINE, *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} a echoue :\n{r.stderr.strip()}")
    return r.stdout.strip()


def publier(message):
    git("add", SERVI, ACTIF, VEILLE)
    if not git("status", "--porcelain", "--", SERVI, ACTIF, VEILLE):
        print("Rien a publier (deja dans cet etat).")
        return
    git("commit", "-m", message)
    git("push")
    print("Pousse sur GitHub. Attendre ~5 min (cache raw), verifier en navigation privee.")


def main():
    p = argparse.ArgumentParser(description="Interrupteur du bandeau evenement")
    p.add_argument("action", choices=["status", "on", "off", "nouveau"])
    p.add_argument("fichier", nargs="?", help="pour 'nouveau' : le GIF du nouveau bandeau")
    p.add_argument("--push", action="store_true", help="commit + push apres modification")
    a = p.parse_args()

    if a.action == "status":
        e = etat()
        print({"allume": "ALLUME — le bandeau evenement est affiche",
               "eteint": "ETEINT — le bandeau est en veille (GIF transparent 1 px)",
               "absent": "ABSENT — banniere_evenement_1108x277.gif n'existe pas !",
               "inconnu": "INCONNU — le fichier servi ne correspond ni a la veille ni au "
                          "bandeau courant (modifie a la main ?)"}[e])
        return

    if a.action == "nouveau":
        if not a.fichier or not os.path.isfile(a.fichier):
            sys.exit("Indique le GIF du nouveau bandeau : bandeau.py nouveau visuel.gif")
        w, h = dimensions(a.fichier)
        if w != LARGEUR:
            sys.exit(f"{a.fichier} fait {w}x{h} : la largeur doit etre {LARGEUR}. "
                     f"Passer d'abord par tools/normalise_banniere.py")
        shutil.copyfile(a.fichier, ACTIF)
        shutil.copyfile(ACTIF, SERVI)
        print(f"Nouveau bandeau {w}x{h} ({os.path.getsize(ACTIF)/1024/1024:.2f} Mo) : ALLUME")
        if a.push:
            publier("Bandeau evenement : nouveau visuel (allume)")
        return

    cible = {"on": ACTIF, "off": VEILLE}[a.action]
    if not os.path.exists(cible):
        sys.exit(f"Source manquante : {os.path.relpath(cible, RACINE)}")
    shutil.copyfile(cible, SERVI)
    print("Bandeau", "ALLUME" if a.action == "on" else "ETEINT (veille)")
    if a.push:
        publier(f"Bandeau evenement : {'allume' if a.action == 'on' else 'eteint (veille)'}")
    else:
        print("Fichier mis a jour en local. Pousser :  git add -A && git commit -m ... && git push")


if __name__ == "__main__":
    main()
