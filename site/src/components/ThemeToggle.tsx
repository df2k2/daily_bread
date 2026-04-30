import { useEffect, useState } from "react";
import { ActionIcon } from "rizzui/action-icon";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const current = (document.documentElement.getAttribute("data-theme") ?? "light") as
      | "light"
      | "dark";
    setTheme(current);
  }, []);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    setTheme(next);
  };

  return (
    <ActionIcon
      variant="text"
      size="sm"
      aria-label="Toggle theme"
      onClick={toggle}
      title={theme === "dark" ? "Switch to light" : "Switch to dark"}
    >
      <span aria-hidden>{theme === "dark" ? "☀" : "☾"}</span>
    </ActionIcon>
  );
}
