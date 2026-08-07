# Signatures GREYPE — README

Dernière mise à jour : voir date du commit. Écrit pour qu'Adrien n'ait plus à
redemander comment tout ça marche.

---

## 1. Vue d'ensemble

Deux familles d'images, deux régimes différents :

| | Bandeau événement | Signatures nominatives |
|---|---|---|
| Fichier | 1 seul, partagé par tout le monde | 1 par personne (30) |
| Format | 1108 × 277 | 1108 × 277 |
| Change quand ? | À chaque campagne (salon, Noël…) | Rarement (nom, poste, tél.) |
| Qui le fournit | Toi / normalise_banniere.py | Marketing, export Canva |
| Nommage | `banniere_evenement_1108x277.gif` (fixe) | `prenom.gif` |

**Le principe qui rend tout ça indolore : l'URL ne change jamais.**
Les 30 signatures Outlook contiennent chacune deux `<img src="...">` figés.
Publier un nouveau visuel = remplacer le fichier sous le même nom sur
GitHub. Personne ne rouvre Outlook.

---

## 2. Où sont les fichiers

Dépôt : `github.com/adorex5278/signature`

```
signature/
├── banniere_evenement_1108x277.gif   ← bandeau partagé, ne pas renommer
├── nominatives/
│   ├── adrien.gif
│   ├── alex.gif
│   ├── ... (18 à ce jour, 30 à terme)
├── tools/
│   ├── normalise_banniere.py         ← pour le bandeau événement
│   └── normaliser_nominatives.py     ← pour le lot de signatures perso
└── input/                             ← boîte aux lettres du workflow (voir §5)
```

## 3. URL utilisées dans les signatures Outlook

```
Bandeau :     https://raw.githubusercontent.com/adorex5278/signature/main/banniere_evenement_1108x277.gif
Nominative :  https://raw.githubusercontent.com/adorex5278/signature/main/nominatives/PRENOM.gif
```

`raw.githubusercontent.com` fonctionne mais son cache est court (5 min) et
ce n'est pas un hébergement de production. **Si GitHub Pages est activé un
jour** sur le dépôt (Settings → Pages), remplacer le début de l'URL par
`https://adorex5278.github.io/signature/...` — une seule fois, dans le
gabarit de signature, pas dans chaque boîte.

---

## 4. Publier un nouveau bandeau événement (Noël, prochain salon…)

```bash
python tools/normalise_banniere.py visuel_noel.mp4
```

Accepte GIF, PNG, JPG, WEBP, MP4 — n'importe quelle dimension en entrée.
Sort toujours en 1108 × 277, poste-image en tête pour Outlook classique,
et compresse jusqu'à tenir sous ~2,5 Mo.

Puis : pousser le fichier produit sur GitHub **sous le nom déjà utilisé**
(`banniere_evenement_1108x277.gif`). Ne jamais renommer — ça
casserait l'URL dans les 30 signatures.

Attendre 5 minutes (cache raw), vérifier en navigation privée, c'est fait.

**Rappel du 1 point à ne pas oublier chaque fois : l'attribut `alt`** dans
le HTML de la signature n'est pas mis à jour automatiquement par ce process
— il reste écrit en dur au moment du collage dans Outlook. Si le message
change de sens (ex: "Stand 7D02" → "Joyeuses fêtes"), il faut retoucher le
texte alternatif à la main dans les 30 signatures. C'est la seule chose que
changer le fichier ne fait pas tout seul.

---

## 5. Publier un nouveau lot de signatures nominatives

Le marketing fournit un dossier de GIF Canva, format et poids variables,
noms de fichiers en pagaille (espaces, majuscules, "GIF OK" collé au nom).

```bash
python tools/normaliser_nominatives.py dossier_recu/ -o nominatives/
```

Ce que le script fait automatiquement :

- **Renomme** en `prenom.gif` (minuscule, sans accent, sans espace) à partir
  du premier mot utile du nom de fichier fourni.
- **Force le gabarit** 1108 × 277 pour tout le monde, même si la source
  arrive dans une autre taille.
- **Compresse** (Canva exporte du GIF non optimisé, ~340 Ko → ~150 Ko sans
  perte visible).
- **Sous-échantillonne les frames** si la source en a un nombre excessif
  (ex : un export passé par un site tiers à 150 images) — sinon
  l'agrandissement au gabarit fait exploser le poids pour un gain de
  fluidité invisible sur une signature.
