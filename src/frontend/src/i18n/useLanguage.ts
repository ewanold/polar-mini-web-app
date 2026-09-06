import { useContext } from "react";

import { LanguageContext, type LanguageContextValue } from "./language-context";

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (context === null) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return context;
}
