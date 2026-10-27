// schema.org entities for JSON-LD (see composables/useJsonLd.ts). The FEZtool
// organization and the FEZfm app are declared on feztool.com; this site
// references them by @id, so keep those values unchanged. Every fact here
// must match what the pages show; nothing is added for search engines only.

export const ORGANIZATION_ID = "https://feztool.com/#organization";
export const APP_ID = "https://feztool.com/fezfm/#software";

/** Minimal copy of FEZhome's Organization, so each graph names its publisher. */
export const organization = {
  "@type": "Organization",
  "@id": ORGANIZATION_ID,
  name: "FEZtool",
  url: "https://feztool.com/",
};

const org = { "@id": ORGANIZATION_ID };

export const website = (site: string) => ({
  "@type": "WebSite",
  "@id": `${site}/#website`,
  name: "FEZfm",
  url: `${site}/`,
  inLanguage: "en",
  description: "Earthquake and fault-zone monitor: USGS and EMSC reports for Iran and worldwide, merged every 30 minutes.",
  publisher: org,
  about: { "@id": APP_ID },
});

const catalog = (name: string, url: string, publisher: string, alternateName: string) => ({
  "@type": "CreativeWork",
  name,
  url,
  publisher: { "@type": "Organization", name: publisher, alternateName },
});

/** The catalogs FEZfm merges (see the About page). */
export const SOURCES = {
  usgs: catalog("USGS FDSN event service", "https://earthquake.usgs.gov/fdsnws/event/1/", "United States Geological Survey", "USGS"),
  emsc: catalog("EMSC FDSN event service", "https://www.seismicportal.eu/fdsnws/event/1/", "European-Mediterranean Seismological Centre", "EMSC"),
  irsc: catalog("IRSC bulletin", "http://irsc.ut.ac.ir/", "Iranian Seismological Center, Institute of Geophysics, University of Tehran", "IRSC"),
};

/** Every event in the Iran box is kept; elsewhere M2.5 and above (collector/fezfm/model.py). */
export const spatialCoverage = [
  { "@type": "Place", name: "Iran and adjacent areas", geo: { "@type": "GeoShape", box: "24 42 41 64" } },
  { "@type": "Place", name: "Worldwide" },
];

export const FORMATS: Record<string, string> = {
  csv: "text/csv",
  json: "application/json",
  geojson: "application/geo+json",
  parquet: "application/vnd.apache.parquet",
  duckdb: "application/octet-stream",
  xml: "application/atom+xml",
};

export const download = (contentUrl: string, name: string) => ({
  "@type": "DataDownload",
  name,
  contentUrl,
  encodingFormat: FORMATS[contentUrl.split(".").pop() ?? ""] ?? "application/octet-stream",
});

/** Properties every FEZfm dataset shares. No license is stated until the data terms are decided. */
export const datasetBase = (sources: (keyof typeof SOURCES)[] = ["usgs", "emsc"]) => ({
  creator: org,
  publisher: org,
  isAccessibleForFree: true,
  inLanguage: "en",
  keywords: ["earthquakes", "seismology", "Iran", "USGS", "EMSC"],
  isBasedOn: sources.map((s) => SOURCES[s]),
  spatialCoverage,
  creditText: "USGS, EMSC, IRSC (University of Tehran) for earlier events, and FEZfm",
});

export const breadcrumbs = (site: string, trail: { name: string; path: string }[]) => ({
  "@type": "BreadcrumbList",
  itemListElement: trail.map((step, i) => ({
    "@type": "ListItem",
    position: i + 1,
    name: step.name,
    item: `${site}${step.path}`,
  })),
});
