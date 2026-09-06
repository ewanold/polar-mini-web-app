import { createContext } from "react";

import type { en } from "./translations/en";

export type Language = "en" | "de" | "ru";
export type TranslationKey = keyof typeof en;
export type TranslationValues = Record<string, string | number>;
export type Translate = (key: TranslationKey, values?: TranslationValues) => string;

export type LanguageContextValue = {
  language: Language;
  setLanguage: (value: Language) => void;
  t: Translate;
};

export const LanguageContext = createContext<LanguageContextValue | null>(null);
