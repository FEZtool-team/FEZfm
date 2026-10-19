<template>
  <!-- isolate: Leaflet's panes use z-index 200-700; keep them under the fixed navbar. -->
  <div class="relative isolate overflow-hidden rounded-lg border border-glass bg-fez-950">
    <div ref="el" class="fezfm-map h-full w-full" role="region" aria-label="Earthquake map" />

    <div class="absolute left-3 top-3 z-[1000] flex gap-1 rounded-full border border-glass bg-fez-900/85 p-1 text-xs backdrop-blur">
      <button
        v-for="(v, key) in views"
        :key="key"
        type="button"
        class="rounded-full px-3 py-1 transition-colors"
        :class="view === key ? 'bg-fez-50 text-fez-900' : 'text-fez-300 hover:text-fez-50'"
        @click="goTo(key)"
      >
        {{ v.label }}
      </button>
    </div>

    <QuakeLegend v-model:layers="layers" :scale="zoomScale(zoom)" class="absolute bottom-3 left-3 z-[1000]" />
  </div>
</template>

<script setup lang="ts">
import type * as Leaflet from "leaflet";
import type { Quake } from "~/composables/useQuakes";
import type { MapLayers } from "~/composables/useTokens";

const props = withDefaults(defineProps<{ events: Quake[]; selected?: string | null; initialView?: "world" | "iran" }>(), {
  selected: null,
  initialView: "world",
});
const emit = defineEmits<{ select: [id: string] }>();

// World view is centred on the Pacific, the usual choice for global seismicity.
const views = {
  world: { label: "World", center: [15, 150] as [number, number], zoom: 1.5 },
  iran: { label: "Iran", center: [32.5, 53.5] as [number, number], zoom: 5 },
};
const view = ref<keyof typeof views>(props.initialView);
const zoom = ref(views[view.value].zoom);
const layers = ref<MapLayers>({ relief: false, plates: true, faults: true, zones: true });

// Vector layers and markers are drawn three times, one world apart, so the
// Pacific-centred view and panning across the antimeridian show no gaps.
const COPIES = [-360, 0, 360];
// GEBCO tiles: zooms 0-5 worldwide, 6-7 for this box only (collector/scripts/gebco_tiles.py).
const DETAIL_BOX: [[number, number], [number, number]] = [[20, 38], [44, 68]];

const el = ref<HTMLDivElement>();
const theme = useResolvedTheme();
const base = useRuntimeConfig().app.baseURL;
const now = useState<number>("now");

let L: typeof Leaflet | undefined;
let map: Leaflet.Map | undefined;
let quakeRenderer: Leaflet.Canvas | undefined;
let relief: Leaflet.LayerGroup | undefined;
let land: Leaflet.FeatureGroup | undefined;
let gem: Leaflet.FeatureGroup | undefined;
let plates: Leaflet.FeatureGroup | undefined;
let zones: Leaflet.FeatureGroup | undefined;
let quakes: Leaflet.LayerGroup | undefined;
const markers = new Map<string, { q: Quake; dots: Leaflet.CircleMarker[]; halos: Leaflet.CircleMarker[] }>();
// Set when the selection comes from a click on the map, so the map does not fly.
let clickedId: string | null = null;

const escapeHtml = (s: string) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const coord = (v: number, pos: string, neg: string) => `${Math.abs(v).toFixed(2)}° ${v >= 0 ? pos : neg}`;

