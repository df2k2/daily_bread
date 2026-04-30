import { getDevotionalsFor, slugFromId } from "../../lib/i18n";

export async function GET() {
  const sorted = await getDevotionalsFor("pt");
  const items = sorted.map((d) => {
    const body = d.body ?? "";
    const snippet = body
      .replace(/^---[\s\S]*?---/, "")
      .replace(/```[\s\S]*?```/g, "")
      .replace(/[#>*_`]/g, "")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 240);
    return {
      slug: slugFromId(d.id),
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