- **Refuse silencieusement rien** : tout ce qui pose problème est listé
  en clair à la fin, sous "A VERIFIER".

### Cas particuliers rencontrés (pour référence)

- **Doublon de prénom** (deux "Nico" par ex.) : le script ajoute un chiffre
  (`nico2.gif`) et le signale. Il ne choisit jamais silencieusement de
  fichier à la place de l'autre — c'est à vérifier à la main si ça arrive.
- **Fichier déjà minuscule en entrée** (image source plus petite que
  1108×277) : l'agrandissement peut dépasser le budget de poids et/ou
  perdre en netteté. Le script publie quand même le résultat (mieux que
  rien) mais le signale en "A VERIFIER" — demander à la personne de
  refournir un export Canva natif plutôt qu'un fichier déjà retouché par
  un outil tiers (type ezgif).

### Après le passage du script

- Contrôler la liste "A VERIFIER" affichée en fin d'exécution.
- Pousser le contenu de `nominatives/` sur GitHub, dans le dossier
  `nominatives/` du dépôt, **en gardant les noms `prenom.gif`**.
- Chaque personne n'a besoin de coller sa signature dans Outlook
  **qu'une seule fois** — l'URL `nominatives/prenom.gif` ne bouge plus
  ensuite, même si son visuel est mis à jour plus tard (nouveau poste,
  nouveau numéro...).

---

## 6. Le mail-type à donner à chaque collaborateur (une seule fois)

Objet du mail : contient un fichier `.html` à ouvrir dans Chrome/Edge,
sélectionner tout (Ctrl+A), copier (Ctrl+C), coller dans Outlook →
Paramètres → Courrier → Composer et répondre → Signature.

Le `<img>` de ce fichier pointe vers `nominatives/PRENOM.gif` — remplacer
PRENOM par le prénom exact utilisé dans le nom de fichier produit à
l'étape 5.

---

## 7. Limites et points de vigilance

- **Bande passante GitHub** : quota souple de 100 Go/mois. À 30 personnes
  et un usage courant de messagerie professionnelle, ça reste large tant
  que le bandeau événement est optimisé (viser < 1 Mo). Un bandeau à
  2+ Mo, multiplié par un fort volume d'envois/ouvertures, peut approcher
  la limite — voir calcul dans l'historique de conversation si besoin de
  refaire le point.
- **CGU GitHub Pages** : l'usage commercial intensif (30 signatures
  d'entreprise) est en zone grise vis-à-vis des conditions d'utilisation
  du service gratuit. Envisager de migrer vers un hébergement propre à
  GREYPE (ex: `greype-france.com/assets/`) si le volume grandit encore —
  ça règle aussi la question de cohérence de domaine (image servie depuis
  le même domaine que l'expéditeur = meilleure délivrabilité).
- **Cache des destinataires** : remplacer un fichier sous le même nom ne
  met pas forcément à jour instantanément chez ceux qui ont déjà ouvert un
  mail avec l'ancienne version (proxy Gmail notamment, qui met en cache
  l'image côté serveur). Sans impact pour une mise à jour "propre" (avant
  tout envoi), mais ne pas compter sur une extinction immédiate et totale
  d'un visuel déjà largement diffusé.
- **Nouvel Outlook et signatures itinérantes** : les signatures sont
  stockées côté serveur (Exchange Online) et non plus en local. Un
  changement fait dans un client peut être écrasé par la synchronisation
  depuis un autre. Sans effet sur ce système (l'image reste distante,
  seule l'URL est collée une fois), mais à garder en tête si un jour une
  signature "revient en arrière" toute seule après une modif manuelle.

---

## 8. Ce qu'il ne faut jamais faire

- Renommer `banniere_evenement_1108x277.gif`.
- Changer le gabarit (1108×277, désormais identique pour le bandeau et les
  nominatives) sans modifier `TARGET_W` / `TARGET_H` en tête des deux
  scripts ET sans savoir que ça implique de rouvrir les 30 signatures
  Outlook.
- Pousser un fichier hors gabarit "parce que ça ira plus vite" — les
  scripts existent justement pour éviter d'avoir à rouvrir Outlook plus
  tard. Un fichier hors gabarit dans une signature déjà collée s'affichera
  déformé ou tronqué selon le client mail.
