import { useEffect, useState } from "react";

interface Props {
  current: "en" | "pt";
  basePath: string;
}

const LABELS = {
  en: "EN",
  pt: "PT",
} as const;

const PRIMARY = "en";

function deriveSiblingPath(currentPath: string, basePath: string): {
  enPath: string;
  ptPath: string;
} {
  const baseNoTrail = basePath.replace(/\/$/, "");
  const stripped = currentPath.startsWith(baseNoTrail)
    ? currentPath.slice(baseNoTrail.length)
    : currentPath;
  const withoutPt = stripped.replace(/^\/pt(\/|$)/, "/");
  const enPath = `${baseNoTrail}${withoutPt || "/"}`;
  const ptPath = withoutPt === "/"
    ? `${baseNoTrail}/pt/`
    : `${baseNoTrail}/pt${withoutPt}`;
  return { enPath, ptPath };
}

export default function LanguageSwitcher({ current, basePath }: Props) {
  const [paths, setPaths] = useState<{ enPath: string; ptPath: string }>({
    enPath: basePath || "/",
    ptPath: `${basePath}/pt/`,
  });

  useEffect(() => {
    setPaths(deriveSiblingPath(window.location.pathname, basePath));
  }, [basePath]);

  return (
    <div className="inline-flex items-center gap-1 text-xs">
      {(["en", "pt"] as const).map((lang) => {
        const href = lang === "en" ? paths.enPath : paths.ptPath;
        const active = current === lang;
        return (
          <a
            key={lang}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`rounded px-2 py-1 font-medium transition-colors ${
              active
                ? "bg-(--muted) text-(--foreground)"
                : "text-(--muted-foreground) hover:text-(--foreground)"
            }`}
          >
            {LABELS[lang]}
          </a>
        );
      })}
    </div>
  );
}
