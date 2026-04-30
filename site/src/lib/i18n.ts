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
    of_entries: (n: number, total: number) => `${n} of ${total} ${total === 1 ? "entry" : "entries"}`,
    site_title: "Daily Bread",
    site_description: "A daily Bible devotional in English and Portuguese.",
    feed_title: "Daily Bread",
  },
  pt: {
    archive: "Arquivo",
    archive_heading: "Arquivo",
    no_devotionals: "Ainda não há devocionais.",
    placeholder_hint: "Execute python -m scripts.generate_devotional para criar o primeiro.",
    search_placeholder: "Pesquisar título, passagem ou texto...",
    of_entries: (n: number, total: number) => `${n} de ${total} ${total === 1 ? "entrada" : "entradas"}`,
    site_title: "Pão Diário",
    site_description: "Um devocional bíblico diário em português e inglês.",
    feed_title: "Pão Diário",
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
  return id.replace(/\.(en|pt)$/, "");
}

export function entryUrl(lang: Lang, slug: string): string {
  return url(lang, slug);
}

export async function getDevotionalsFor(
  lang: Lang,
): Promise<CollectionEntry<"devotionals">[]> {
  const all = await getCollection("devotionals", (d) => d.data.lang === lang);
  return all.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
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
