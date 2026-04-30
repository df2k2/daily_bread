import { getCollection } from "astro:content";

export async function GET() {
  const all = await getCollection("devotionals");
  const sorted = all.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
  const items = sorted.map((d) => {
    const body = d.body ?? "";
    const snippet = body
      .replace(/^---[\s\S]*?---/, "")
      .replace(/[#>*_`]/g, "")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 240);
    return {
      slug: d.id.replace(/\.md$/, ""),
      title: d.data.title,
      reference: d.data.reference,
      translation: d.data.translation,
      slot: d.data.slot,
      date: d.data.date.toISOString().slice(0, 10),
      snippet,
    };
  });
  return new Response(JSON.stringify(items), {
    headers: { "Content-Type": "application/json" },
  });
}
