# Signatures GREYPE — README

Dernière mise à jour : voir date du commit. Écrit pour qu'Adrien n'ait plus à
redemander comment tout ça marche.

---

## 0. Aide-mémoire (à lire en premier)

### Allumer / éteindre le bandeau événementiel (le « switch »)

Le bandeau est la 1re image de toutes les signatures. L'allumer ou l'éteindre =
changer le contenu d'**un seul fichier** sur GitHub, `banniere_evenement_1108x277.gif`.
**Rien à modifier sur les postes ni dans Outlook.** Valable pour toutes les
signatures d'un coup. Délai : jusqu'à ~10 min (2 caches de 5 min), plus long
dans les mails déjà ouverts (proxy Gmail).

**État actuel : ÉTEINT** (le fichier servi est un GIF transparent 1108×1 px).

| Je veux… | Avec le script (clone + Python) | Directement sur github.com (sans rien installer) |
|---|---|---|
| **Éteindre** | `python tools/bandeau.py off --push` | *Add file → Upload files* : déposer `bandeau/veille_1108x1.gif` **renommé** `banniere_evenement_1108x277.gif` |
| **Rallumer** le bandeau en cours | `python tools/bandeau.py on --push` | idem avec `bandeau/evenement_courant.gif` renommé `banniere_evenement_1108x277.gif` |
| **Nouveau** bandeau (autre événement) | `python tools/bandeau.py nouveau visuel.gif --push` | déposer le nouveau GIF (1108 px de large, < 2 Mo) sous le nom exact `banniere_evenement_1108x277.gif` |
| Voir l'état | `python tools/bandeau.py status` | — |

Le nom `banniere_evenement_1108x277.gif` ne change **jamais**, même si l'image
n'a plus cette taille (c'est un nom d'URL, pas une description). Détails : §4 et §4bis.

### Publier / modifier la signature d'une personne
1. Normaliser : `python tools/normaliser_nominatives.py dossier_recu/ -o nominatives/`
   (source fixe JPEG/PNG → `prenom.jpg` ; animation → `prenom.gif`).
2. **Si le format change** (ex. `.gif` → `.jpg`), **supprimer l'ancien fichier** : le
   Worker sert `.gif` en premier, puis `.jpg`, puis `.png`. L'URL des signatures ne
   change pas (§9).
3. Pousser sur `main`. La signature se met à jour chez tout le monde (~10 min).

### Donner la signature à un collaborateur
- **Gabarits HTML** : `python tools/generer_gabarits.py --worker https://greype-sig.greype.workers.dev -o gabarits/`
  (une ligne « Cordialement, », le bandeau, puis la signature ; aucune hauteur imposée).
- **Copie dans le presse-papiers** : `tools/copier_gabarits_gui.py` → `signatures_greype.exe`
  (fenêtre avec la liste des prénoms, Ctrl+V dans Outlook). Compilation : voir l'en-tête du fichier.
- **Outlook classique (bureau) : à vérifier** — coller du HTML dans l'éditeur de signature
  peut faire **télécharger et stocker localement** les images au lieu de garder le lien ;
  l'interrupteur du bandeau ne marcherait alors pas pour cette signature. Test : s'envoyer un
  mail vers Gmail → *Afficher l'original* → on doit y trouver `greype-sig.greype.workers.dev`
  (pas `cid:` ni un bloc base64). Le nouvel Outlook garde en principe le lien (à vérifier aussi).

---

## 1. Vue d'ensemble

Deux familles d'images, deux régimes différents :

| | Bandeau événement | Signatures nominatives |
|---|---|---|
| Fichier | 1 seul, partagé par tout le monde | 1 par personne |
| Format | largeur 1108, GIF (animé) | largeur 1108, hauteur selon le visuel (277 ou 462) |
| Change quand ? | À chaque campagne (salon, Noël…) | Rarement (nom, poste, tél.) |
| Qui le fournit | Toi / normalise_banniere.py | Marketing, export Canva |
| Nommage | `banniere_evenement_1108x277.gif` (fixe) | `prenom.jpg` (visuel fixe) ou `prenom.gif` (animé) |

