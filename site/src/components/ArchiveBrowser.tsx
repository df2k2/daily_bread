import { useEffect, useMemo, useState } from "react";
import { Input } from "rizzui/input";
import { Badge } from "rizzui/badge";
import { Title, Text } from "rizzui/typography";

export interface BrowserEntry {
  slug: string;
  title: string;
  reference: string;
  book: string;
  translation: string;
  slot: string;
  date: string;
  year: string;
  month: string;
  tags: string[];
  excerpt: string;
  imageUrl: string | null;
  url: string;
}

interface Props {
  entries: BrowserEntry[];
  lang: "en" | "pt";
  searchPlaceholder: string;
  countLabels: {
    of: string;
    entry: string;
    entries: string;
  };
  noResultsLabel: string;
  viewLabel: string;
  monthNames: string[];
  tagPathPrefix: string;
}

type Filters = {
  q: string;
  year: string;
  month: string;
  book: string;
  tag: string;
};

const EMPTY: Filters = { q: "", year: "", month: "", book: "", tag: "" };

function readParams(): Filters {
  if (typeof window === "undefined") return EMPTY;
  const p = new URLSearchParams(window.location.search);
  return {
    q: p.get("q") ?? "",
    year: p.get("year") ?? "",
    month: p.get("month") ?? "",
    book: p.get("book") ?? "",
    tag: p.get("tag") ?? "",
  };
}

function writeParams(filters: Filters) {
  if (typeof window === "undefined") return;
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) if (v) p.set(k, v);
  const qs = p.toString();
  const url = qs
    ? `${window.location.pathname}?${qs}`
    : window.location.pathname;
  window.history.replaceState(null, "", url);
}

export default function ArchiveBrowser({
  entries,
  lang,
  searchPlaceholder,
  countLabels,
  noResultsLabel,
  viewLabel,
  monthNames,
  tagPathPrefix,
}: Props) {
  const [filters, setFilters] = useState<Filters>(EMPTY);

  useEffect(() => {
    setFilters(readParams());
  }, []);

  useEffect(() => {
    writeParams(filters);
  }, [filters]);

  const results = useMemo(() => {
    const q = filters.q.trim().toLowerCase();
    return entries.filter((e) => {
      if (filters.year && e.year !== filters.year) return false;
      if (filters.month && e.month !== filters.month) return false;
      if (filters.book && e.book.toLowerCase() !== filters.book.toLowerCase()) return false;
      if (filters.tag) {
        const matches = e.tags.some((t) => t.toLowerCase() === filters.tag.toLowerCase());
        if (!matches) return false;
      }
      if (q) {
        const hay = `${e.title} ${e.reference} ${e.excerpt} ${e.tags.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [entries, filters]);

  const activeChips: { key: keyof Filters; label: string }[] = [];
  if (filters.year) activeChips.push({ key: "year", label: filters.year });
  if (filters.month) {
    const idx = parseInt(filters.month, 10) - 1;
    activeChips.push({ key: "month", label: monthNames[idx] ?? filters.month });
  }
  if (filters.book) activeChips.push({ key: "book", label: filters.book });
  if (filters.tag) activeChips.push({ key: "tag", label: `#${filters.tag}` });

  return (
    <div className="flex flex-col gap-4">
      <Input
        type="search"
        placeholder={searchPlaceholder}
        value={filters.q}
        onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
        clearable
        onClear={() => setFilters((f) => ({ ...f, q: "" }))}
      />

      {activeChips.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {activeChips.map((chip) => (
            <button
              key={`${chip.key}:${chip.label}`}
              type="button"
              onClick={() => setFilters((f) => ({ ...f, [chip.key]: "" }))}
              className="inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs hover:bg-(--muted)"
              style={{ borderColor: "var(--border)" }}
            >
              <span>{chip.label}</span>
              <span aria-hidden>×</span>
            </button>
          ))}
        </div>
      )}

      <Text className="!text-xs" style={{ color: "var(--muted-foreground)" }}>
        {results.length} {countLabels.of} {entries.length} {entries.length === 1 ? countLabels.entry : countLabels.entries}
      </Text>

      {results.length === 0 ? (
        <p className="rounded-xl border p-6 text-center text-sm" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
          {noResultsLabel}
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {results.map((r) => (
            <article
              key={r.slug}
              className="flex flex-col gap-3 rounded-xl border p-4 sm:flex-row"
              style={{ borderColor: "var(--border)" }}
            >
              {r.imageUrl && (
                <a href={r.url} className="block flex-shrink-0">
                  <img
                    src={r.imageUrl}
                    alt={r.title}
                    className="h-28 w-full rounded-lg object-cover sm:w-40"
                    loading="lazy"
                  />
                </a>
              )}
              <div className="flex flex-1 flex-col gap-1">
                <a href={r.url}>
                  <Title as="h3" className="!text-base !font-semibold hover:underline">
                    {r.title}
                  </Title>
                </a>
                <div className="flex items-center gap-2">
                  <Badge variant="flat" size="sm">{r.slot}</Badge>
                  <Text className="!text-xs" style={{ color: "var(--muted-foreground)" }}>
                    {r.date} · {r.reference} ({r.translation})
                  </Text>
                </div>
                {r.tags.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {r.tags.slice(0, 5).map((tag) => (
                      <a
                        key={tag}
                        href={`${tagPathPrefix}${encodeURIComponent(tag)}`}
                        className="rounded-full border px-2 py-0.5 text-[11px] hover:bg-(--muted)"
                        style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}
                      >
                        #{tag}
                      </a>
                    ))}
                  </div>
                )}
                {r.excerpt && (
                  <Text
                    className="!text-sm !mt-1 line-clamp-3"
                    style={{ color: "var(--foreground)" }}
                  >
                    {r.excerpt}
                  </Text>
                )}
                <a
                  href={r.url}
                  className="mt-2 inline-block text-sm font-medium hover:underline"
                  style={{ color: "var(--primary)" }}
                >
                  {viewLabel} →
                </a>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
