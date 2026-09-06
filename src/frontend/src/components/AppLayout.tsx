import { NavLink, Outlet } from "react-router-dom";

import { ThemeSwitch } from "../theme/ThemeSwitch";
import { LanguageSelect } from "../i18n/LanguageSelect";
import { useLanguage } from "../i18n/useLanguage";

export function AppLayout() {
  const { t } = useLanguage();
  const navigation = [[t("timeline"), "/timeline"], [t("training"), "/training"], [t("mappings"), "/mappings"], [t("settings"), "/settings"]] as const;
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">{t("personalObservation")}</p>
          <span className="app-title">Polar Progress</span>
        </div>
        <LanguageSelect /><ThemeSwitch />
      </header>
      <nav aria-label={t("primaryNavigation")} className="primary-nav">
        {navigation.map(([label, path]) => (
          <NavLink key={path} to={path}>
            {label}
          </NavLink>
        ))}
      </nav>
      <main className="page-content">
        <Outlet />
      </main>
    </div>
  );
}