**Le principe qui rend tout ça indolore : l'URL ne change jamais.**
Les 30 signatures Outlook contiennent chacune deux `<img src="...">` figés.
Publier un nouveau visuel = remplacer le fichier sous le même nom sur
GitHub. Personne ne rouvre Outlook.

---

## 2. Où sont les fichiers

Dépôt : `github.com/adorex5278/signature`

```
signature/
├── banniere_evenement_1108x277.gif   ← fichier SERVI aux signatures, ne pas renommer
│                                        (= copie du bandeau courant OU de la veille, voir §4bis)
├── bandeau/
│   ├── evenement_courant.gif         ← le bandeau événement en cours (source)
│   └── veille_1108x1.gif             ← GIF transparent 1 px = bandeau éteint
├── nominatives/
│   ├── adrien.jpg                    ← prenom.jpg (visuel fixe) ou prenom.gif (animé)
│   ├── alex.jpg
│   ├── ... (une par personne ; le Worker sert .gif, puis .jpg, puis .png)
├── worker/
│   └── worker.js                     ← Cloudflare Worker : URL stable sans extension (voir §9)
├── tools/
│   ├── generer_gabarits.py           ← régénère les gabarits HTML (voir §9)
│   ├── copier_gabarits_gui.py        ← exe « presse-papiers » pour coller dans Outlook (voir §0)
│   ├── bandeau.py                    ← interrupteur du bandeau (on / off / nouveau)
│   ├── normalise_banniere.py         ← pour le bandeau événement
│   └── normaliser_nominatives.py     ← pour le lot de signatures perso
└── input/                             ← boîte aux lettres du workflow (voir §5)
```

## 3. URL utilisées dans les signatures Outlook

**URL actuelles (via le Worker Cloudflare, sans extension — voir §9) :**

```
Bandeau :     https://greype-sig.greype.workers.dev/bandeau
Nominative :  https://greype-sig.greype.workers.dev/n/PRENOM
```

Le Worker va chercher les fichiers sur GitHub :

