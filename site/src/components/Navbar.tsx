import { Title } from "rizzui/typography";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  return (
    <header className="border-b" style={{ borderColor: "var(--border)" }}>
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
        <a href="/" className="flex items-center gap-2">
          <Title as="h1" className="!text-lg !font-semibold tracking-tight">
            Daily Bread
          </Title>
        </a>
        <nav className="flex items-center gap-4 text-sm">
          <a href="/archive" className="hover:underline">
            Archive
          </a>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
