// Reads a file that `fezfm export` wrote to public/data. While prerendering it
// comes from disk, so the HTML carries real content and the payload hands the
// result to the client. Where a page is rendered in the browser (navigation in
// `nuxt dev`), the file is fetched instead. `pick` keeps the payload small.

export const usePublicData = <T, R = T>(key: string, file: string, pick: (raw: T) => R = (raw) => raw as unknown as R) => {
  // Read before the handler awaits anything, while the Nuxt context is set.
  const cfg = useRuntimeConfig();
  const dataDir = import.meta.server ? (cfg.dataDir as string) : "";
  const base = cfg.app.baseURL;

  return useAsyncData(key, async () => {
    if (import.meta.server) {
      const { readFile } = await import("node:fs/promises");
      return pick(JSON.parse(await readFile(`${dataDir}/${file}`, "utf8")));
    }
    return pick(await $fetch<T>(`${base}data/${file}`));
  });
};
