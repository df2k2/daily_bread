import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const devotionals = defineCollection({
  loader: glob({ pattern: "**/*-{en,pt}.md", base: "../content" }),
  schema: ({ image }) =>
    z.object({
      date: z.coerce.date(),
      datetime: z.coerce.date().optional(),
      slot: z.enum(["morning", "evening"]),
      lang: z.enum(["en", "pt"]),
      reference: z.string(),
      book: z.string().optional(),
      translation: z.string(),
      title: z.string(),
      tags: z.array(z.string()).default([]),
      excerpt: z.string().optional(),
      image: image().optional(),
      ai: z
        .object({
          text: z.string().optional(),
          image: z.string().optional(),
        })
        .optional(),
    }),
});

export const collections = { devotionals };
