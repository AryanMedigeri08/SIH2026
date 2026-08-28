import React from "react";
import { Languages } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export function LanguageSelector({ compact = false }) {
  const { language, setLanguage, languages, t } = useLanguage();
  return (
    <label className={`inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 ${compact ? "w-full" : ""}`} title={t("selectLanguage")}>
      <Languages className="h-3.5 w-3.5 shrink-0 text-sovereign-700" aria-hidden="true" />
      <span className="sr-only">{t("language")}</span>
      <select value={language} onChange={(event) => setLanguage(event.target.value)} className="min-w-0 bg-transparent font-semibold outline-none" aria-label={t("selectLanguage")}>
        {languages.map(({ code, label }) => <option key={code} value={code}>{label}</option>)}
      </select>
    </label>
  );
}
