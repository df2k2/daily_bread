import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const devotionals = defineCollection({
  loader: glob({ pattern: "**/*.{en,pt}.md", base: "../content" }),
  schema: () =>
    z.object({
      date: z.coerce.date(),
      slot: z.enum(["morning", "evening"]),
      lang: z.enum(["en", "pt"]),
      reference: z.string(),
      translation: z.string(),
      title: z.string(),
      image: z.string().optional(),
      ai: z
        .object({
          text: z.string().optional(),
          image: z.string().optional(),
        })
        .optional(),
    }),
});

export const collections = { devotionals };
