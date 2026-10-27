// sitemap.xml, prerendered next to the pages (see nitro.prerender.routes).
// The static pages plus one page per archive month, read from the files
// `fezfm export` wrote to public/data.
import { readFile } from "node:fs/promises";

interface MonthInfo {
  month: string;
  events: number;
}

// Same threshold as MIN_INDEXED_EVENTS in composables/useArchive.ts: thinner months are noindex.
const MIN_INDEXED_EVENTS = 100;

// The collector re-reads the last 2 days, so a month's events can still change
// until 2 days after it ends; after that its page stays the same.
const SETTLE_MS = 2 * 86400e3;

const readJson = async (path: string) => {
  try {
    return JSON.parse(await readFile(path, "utf8"));
  } catch {
    return null;
  }
};

export default defineEventHandler(async (event) => {
  const { dataDir, public: pub } = useRuntimeConfig(event);
  const site = pub.siteUrl;
  const latest = await readJson(`${dataDir}/latest.json`);
  const archive = await readJson(`${dataDir}/archive/index.json`);
  const updated: string | undefined = latest?.generated_at;

  const urls: { path: string; lastmod?: string }[] = [
    { path: "/", lastmod: updated },
    { path: "/map/", lastmod: updated },
    { path: "/archive/", lastmod: archive?.generated_at },
    { path: "/downloads/", lastmod: updated },
    { path: "/about/" },
  ];
  for (const m of (archive?.months ?? []) as MonthInfo[]) {
    if (m.events < MIN_INDEXED_EVENTS) continue;
    const [y, mo] = m.month.split("-").map(Number);
    const settled = Date.UTC(y, mo, 1) + SETTLE_MS;
    const generated = Date.parse(archive.generated_at);
    const lastmod = new Date(Math.min(settled, generated)).toISOString().replace(/\.\d{3}Z$/, "Z");
    urls.push({ path: `/archive/${m.month}/`, lastmod });
  }

  const body = urls
    .map((u) => `  <url><loc>${site}${u.path}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ""}</url>`)
    .join("\n");
  setHeader(event, "content-type", "application/xml; charset=utf-8");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`;
});
