#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signatures GREYPE — copie un gabarit de signature dans le presse-papiers
(HTML riche), pret a coller dans Outlook (Ctrl+V dans l'editeur de signature).

  - sans argument : fenetre avec la liste des prenoms
  - avec un prenom : copie directement et quitte  (ex: signatures_greype.exe alex)

Les gabarits sont ceux EMBARQUES dans l'exe. Si un dossier "gabarits_30"
existe a cote de l'exe, il est utilise a la place (mise a jour sans recompiler).

Compilation (depuis tools/) :
    python -m PyInstaller --onefile --noconsole --name signatures_greype ^
        --add-data "<dossier gabarits_30>;gabarits_30" copier_gabarits_gui.py
"""

import ctypes
import os
import re
import sys
import time

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040


def dossier_exe():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def dossier_gabarits():
    externe = os.path.join(dossier_exe(), "gabarits_30")
    if os.path.isdir(externe) and any(f.startswith("signature_") for f in os.listdir(externe)):
        return externe
    base = getattr(sys, "_MEIPASS", dossier_exe())
    return os.path.join(base, "gabarits_30")


def prenoms():
    d = dossier_gabarits()
    return sorted(f[len("signature_"):-len(".html")] for f in os.listdir(d)
                  if f.startswith("signature_") and f.endswith(".html"))


def fragment_html(prenom):
    chemin = os.path.join(dossier_gabarits(), f"signature_{prenom}.html")
    with open(chemin, encoding="utf-8") as fh:
        html = fh.read()
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S)
    frag = m.group(1) if m else html
    return re.sub(r"<!--.*?-->", "", frag, flags=re.S).strip()


def construire_cf_html(fragment):
    """Format 'HTML Format' du presse-papiers Windows (offsets en octets UTF-8)."""
    debut = "<html><body>\r\n<!--StartFragment-->"
    fin = "<!--EndFragment-->\r\n</body></html>"
    entete = ("Version:0.9\r\nStartHTML:{:010d}\r\nEndHTML:{:010d}\r\n"
              "StartFragment:{:010d}\r\nEndFragment:{:010d}\r\n")
    n = len(entete.format(0, 0, 0, 0).encode("utf-8"))
    b = lambda s: len(s.encode("utf-8"))
    start_frag = n + b(debut)
    end_frag = start_frag + b(fragment)
    end_html = end_frag + b(fin)
    return (entete.format(n, end_html, start_frag, end_frag) + debut + fragment + fin).encode("utf-8")


def copier(prenom):
    """Met le gabarit dans le presse-papiers (HTML + texte). Leve OSError si echec."""
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.RegisterClipboardFormatW.argtypes = [ctypes.c_wchar_p]

    cf_html = user32.RegisterClipboardFormatW("HTML Format")
    donnees_html = construire_cf_html(fragment_html(prenom)) + b"\x00"
    donnees_txt = "Cordialement,".encode("utf-16-le") + b"\x00\x00"

    for _ in range(20):                      # le presse-papiers peut etre occupe un instant
        if user32.OpenClipboard(None):
            break
        time.sleep(0.1)
    else:
        raise OSError("presse-papiers occupe")
    try:
        user32.EmptyClipboard()
        for fmt, data in ((cf_html, donnees_html), (CF_UNICODETEXT, donnees_txt)):
            h = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data))
            p = kernel32.GlobalLock(h)
            ctypes.memmove(p, data, len(data))
            kernel32.GlobalUnlock(h)
            if not user32.SetClipboardData(fmt, h):
                raise OSError("SetClipboardData a echoue")
    finally:
        user32.CloseClipboard()


def fenetre():
    import tkinter as tk
    from tkinter import ttk

    liste = prenoms()
    root = tk.Tk()
    root.title("Signatures GREYPE")
    root.geometry("360x560")
    root.minsize(320, 400)

    ttk.Label(root, text="Choisis un prénom puis Entrée (ou double-clic)",
              padding=(10, 10, 10, 4)).pack(anchor="w")
    filtre = tk.StringVar()
    entree = ttk.Entry(root, textvariable=filtre)
    entree.pack(fill="x", padx=10)

    cadre = ttk.Frame(root)
    cadre.pack(fill="both", expand=True, padx=10, pady=8)
    lb = tk.Listbox(cadre, font=("Segoe UI", 12), activestyle="dotbox", exportselection=False)
    sb = ttk.Scrollbar(cadre, command=lb.yview)
    lb.config(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    lb.pack(side="left", fill="both", expand=True)

    statut = tk.StringVar(value="Prêt.")
    ttk.Label(root, textvariable=statut, padding=(10, 0, 10, 6), wraplength=330).pack(anchor="w")

    visibles = []

    def remplir(*_):
        nonlocal visibles
        t = filtre.get().strip().lower()
        visibles = [p for p in liste if t in p]
        lb.delete(0, "end")
        for p in visibles:
            lb.insert("end", p.capitalize())
        if visibles:
            lb.selection_set(0)

    def valider(*_):
        sel = lb.curselection()
        if not sel:
            return
        p = visibles[sel[0]]
        try:
            copier(p)
            statut.set(f"✔ {p.capitalize()} copié — colle avec Ctrl+V dans Outlook.")
        except Exception as e:                       # noqa: BLE001
            statut.set(f"✘ Échec : {e}")

    def bas(_):
        sel = lb.curselection()
        if sel and sel[0] + 1 < lb.size():
            lb.selection_clear(0, "end"); lb.selection_set(sel[0] + 1); lb.see(sel[0] + 1)
        return "break"

    def haut(_):
        sel = lb.curselection()
        if sel and sel[0] > 0:
            lb.selection_clear(0, "end"); lb.selection_set(sel[0] - 1); lb.see(sel[0] - 1)
        return "break"

    filtre.trace_add("write", remplir)
    entree.bind("<Return>", valider)
    entree.bind("<Down>", bas)
    entree.bind("<Up>", haut)
    lb.bind("<Double-Button-1>", valider)
    lb.bind("<Return>", valider)
    ttk.Button(root, text="Copier dans le presse-papiers", command=valider).pack(
        fill="x", padx=10, pady=(0, 10))
    remplir()
    entree.focus_set()
    root.mainloop()


def main():
    if len(sys.argv) > 1:
        p = sys.argv[1].strip().lower()
        if p not in prenoms():
            sys.exit(f"Prénom inconnu : {p}")
        copier(p)
        return
    fenetre()


if __name__ == "__main__":
    main()
