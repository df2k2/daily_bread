import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getDevotionalsFor, slugFromId, t, url } from "../../lib/i18n";

export async function GET(context: APIContext) {
  const lang = "pt" as const;
  const sorted = await getDevotionalsFor(lang);
  const strings = t(lang);
  return rss({
    title: strings.feed_title,
    description: strings.site_description,
    site: context.site!,
    items: sorted.map((d) => ({
      title: d.data.title,
      link: url(lang, slugFromId(d.id)),
      pubDate: d.data.date,
      description: `${d.data.reference} (${d.data.translation})`,
    })),
  });
}
