/** Read RGB-channel design tokens ("59 130 246") as CSS colors for canvas/WebGL use. */
export const token = (name: string, alpha = 1) => {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim();
  const [r, g, b] = raw.split(/\s+/).map(Number);
  return alpha === 1 ? `rgb(${r}, ${g}, ${b})` : `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

/** Current resolved theme, updated when html[data-theme] changes. */
export const useResolvedTheme = () => {
  const theme = ref<"light" | "dark">("dark");
  let observer: MutationObserver | undefined;
  onMounted(() => {
    const read = () => (theme.value = document.documentElement.dataset.theme === "light" ? "light" : "dark");
    read();
    observer = new MutationObserver(read);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  });
  onUnmounted(() => observer?.disconnect());
  return theme;
};

/** Depth stops (km) for the sequential fm-* ramp: shallow = strongest. */
export const DEPTH_STOPS: [number, string][] = [
  [0, "fm-100"],
  [15, "fm-300"],
  [35, "fm-500"],
  [70, "fm-700"],
];

/** Linear interpolation along DEPTH_STOPS, returned as a CSS rgb() color. */
export const depthColor = (km: number | null) => {
  const d = km ?? 10;
  const stops = DEPTH_STOPS.map(([k, t]) => [k, rgbOf(t)] as const);
  if (d <= stops[0][0]) return toCss(stops[0][1]);
  for (let i = 1; i < stops.length; i++) {
    const [k1, c1] = stops[i];
    const [k0, c0] = stops[i - 1];
    if (d <= k1) {
      const t = (d - k0) / (k1 - k0);
      return toCss(c0.map((v, j) => v + t * (c1[j] - v)) as [number, number, number]);
    }
  }
  return toCss(stops[stops.length - 1][1]);
};

const rgbOf = (name: string) =>
  getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim().split(/\s+/).map(Number) as [number, number, number];
const toCss = ([r, g, b]: [number, number, number]) => `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;

// Circle radius (px) by magnitude: exponential (base 1.6) between stops, used by the map and its legend.
const RADIUS_STOPS: [number, number][] = [[1, 2.5], [4, 6], [6, 12], [8, 26]];
export const magRadius = (mag: number | null) => {
  const m = Math.min(8, Math.max(1, mag ?? 2));
  const i = Math.max(0, Math.min(RADIUS_STOPS.length - 2, RADIUS_STOPS.findIndex(([x]) => x >= m) - 1));
  const [[x0, y0], [x1, y1]] = [RADIUS_STOPS[i], RADIUS_STOPS[i + 1]];
  const t = (Math.pow(1.6, m - x0) - 1) / (Math.pow(1.6, x1 - x0) - 1);
  return y0 + t * (y1 - y0);
};
