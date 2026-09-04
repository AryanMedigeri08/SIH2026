/**
 * useAutoTranslate.js — React Hook for Automatic Google Cloud Translation of dynamic Groq & Report text.
 */

import { useState, useEffect, useRef } from "react";
import { useLanguage } from "../context/LanguageContext";

export function useAutoTranslate(content) {
  const { language, lookupStatic, translateText, translateBatch, incrementPending, decrementPending } = useLanguage();
  
  const getInitialValue = () => {
    if (!content || language === "en") return content;
    if (typeof content === "string" && lookupStatic) {
      const match = lookupStatic(content, language);
      if (match) return match;
    }
    return content;
  };

  const [translated, setTranslated] = useState(getInitialValue);
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
      setIsTranslating(false);
      return;
    }

    if (language === "en") {
      setTranslated(content);
      setIsTranslating(false);
      return;
    }

    // Check synchronous static dictionary first for instant 0ms response
    if (typeof content === "string" && lookupStatic) {
      const staticMatch = lookupStatic(content, language);
      if (staticMatch) {
        setTranslated(staticMatch);
        setIsTranslating(false);
        return;
      }
    }

    let isCancelled = false;
    setIsTranslating(true);
    if (incrementPending) incrementPending();

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
        if (decrementPending) decrementPending();
      }
    };

    performTranslation();

    return () => {
      isCancelled = true;
    };
  }, [content, language, lookupStatic, translateText, translateBatch, incrementPending, decrementPending]);

  return { translated, isTranslating, language };
}

export default useAutoTranslate;
