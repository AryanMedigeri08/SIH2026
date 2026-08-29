/**
 * TranslatedText.jsx — Drop-in React Component for Auto-Translating dynamic Groq / LLM and Report strings.
 */

import React from "react";
import { useAutoTranslate } from "../hooks/useAutoTranslate";

export function TranslatedText({ text, className = "", inline = false, as = "span" }) {
  const { translated, isTranslating } = useAutoTranslate(text);

  // Markdown bold parser
  const formatContent = (val) => {
    if (!val) return null;
    const parts = val.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i} className="font-bold">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const Component = as;

  return (
    <Component className={`${className} ${isTranslating ? "opacity-75 transition-opacity" : ""}`}>
      {formatContent(translated || text)}
    </Component>
  );
}

export default TranslatedText;
