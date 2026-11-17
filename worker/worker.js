// Cloudflare Worker — URL stable, independante du format de l'image
// -----------------------------------------------------------------
// Les signatures Outlook pointent vers :
//     https://<worker>.workers.dev/n/<prenom>     (signature nominative)
//     https://<worker>.workers.dev/bandeau        (bandeau evenement)
// Le Worker va chercher le fichier sur GitHub en essayant plusieurs
// extensions (gif, jpg, png) et le renvoie avec le bon Content-Type.
// => changer le format d'une image (gif -> jpg...) ne change JAMAIS l'URL
//    collee dans les signatures.
//
// Deploiement : voir README, section "URL stable (Cloudflare Worker)".

const REPO = "https://raw.githubusercontent.com/adorex5278/signature/main/";
const BANDEAU = "banniere_evenement_1108x277";   // nom de base du fichier servi (sans extension)
const TYPES = [                                   // ordre d'essai
  ["gif", "image/gif"],
  ["jpg", "image/jpeg"],
  ["png", "image/png"],
];

async function chercher(base) {
  for (const [ext, type] of TYPES) {
    const r = await fetch(REPO + base + "." + ext, {
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

    const chemin = new URL(request.url).pathname;
    let base = null;
    const m = chemin.match(/^\/n\/([a-z0-9]{1,40})$/);   // prenom : minuscules/chiffres uniquement
    if (m) base = "nominatives/" + m[1];
    else if (chemin === "/bandeau") base = BANDEAU;
    if (base === null) return new Response("Not found", { status: 404 });

    const trouve = await chercher(base);
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
