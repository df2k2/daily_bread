import type { CollectionEntry } from "astro:content";
import { getCollection } from "astro:content";

export type Lang = "en" | "pt";

export const PRIMARY: Lang = "en";

export const LANGUAGES: { code: Lang; label: string; flag: string }[] = [
  { code: "en", label: "English", flag: "EN" },
  { code: "pt", label: "Português", flag: "PT" },
];

const STRINGS = {
  en: {
    archive: "Archive",
    archive_heading: "Archive",
    no_devotionals: "No devotionals yet.",
    placeholder_hint: "Run python -m scripts.generate_devotional to create the first one.",
    search_placeholder: "Search title, passage, or text...",
    site_title: "Daily Bread",
    site_description: "A daily Bible devotional in English and Portuguese.",
    feed_title: "Daily Bread",
    today: "Today's Posts",
    recent: "Recent Posts",
    read_post: "Read this post",
    view: "View",
    filters: "Filters",
    year: "Year",
    month: "Month",
    book: "Book",
    tags: "Tags",
    clear_filters: "Clear filters",
    count_of: "of",
    count_entry: "entry",
    count_entries: "entries",
    showing: (n: number) => `Showing ${n}`,
    tagged_with: (tag: string) => `Tagged: ${tag}`,
    no_results: "No matching entries.",
  },
  pt: {
    archive: "Arquivo",
    archive_heading: "Arquivo",
    no_devotionals: "Ainda não há devocionais.",
    placeholder_hint: "Execute python -m scripts.generate_devotional para criar o primeiro.",
    search_placeholder: "Pesquisar título, passagem ou texto...",
    site_title: "Pão Diário",
    site_description: "Um devocional bíblico diário em português e inglês.",
    feed_title: "Pão Diário",
    today: "Posts de Hoje",
    recent: "Posts Recentes",
    read_post: "Ler este post",
    view: "Ver",
    filters: "Filtros",
    year: "Ano",
    month: "Mês",
    book: "Livro",
    tags: "Tópicos",
    clear_filters: "Limpar filtros",
    count_of: "de",
    count_entry: "entrada",
    count_entries: "entradas",
    showing: (n: number) => `Mostrando ${n}`,
    tagged_with: (tag: string) => `Tópico: ${tag}`,
    no_results: "Nenhuma entrada encontrada.",
  },
} as const;

export function t(lang: Lang) {
  return STRINGS[lang];
}

export function basePath(): string {
  return import.meta.env.BASE_URL.replace(/\/$/, "");
}

export function url(lang: Lang, path = ""): string {
  const prefix = lang === PRIMARY ? "" : `/${lang}`;
  const clean = path.startsWith("/") ? path : path ? `/${path}` : "";
  return `${basePath()}${prefix}${clean || "/"}`;
}

export function slugFromId(id: string): string {
  return id.replace(/-(en|pt)$/, "");
}

export function entryUrl(lang: Lang, entry: CollectionEntry<"devotionals">): string {
  return url(lang, slugFromId(entry.id));
}

export function tagSlug(tag: string): string {
  const lowered = tag.toLowerCase().trim();
  return lowered
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function tagUrl(lang: Lang, tag: string): string {
  return url(lang, `/tags/${tagSlug(tag)}`);
}

export async function getDevotionalsFor(
  lang: Lang,
): Promise<CollectionEntry<"devotionals">[]> {
  const all = await getCollection("devotionals", (d) => d.data.lang === lang);
  return all.sort((a, b) => {
    const aTime = (a.data.datetime ?? a.data.date).getTime();
    const bTime = (b.data.datetime ?? b.data.date).getTime();
    return bTime - aTime;
  });
}

export function localizedDate(date: Date, lang: Lang): string {
  const locale = lang === "pt" ? "pt-BR" : "en-US";
  return date.toLocaleDateString(locale, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function shortDate(date: Date, lang: Lang): string {
  const locale = lang === "pt" ? "pt-BR" : "en-US";
  return date.toLocaleDateString(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function isSameLocalDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

const MONTH_NAMES = {
  en: [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ],
  pt: [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
  ],
} as const;

export function monthName(monthIndex: number, lang: Lang): string {
  return MONTH_NAMES[lang][monthIndex];
}

export type Aggregate = { value: string; label: string; count: number };

export function aggregateBy(
  entries: CollectionEntry<"devotionals">[],
  pick: (e: CollectionEntry<"devotionals">) => string[],
  label: (key: string) => string = (k) => k,
): Aggregate[] {
  const counts = new Map<string, number>();
  for (const e of entries) {
    for (const k of pick(e)) {
      counts.set(k, (counts.get(k) ?? 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, label: label(value), count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}
