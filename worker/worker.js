// Cloudflare Worker — URL stable, independante du format de l'image
// -----------------------------------------------------------------
// Les signatures Outlook pointent vers :
//     https://<worker>.workers.dev/n/<prenom>        (GREYPE : signature nominative)
//     https://<worker>.workers.dev/bandeau           (GREYPE : bandeau evenement)
//     https://<worker>.workers.dev/lp/n/<prenom>     (LUNIPRIM'S : signature nominative)
//     https://<worker>.workers.dev/lp/bandeau        (LUNIPRIM'S : bandeau evenement)
// Le Worker va chercher le fichier sur GitHub en essayant plusieurs
// extensions (gif, jpg, png) et le renvoie avec le bon Content-Type.
// => changer le format d'une image (gif -> jpg...) ne change JAMAIS l'URL
//    collee dans les signatures.
// Pour ajouter une societe : une ligne dans SOCIETES (prefixe -> depot GitHub).
//
// Deploiement : voir README, section "URL stable (Cloudflare Worker)".

const SOCIETES = {
  "":   "https://raw.githubusercontent.com/adorex5278/signature/main/",            // GREYPE (URL historiques)
  "lp": "https://raw.githubusercontent.com/adorex5278/luniprims-signature/main/",  // LUNIPRIM'S
};
const BANDEAU = "banniere_evenement_1108x277";   // nom de base du fichier servi (sans extension)
const TYPES = [                                   // ordre d'essai
  ["gif", "image/gif"],
  ["jpg", "image/jpeg"],
  ["png", "image/png"],
];

async function chercher(depot, base) {
  for (const [ext, type] of TYPES) {
    const r = await fetch(depot + base + "." + ext, {
      cf: { cacheTtl: 300, cacheEverything: true },   // cache 5 min cote Cloudflare
    });
    if (r.ok) return { corps: r.body, type };
  }
  return null;
}

export default {
  async fetch(request) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }

    // /[prefixe/]n/<prenom>   ou   /[prefixe/]bandeau
    const chemin = new URL(request.url).pathname;
    const m = chemin.match(/^(?:\/([a-z]{1,10}))?(?:\/n\/([a-z0-9]{1,40})|\/(bandeau))$/);
    if (m === null) return new Response("Not found", { status: 404 });
    const prefixe = m[1] || "";
    if (!Object.prototype.hasOwnProperty.call(SOCIETES, prefixe)) {
      return new Response("Not found", { status: 404 });
    }
    const base = m[2] ? "nominatives/" + m[2] : BANDEAU;

    const trouve = await chercher(SOCIETES[prefixe], base);
    if (trouve === null) return new Response("Not found", { status: 404 });

    return new Response(request.method === "HEAD" ? null : trouve.corps, {
      status: 200,
      headers: {
        "Content-Type": trouve.type,
        "Cache-Control": "public, max-age=300",
      },
    });
  },
};
