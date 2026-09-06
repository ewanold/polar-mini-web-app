import { useTheme } from "./useTheme";
import { useLanguage } from "../i18n/useLanguage";

export function ThemeSwitch() {
  const { theme, setTheme } = useTheme();
  const { t } = useLanguage();
  const nextTheme = theme === "light" ? "dark" : "light";

  return (
    <button
      className="theme-switch"
      type="button"
      aria-label={t(nextTheme === "dark" ? "switchToDarkTheme" : "switchToLightTheme")}
      onClick={() => setTheme(nextTheme)}
    >
      <span aria-hidden="true">{theme === "light" ? "☾" : "☀"}</span>
      <span>{t(theme === "light" ? "themeDark" : "themeLight")}</span>
    </button>
  );
}
