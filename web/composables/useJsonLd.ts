// Adds a schema.org JSON-LD block to the page head. Pass the nodes of one
// @graph; entities shared with FEZhome are referenced by the @id values in
// data/schema.ts.

export const useJsonLd = (nodes: MaybeRefOrGetter<Record<string, unknown>[]>) => {
  useHead({
    script: [
      {
        type: "application/ld+json",
        // "<" is escaped so no string in the data can close the script tag.
        innerHTML: () =>
          JSON.stringify({ "@context": "https://schema.org", "@graph": toValue(nodes) }).replace(/</g, "\\u003c"),
      },
    ],
  });
};
