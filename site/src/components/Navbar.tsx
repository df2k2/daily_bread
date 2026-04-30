import { Title } from "rizzui/typography";
import LanguageSwitcher from "./LanguageSwitcher";
import ThemeToggle from "./ThemeToggle";

interface Props {
  lang: "en" | "pt";
  basePath: string;
  archiveLabel: string;
  homeHref: string;
  archiveHref: string;
  siteTitle: string;
}

export default function Navbar({
  lang,
  basePath,
  archiveLabel,
  homeHref,
  archiveHref,
  siteTitle,
}: Props) {
  return (
    <header className="border-b" style={{ borderColor: "var(--border)" }}>
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-4">
        <a href={homeHref} className="flex items-center gap-2">
          <Title as="h1" className="!text-lg !font-semibold tracking-tight">
            {siteTitle}
          </Title>
        </a>
        <nav className="flex items-center gap-3 text-sm">
          <a href={archiveHref} className="hover:underline">
            {archiveLabel}
          </a>
          <LanguageSwitcher current={lang} basePath={basePath} />
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
