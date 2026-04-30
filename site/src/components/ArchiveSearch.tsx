import { useEffect, useMemo, useState } from "react";
import { Input } from "rizzui/input";
import { Badge } from "rizzui/badge";
import { Title, Text } from "rizzui/typography";

interface IndexItem {
  slug: string;
  title: string;
  reference: string;
  translation: string;
  slot: string;
  date: string;
  snippet: string;
}

export default function ArchiveSearch() {
  const [items, setItems] = useState<IndexItem[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL.replace(/\/$/, "")}/search-index.json`)
      .then((r) => r.json())
      .then(setItems)
      .catch(() => setItems([]));
  }, []);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((i) =>
      [i.title, i.reference, i.snippet].some((s) => s.toLowerCase().includes(q)),
    );
  }, [items, query]);

  return (
    <div className="flex flex-col gap-4">
      <Input
        type="search"
        placeholder="Search title, passage, or text..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        clearable
        onClear={() => setQuery("")}
      />
      <Text className="!text-xs" style={{ color: "var(--muted-foreground)" }}>
        {results.length} of {items.length} {items.length === 1 ? "entry" : "entries"}
      </Text>
      <div className="flex flex-col gap-3">
        {results.map((r) => (
          <a
            key={r.slug}
            href={`${import.meta.env.BASE_URL.replace(/\/$/, "")}/${r.slug}`}
            className="block rounded-xl border p-4 transition-colors hover:bg-(--muted)"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="flex items-center gap-2">
              <Badge variant="flat" size="sm">
                {r.slot}
              </Badge>
              <Text className="!text-xs" style={{ color: "var(--muted-foreground)" }}>
                {r.date} · {r.reference} ({r.translation})
              </Text>
            </div>
            <Title as="h3" className="!text-base !font-semibold">
              {r.title}
            </Title>
            {r.snippet && (
              <Text
                className="!text-sm !mt-1 line-clamp-2"
                style={{ color: "var(--muted-foreground)" }}
              >
                {r.snippet}
              </Text>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
