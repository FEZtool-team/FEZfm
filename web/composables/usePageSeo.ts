// Per-page SEO: canonical URL, Open Graph and Twitter tags, all absolute.
// The origin comes from runtimeConfig.public.siteUrl (NUXT_PUBLIC_SITE_URL).
// Same shape as FEZhome's composable of the same name.

export interface PageSeo {
  /** Route path, e.g. "/" or "/archive/". A trailing slash is added if missing. */
  path: string;
  title: string;
  description: string;
  /** Path under public/, e.g. "/og/fezfm.png" (1200×630). */
  image?: string;
  imageAlt?: string;
  type?: "website" | "article";
  /** Keep the page out of search results (thin pages); links are still followed. */
  noindex?: boolean;
}

/** Absolute URL on this site for a path. */
export const useAbsoluteUrl = () => {
  const { siteUrl } = useRuntimeConfig().public;
  return (path: string) => (/^https?:\/\//.test(path) ? path : new URL(path, siteUrl).href);
};

export const usePageSeo = (seo: MaybeRefOrGetter<PageSeo>) => {
  const absolute = useAbsoluteUrl();
  const page = computed(() => toValue(seo));
  const url = computed(() => absolute(page.value.path.endsWith("/") ? page.value.path : `${page.value.path}/`));
  const image = computed(() => absolute(page.value.image ?? "/og/fezfm.png"));

  useHead({ link: [{ rel: "canonical", href: url }] });
  useSeoMeta({
    title: () => page.value.title,
    description: () => page.value.description,
    robots: () => (page.value.noindex ? "noindex, follow" : undefined),
    ogType: () => page.value.type ?? "website",
    ogUrl: url,
    ogTitle: () => page.value.title,
    ogDescription: () => page.value.description,
    ogImage: image,
    ogImageWidth: 1200,
    ogImageHeight: 630,
    ogImageAlt: () => page.value.imageAlt ?? "FEZfm: earthquake and fault-zone monitor",
    twitterCard: "summary_large_image",
    twitterTitle: () => page.value.title,
    twitterDescription: () => page.value.description,
    twitterImage: image,
  });
};
