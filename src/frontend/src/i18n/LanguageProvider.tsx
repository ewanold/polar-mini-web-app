import { type PropsWithChildren, useEffect, useMemo, useState } from "react";

import { LanguageContext, type Language, type TranslationKey, type TranslationValues } from "./language-context";
import { de } from "./translations/de";
import { en } from "./translations/en";
import { ru } from "./translations/ru";

const all = { en, de, ru };
function initialLanguage(): Language { const saved = window.localStorage.getItem("polar-language"); if (saved === "en" || saved === "de" || saved === "ru") return saved; const browser = navigator.language.toLowerCase(); return browser.startsWith("de") ? "de" : browser.startsWith("ru") ? "ru" : "en"; }
export function LanguageProvider({ children }: PropsWithChildren) { const [language, setLanguage] = useState<Language>(initialLanguage); useEffect(() => { window.localStorage.setItem("polar-language", language); document.documentElement.lang = language; }, [language]); const value = useMemo(() => ({ language, setLanguage, t: (key: TranslationKey, values: TranslationValues = {}) => Object.entries(values).reduce((text, [name, replacement]) => text.replaceAll(`{${name}}`, String(replacement)), all[language][key]) }), [language]); return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>; }