```
Bandeau :     https://raw.githubusercontent.com/adorex5278/signature/main/banniere_evenement_1108x277.gif
Nominative :  https://raw.githubusercontent.com/adorex5278/signature/main/nominatives/PRENOM.(gif|jpg|png)
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

Puis le publier (et l'allumer) avec l'interrupteur, qui le met **sous le nom
déjà utilisé** (`banniere_evenement_1108x277.gif`) :

```bash
python tools/bandeau.py nouveau banniere_signature.gif --push
```

Ne jamais renommer le fichier servi — ça casserait l'URL dans les 30
signatures. Attendre 5 minutes (cache raw), vérifier en navigation privée,
c'est fait.

**L'attribut `alt`** dans le HTML de la signature n'est pas mis à jour
automatiquement par ce process — il reste écrit en dur au moment du collage
dans Outlook. Les gabarits livrent `alt=""` (bandeau décoratif) pour ne pas
afficher un message périmé quand le bandeau est éteint. Si on veut un texte
alternatif pour un événement, il faut le saisir à la main dans les 30
signatures : c'est la seule chose que changer le fichier ne fait pas tout seul.

## 4bis. Éteindre / rallumer le bandeau (sans toucher aux postes)

```bash
python tools/bandeau.py status          # allumé ? éteint ?
python tools/bandeau.py off --push      # éteint : le bandeau disparaît des signatures
python tools/bandeau.py on  --push      # rallume le bandeau courant
```

Éteindre = remplacer le contenu du fichier servi par `bandeau/veille_1108x1.gif`
(GIF **transparent de 1 px de haut**, 103 octets). Aucun poste, aucune
signature Outlook n'est à modifier : c'est la même URL.

**Condition pour que ça ne laisse pas de trou : le `<img>` du bandeau dans le
gabarit HTML n'a PAS d'attribut `height`** (seulement `width="1108"` et
`style="…height:auto"`). L'image prend alors la hauteur de ce qu'on sert :
277 px allumé, 1 px éteint. Si on remet un `height="277"`, le bandeau éteint
laissera un vide blanc de 277 px.

Délai : ~5 min (cache raw), plus long dans les mails déjà ouverts (proxy Gmail).
Sans `--push`, le fichier est modifié en local et il reste à faire `git push`.

---

## 5. Publier un nouveau lot de signatures nominatives

Le marketing fournit un dossier de GIF Canva, format et poids variables,
noms de fichiers en pagaille (espaces, majuscules, "GIF OK" collé au nom).

**Visuel fixe (JPEG/PNG, sans animation) → fichier `prenom.jpg`, pas `.gif`.**
Un GIF est limité à 256 couleurs : sur un visuel fixe ça dégrade nettement
l'image. Le script sort donc un JPEG 4:4:4 à la qualité la plus haute qui
tient dans le budget (adrien, elysee, rajaa, roxane sont en `.jpg`). L'URL du
gabarit HTML doit alors finir en `.jpg` ; la hauteur (`height`) est affichée
en fin de run. Seuls les visuels animés restent en `.gif`.

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

---

## 9. URL stable, indépendante du format (Cloudflare Worker)

Problème : une URL GitHub contient l'extension (`adrien.gif`). Passer une
image en `.jpg`/`.png` change l'URL → il faut recoller la signature.
Solution gratuite, sans domaine : un **Worker Cloudflare** (`worker/worker.js`,
~50 lignes) qui reçoit `/n/<prenom>` ou `/bandeau`, cherche le fichier sur
GitHub (gif, jpg, png) et le renvoie avec le bon type. Les signatures
pointent vers le Worker : **le format d'une image peut changer sans jamais
toucher aux signatures collées**. L'interrupteur du bandeau (§4bis) continue de
fonctionner tel quel.

```
Bandeau :     https://<worker>.workers.dev/bandeau
Nominative :  https://<worker>.workers.dev/n/PRENOM
```

**État : déployé** sur `https://greype-sig.greype.workers.dev` (compte Cloudflare
gratuit, sous-domaine `greype`). Testé : `/bandeau`, `/n/adrien` (jpg),
`/n/kinjodemol` (gif). Les gabarits des 18 signatures pointent dessus.
Le code déployé est celui de `worker/worker.js` (à recoller dans l'éditeur
Cloudflare si on le modifie).

**Mise en place (une fois, ~10 min, gratuit — plan Free : 100 000 requêtes/jour)**

1. Créer un compte gratuit sur `dash.cloudflare.com` (e-mail + mot de passe).
2. *Workers & Pages* → *Create* → *Create Worker* (« Hello World ») → nom :
   `greype-sig` → *Deploy*.
3. *Edit code* → supprimer le code d'exemple → coller le contenu de
   `worker/worker.js` → *Deploy*.
4. Noter l'adresse du Worker : `https://greype-sig.<ton-sous-domaine>.workers.dev`.
5. Vérifier dans un navigateur : `…/bandeau` et `…/n/adrien` affichent l'image.
6. Générer les gabarits :
   `python tools/generer_gabarits.py --worker https://greype-sig.<…>.workers.dev -o gabarits/`

Les gabarits générés n'ont **aucun attribut `height`** (largeur seule +
`height:auto`) : la hauteur suit l'image, donc un visuel d'un autre ratio ne
demande pas non plus de modifier le gabarit.

**Points de vigilance**
- L'adresse `workers.dev` est liée au compte Cloudflare : si le compte est
  supprimé ou suspendu, toutes les signatures cassent. Garder l'accès (mot de
  passe dans le gestionnaire de mots de passe, au moins 2 personnes informées).
- Certains filtres anti-spam / passerelles web classent `workers.dev` avec
  réserve : tester l'arrivée de vraies images chez des destinataires externes
  (Gmail, Outlook, une grande entreprise) avant de généraliser.
- Si un jour le domaine `greype-france.com` devient accessible, remplacer
  `workers.dev` par un sous-domaine GREYPE (une seule fois, dans le générateur).
