export type ThemePreference = "system" | "light" | "dark";

// Keep in sync with the inline script in nuxt.config.ts.
const STORAGE_KEY = "fez-theme";
const order: ThemePreference[] = ["system", "light", "dark"];

let media: MediaQueryList | undefined;

const resolve = (pref: ThemePreference) =>
  pref === "system" ? (media?.matches ? "light" : "dark") : pref;

const apply = (pref: ThemePreference) => {
  document.documentElement.dataset.theme = resolve(pref);
};

/** Theme preference shared by every toggle; "system" follows the OS setting. */
export const useTheme = () => {
  const preference = useState<ThemePreference>("theme-preference", () => "system");

  const set = (pref: ThemePreference) => {
    preference.value = pref;
    try {
      if (pref === "system") localStorage.removeItem(STORAGE_KEY);
      else localStorage.setItem(STORAGE_KEY, pref);
    } catch {
      // Storage can be blocked; the choice then lasts for this page view.
    }
    apply(pref);
  };

  const cycle = () => set(order[(order.indexOf(preference.value) + 1) % order.length]);

  onMounted(() => {
    if (media) return;
    media = window.matchMedia("(prefers-color-scheme: light)");
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "light" || saved === "dark") preference.value = saved;
    } catch {}
    media.addEventListener("change", () => {
      if (preference.value === "system") apply("system");
    });
  });

  return { preference, set, cycle };
};
