import { defineConfig, passthroughImageService } from "astro/config";
import react from "@astrojs/react";
import mdx from "@astrojs/mdx";
import tailwindcss from "@tailwindcss/vite";

const repoName = process.env.GITHUB_REPO_NAME ?? "daily_bread";
const owner = process.env.GITHUB_REPO_OWNER ?? "username";

export default defineConfig({
  site: `https://${owner}.github.io`,
  base: process.env.BASE_PATH ?? `/${repoName}`,
  image: {
    service: passthroughImageService(),
  },
  integrations: [react(), mdx()],
  vite: {
    plugins: [tailwindcss()],
  },
});
