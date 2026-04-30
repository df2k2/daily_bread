import type { CollectionEntry } from "astro:content";
import type { BrowserEntry } from "../components/ArchiveBrowser";
import { entryUrl, shortDate, slugFromId, type Lang } from "./i18n";

export function serializeEntries(
  entries: CollectionEntry<"devotionals">[],
  lang: Lang,
): BrowserEntry[] {
  return entries.map((e) => {
    const date = e.data.date;
    return {
      slug: slugFromId(e.id),
      title: e.data.title,
      reference: e.data.reference,
      book: e.data.book ?? e.data.reference.split(/\s+\d/)[0]?.trim() ?? e.data.reference,
      translation: e.data.translation,
      slot: e.data.slot,
      date: shortDate(date, lang),
      year: String(date.getFullYear()),
      month: String(date.getMonth() + 1).padStart(2, "0"),
      tags: e.data.tags ?? [],
      excerpt: e.data.excerpt ?? "",
      imageUrl: e.data.image ? e.data.image.src : null,
      url: entryUrl(lang, e),
    };
  });
}