const popupHtml = (q: Quake) => {
  const links = q.sources
    .map((s) =>
      s.url
        ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${SOURCE_LABELS[s.name] ?? s.name}</a>`
        : (SOURCE_LABELS[s.name] ?? s.name)
    )
    .join(" · ");
  const rows: [string, string][] = [
    ["Time", `${utc(q.t)} · ${ago(q.t, now.value)}`],
    ["Magnitude", q.mag != null ? `${q.mag.toFixed(1)}${q.magType ? ` ${q.magType}` : ""}` : "Unknown"],
    ["Depth", q.depth != null ? `${q.depth.toFixed(1)} km` : "Unknown"],
    ["Location", `${coord(q.lat, "N", "S")}, ${coord(q.lon, "E", "W")}`],
  ];
  if (q.zone) rows.push(["Fault zone", `${zoneLabel(q.zone)}${q.zoneKm != null ? `, ${q.zoneKm} km from trace` : ""}`]);
  rows.push(["Preferred", SOURCE_LABELS[q.src] ?? q.src]);
  const tags = [q.sig && "Significant", q.sequence && "Active sequence", q.region && "Iran region"].filter(Boolean);
  return `<p class="fezfm-popup-title">${escapeHtml(q.headline)}</p>
    <dl class="fezfm-popup-grid">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${escapeHtml(v)}</dd>`).join("")}</dl>
    ${tags.length ? `<p class="fezfm-popup-tags">${tags.map((t) => `<span>${t}</span>`).join("")}</p>` : ""}
    <p class="fezfm-popup-links">Reported by ${links}</p>`;
};

// Over the relief, borders and faults are dark ink; on the plain basemap they use the theme tokens.
const landStyle = () =>
  layers.value.relief
    ? { color: token("map-ink"), weight: 0.5, opacity: 0.45, fill: false }
    : { color: token("fez-600"), weight: 0.6, opacity: 0.9, fill: true, fillColor: token("fez-800"), fillOpacity: 1 };
const gemStyle = () =>
  layers.value.relief ? { color: token("map-ink"), weight: 0.8, opacity: 0.55 } : { color: token("fez-400"), weight: 0.8, opacity: 0.45 };
const plateStyle = (f?: GeoJSON.Feature) => ({
  color: token("map-plate"),
  weight: f?.properties?.subduction ? 1.8 : 1.1,
  opacity: 0.75,
});
const zoneStyle = () => ({ color: token("fm-400"), weight: 2, opacity: 0.8, dashArray: "6 4" });

const radius = (q: Quake) => magRadius(q.mag) * zoomScale(zoom.value);
const quakeStyle = (q: Quake, selected: boolean) => ({
  renderer: quakeRenderer,
  radius: radius(q),
  fillColor: depthColor(q.depth),
  fillOpacity: 0.9,
  color: selected ? token("fez-50") : token("map-ink", 0.85),
  weight: selected ? 2.5 : 0.75,
});
const haloStyle = (q: Quake) => ({
  renderer: quakeRenderer,
  radius: radius(q) * 1.9,
  fillColor: token("fm-500"),
  fillOpacity: 0.16,
  color: token("fm-400", 0.6),
  weight: 1,
  interactive: false,
});

/** Three copies of a GeoJSON layer, one world apart. */
const wrapped = (data: GeoJSON.GeoJsonObject, opts: Leaflet.GeoJSONOptions) =>
  L!.featureGroup(COPIES.map((off) => L!.geoJSON(data, { ...opts, coordsToLatLng: (c) => L!.latLng(c[1], c[0] + off) })));

const drawQuakes = () => {
  if (!L || !map) return;
  quakes?.remove();
  markers.clear();
  quakes = L.layerGroup();
  // Small first so large events draw on top.
  const sorted = [...props.events].sort((a, b) => (a.mag ?? 0) - (b.mag ?? 0));
  for (const q of sorted) {
    const entry = { q, dots: [] as Leaflet.CircleMarker[], halos: [] as Leaflet.CircleMarker[] };
    for (const off of COPIES) {
      if (q.sig) entry.halos.push(L.circleMarker([q.lat, q.lon + off], haloStyle(q)).addTo(quakes));
      const m = L.circleMarker([q.lat, q.lon + off], quakeStyle(q, q.id === props.selected));
      m.bindTooltip(q.headline, { direction: "top", offset: [0, -4], className: "fezfm-quake-tip" });
      m.on("click", () => {
        clickedId = q.id;
        if (q.id === props.selected) openPopup(q);
        else emit("select", q.id);
      });
      entry.dots.push(m.addTo(quakes));
    }
    markers.set(q.id, entry);
  }
  quakes.addTo(map);
};

const resize = () => {
  for (const { q, dots, halos } of markers.values()) {
    for (const d of dots) d.setRadius(radius(q));
    for (const h of halos) h.setRadius(radius(q) * 1.9);
  }
};

/** Longitude of the copy of `lon` nearest the map centre. */
const nearLon = (lon: number) => {
  const c = map!.getCenter().lng;
  return lon + Math.round((c - lon) / 360) * 360;
};

const openPopup = (q: Quake) => {
  if (!map || !L) return;
  L.popup({ offset: [0, -4], maxWidth: 300, minWidth: 220, autoPanPaddingTopLeft: [16, 140] }).setLatLng([q.lat, nearLon(q.lon)]).setContent(popupHtml(q)).openOn(map);
};

const applyLayers = () => {
  if (!map) return;
  const show = (layer: Leaflet.Layer | undefined, on: boolean) => layer && (on ? layer.addTo(map!) : layer.remove());
  show(relief, layers.value.relief);
  show(plates, layers.value.plates);
  show(gem, layers.value.faults);
  show(zones, layers.value.zones);
  land?.setStyle(landStyle);
  gem?.setStyle(gemStyle);
};

const restyle = () => {
  land?.setStyle(landStyle);
  gem?.setStyle(gemStyle);
  plates?.setStyle(plateStyle as Leaflet.StyleFunction);
  zones?.setStyle(zoneStyle);
  drawQuakes();
};

const goTo = (key: keyof typeof views) => {
  view.value = key;
  map?.flyTo(views[key].center, views[key].zoom, { duration: 0.8 });
};

const onZoom = () => {
  zoom.value = map?.getZoom() ?? zoom.value;
  el.value?.classList.toggle("fezfm-zoom-low", zoom.value < 5);
  resize();
};

onMounted(async () => {
  L = (await import("leaflet")).default;
  map = L.map(el.value!, {
    preferCanvas: true,
    zoomSnap: 0.5,
    worldCopyJump: true,
    zoomControl: false,
    minZoom: 1,
    maxZoom: 9,
  }).setView(views[view.value].center, views[view.value].zoom);
  L.control.zoom({ position: "topright" }).addTo(map);
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution(
    [
      'Relief: <a href="https://www.gebco.net/">GEBCO Grid</a>',
      'Plates: <a href="https://doi.org/10.1029/2001GC000252">Bird 2003</a>',
      'Faults: <a href="https://github.com/GEMScienceTools/gem-global-active-faults">GEM</a>',
      'Countries: <a href="https://www.naturalearthdata.com/">Natural Earth</a>',
    ].join(" · ")
  );

  // One canvas per pane keeps the drawing order fixed whatever loads first.
  for (const [name, z] of [["land", 250], ["faults", 410], ["plates", 420], ["zones", 430], ["quakes", 450]] as const) {
    map.createPane(name).style.zIndex = String(z);
  }
  quakeRenderer = L.canvas({ pane: "quakes", tolerance: 6 });

  // Self-hosted GEBCO relief, so the map needs no tile service (third-party tiles fail from Iran).
  const tiles = `${base}layers/gebco/{z}/{x}/{y}.webp`;
  relief = L.layerGroup([
    L.tileLayer(tiles, { maxNativeZoom: 5, maxZoom: 9 }),
    L.tileLayer(tiles, { minZoom: 6, minNativeZoom: 6, maxNativeZoom: 7, maxZoom: 9, bounds: L.latLngBounds(DETAIL_BOX) }),
  ]);

  map.on("zoomend", onZoom);
  onZoom();
  drawQuakes();

  const [landData, gemData, plateData, zoneData] = await Promise.all(
    ["layers/countries.geojson", "layers/gem_active_faults.geojson", "layers/plate_boundaries.geojson", "data/fault_zones.geojson"].map((f) =>
      fetch(`${base}${f}`).then((r) => r.json())
    )
  );
  if (!map) return;
  land = wrapped(landData, { pane: "land", style: landStyle, interactive: false }).addTo(map);
  gem = wrapped(gemData, { pane: "faults", style: gemStyle, interactive: false });
  plates = wrapped(plateData, { pane: "plates", style: plateStyle as Leaflet.StyleFunction, interactive: false });
  zones = wrapped(zoneData, {
    pane: "zones",
    style: zoneStyle,
    onEachFeature: (f, layer) =>
      layer.bindTooltip(f.properties.name, { permanent: true, direction: "center", className: "fezfm-zone-label" }),
  });
  applyLayers();
});

onUnmounted(() => {
  map?.remove();
  map = undefined;
});

watch(() => props.events, drawQuakes);
watch(layers, applyLayers, { deep: true });

watch(
  () => props.selected,
  (id, prev) => {
    if (!map || !L) return;
    const old = prev ? markers.get(prev) : undefined;
    old?.dots.forEach((d) => d.setStyle(quakeStyle(old.q, false)));
    const entry = id ? markers.get(id) : undefined;
    const fromMap = clickedId === id;
    clickedId = null;
    if (!entry) return;
    const q = entry.q;
    entry.dots.forEach((d) => d.setStyle(quakeStyle(q, true)).bringToFront());
    if (!fromMap) map.flyTo([q.lat, nearLon(q.lon)], Math.max(map.getZoom(), q.region ? 6 : 4), { duration: 0.8 });
    openPopup(q);
  }
);

watch(theme, restyle);
</script>
