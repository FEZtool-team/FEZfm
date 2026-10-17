<template>
  <div class="relative overflow-hidden rounded-lg border border-glass bg-fez-950">
    <div ref="el" class="fezfm-map h-full w-full" role="region" aria-label="Earthquake map" />

    <div class="absolute left-3 top-3 z-[500] flex gap-1 rounded-full border border-glass bg-fez-900/85 p-1 text-xs backdrop-blur">
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

    <QuakeLegend class="absolute bottom-3 left-3 z-[500]" />
  </div>
</template>

<script setup lang="ts">
import type * as Leaflet from "leaflet";
import type { Quake } from "~/composables/useQuakes";

const props = withDefaults(defineProps<{ events: Quake[]; selected?: string | null; initialView?: "world" | "iran" }>(), {
  selected: null,
  initialView: "world",
});
const emit = defineEmits<{ select: [id: string] }>();

const views = {
  world: { label: "World", center: [20, 40] as [number, number], zoom: 1.5 },
  iran: { label: "Iran", center: [32.5, 53.5] as [number, number], zoom: 5 },
};
const view = ref<keyof typeof views>(props.initialView);

const el = ref<HTMLDivElement>();
const theme = useResolvedTheme();
const base = useRuntimeConfig().app.baseURL;
const now = useState<number>("now");

let L: typeof Leaflet | undefined;
let map: Leaflet.Map | undefined;
let land: Leaflet.GeoJSON | undefined;
let gem: Leaflet.GeoJSON | undefined;
let zones: Leaflet.GeoJSON | undefined;
let quakes: Leaflet.LayerGroup | undefined;
const markers = new Map<string, Leaflet.CircleMarker>();


const escapeHtml = (s: string) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const popupHtml = (q: Quake) => {
  const links = q.sources
    .map((s) =>
      s.url
        ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener">${SOURCE_LABELS[s.name] ?? s.name}</a>`
        : (SOURCE_LABELS[s.name] ?? s.name)
    )
    .join(" · ");
  return `<p class="fezfm-popup-title">${escapeHtml(q.headline)}</p>
    <p class="fezfm-popup-meta">${utc(q.t)} · ${ago(q.t, now.value)}${q.depth != null ? ` · depth ${q.depth.toFixed(0)} km` : ""}</p>
    <p class="fezfm-popup-links">${links}</p>`;
};

// Self-hosted basemap (Natural Earth countries) so the map needs no tile service or key.
const landStyle = () => ({ color: token("fez-600"), weight: 0.6, opacity: 0.9, fillColor: token("fez-800"), fillOpacity: 1 });
const gemStyle = () => ({ color: token("fez-400"), weight: 0.8, opacity: 0.45 });
const zoneStyle = () => ({ color: token("fm-400"), weight: 2, opacity: 0.8, dashArray: "6 4" });
const quakeStyle = (q: Quake, selected: boolean) => ({
  radius: magRadius(q.mag),
  fillColor: depthColor(q.depth),
  fillOpacity: 0.9,
  color: token("fez-50", selected ? 1 : 0.85),
  weight: selected ? 2.5 : 0.75,
});

const drawQuakes = () => {
  if (!L || !map) return;
  quakes?.remove();
  markers.clear();
  quakes = L.layerGroup();
  // Small first so large events draw on top.
  const sorted = [...props.events].sort((a, b) => (a.mag ?? 0) - (b.mag ?? 0));
  for (const q of sorted) {
    if (q.sig) {
      L.circleMarker([q.lat, q.lon], {
        radius: magRadius(q.mag) * 1.9,
        fillColor: token("fm-500"),
        fillOpacity: 0.16,
        color: token("fm-400", 0.6),
        weight: 1,
        interactive: false,
      }).addTo(quakes);
    }
    const m = L.circleMarker([q.lat, q.lon], quakeStyle(q, q.id === props.selected));
    m.on("click", () => emit("select", q.id));
    m.addTo(quakes);
    markers.set(q.id, m);
  }
  quakes.addTo(map);
};

const restyle = () => {
  land?.setStyle(landStyle);
  gem?.setStyle(gemStyle);
  zones?.setStyle(zoneStyle);
  drawQuakes();
};

const goTo = (key: keyof typeof views) => {
  view.value = key;
  map?.flyTo(views[key].center, views[key].zoom, { duration: 0.8 });
};

const toggleZoneLabels = () => el.value?.classList.toggle("fezfm-zoom-low", (map?.getZoom() ?? 0) < 5);

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
    'Countries: <a href="https://www.naturalearthdata.com/">Natural Earth</a> · Faults: <a href="https://github.com/GEMScienceTools/gem-global-active-faults">GEM</a>'
  );

  map.on("zoomend", toggleZoneLabels);
  toggleZoneLabels();
  drawQuakes();

  const [landData, gemData, zoneData] = await Promise.all([
    fetch(`${base}layers/countries.geojson`).then((r) => r.json()),
    fetch(`${base}layers/gem_active_faults.geojson`).then((r) => r.json()),
    fetch(`${base}data/fault_zones.geojson`).then((r) => r.json()),
  ]);
  land = L.geoJSON(landData, { style: landStyle, interactive: false }).addTo(map);
  gem = L.geoJSON(gemData, { style: gemStyle, interactive: false }).addTo(map);
  zones = L.geoJSON(zoneData, {
    style: zoneStyle,
    onEachFeature: (f, layer) =>
      layer.bindTooltip(f.properties.name, { permanent: true, direction: "center", className: "fezfm-zone-label" }),
  }).addTo(map);
  gem.bringToBack();
  land.bringToBack();
  quakes?.eachLayer((l) => (l as Leaflet.CircleMarker).bringToFront());
});

onUnmounted(() => map?.remove());

watch(() => props.events, drawQuakes);

watch(
  () => props.selected,
  (id, prev) => {
    if (!map || !L) return;
    const old = prev ? props.events.find((e) => e.id === prev) : undefined;
    if (old) markers.get(old.id)?.setStyle(quakeStyle(old, false));
    const q = props.events.find((e) => e.id === id);
    if (!q) return;
    markers.get(q.id)?.setStyle(quakeStyle(q, true)).bringToFront();
    map.flyTo([q.lat, q.lon], Math.max(map.getZoom(), q.region ? 6 : 4), { duration: 0.8 });
    L.popup({ offset: [0, -4], maxWidth: 280 }).setLatLng([q.lat, q.lon]).setContent(popupHtml(q)).openOn(map);
  }
);

watch(theme, restyle);
</script>
