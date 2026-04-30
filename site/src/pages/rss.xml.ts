import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import type { APIContext } from "astro";

export async function GET(context: APIContext) {
  const all = await getCollection("devotionals");
  const sorted = all.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
  return rss({
    title: "Daily Bread",
    description: "A daily Bible devotional.",
    site: context.site!,
    items: sorted.map((d) => ({
      title: d.data.title,
      link: `/${d.id.replace(/\.md$/, "")}`,
      pubDate: d.data.date,
      description: `${d.data.reference} (${d.data.translation})`,
    })),
  });
}
