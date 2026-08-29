/**
 * useAutoTranslate.js — React Hook for Automatic Google Cloud Translation of dynamic Groq & Report text.
 */

import { useState, useEffect, useRef } from "react";
import { useLanguage } from "../context/LanguageContext";

export function useAutoTranslate(content) {
  const { language, translateText, translateBatch } = useLanguage();
  const [translated, setTranslated] = useState(content);
  const [isTranslating, setIsTranslating] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!content) {
      setTranslated(content);
      return;
    }

    if (language === "en") {
      setTranslated(content);
      return;
    }

    let isCancelled = false;
    setIsTranslating(true);

    const performTranslation = async () => {
      try {
        if (typeof content === "string") {
          const res = await translateText(content, language, "en");
          if (!isCancelled && mountedRef.current) {
            setTranslated(res);
          }
        } else if (Array.isArray(content)) {
          const stringItems = content.map((item) => (typeof item === "string" ? item : JSON.stringify(item)));
          const res = await translateBatch(stringItems, language, "en");
          if (!isCancelled && mountedRef.current) {
            setTranslated(res);
          }
        }
      } catch (err) {
        if (!isCancelled && mountedRef.current) {
          setTranslated(content);
        }
      } finally {
        if (!isCancelled && mountedRef.current) {
          setIsTranslating(false);
        }
      }
    };

    performTranslation();

    return () => {
      isCancelled = true;
    };
  }, [content, language, translateText, translateBatch]);

  return { translated, isTranslating, language };
}

export default useAutoTranslate;
