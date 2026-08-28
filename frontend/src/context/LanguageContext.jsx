/**
 * LanguageContext.jsx — App-shell localization and enterprise report language.
 * The UI preference is intentionally separate from a saved enterprise's
 * language: changing navigation labels never mutates an already issued DPR.
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const LANGUAGE_STORAGE_KEY = "udyam_saathi_ui_language";

export const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी" },
  { code: "mr", label: "मराठी" },
  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" },
  { code: "kn", label: "ಕನ್ನಡ" },
];

const messages = {
  en: { dashboard: "Dashboard", overview: "Overview & Synthesis", viability: "ML Viability", market: "Market & Demand", schemes: "Government Schemes", financials: "Financials & Cash Flow", risk: "Risk Assessment", swot: "SWOT Analysis", dpr: "Bank DPR & Documents", calculator: "Loan Calculator", dataSources: "Data Sources", newEnterprise: "New Enterprise", logout: "Logout", login: "Login", register: "Register", language: "Language", yourEnterprises: "Your Enterprises", activeEnterprise: "Active Enterprise", createEnterprise: "Create & Analyze New Enterprise", createAccount: "Create Entrepreneur Account", signIn: "Sign In", backToDashboard: "Back to Dashboard", appraisalLanguage: "Credit Appraisal Language", selectLanguage: "Select language" },
  hi: { dashboard: "डैशबोर्ड", overview: "अवलोकन और सार", viability: "एमएल व्यवहार्यता", market: "बाज़ार और मांग", schemes: "सरकारी योजनाएँ", financials: "वित्त और नकदी प्रवाह", risk: "जोखिम मूल्यांकन", swot: "SWOT विश्लेषण", dpr: "बैंक डीपीआर और दस्तावेज़", calculator: "ऋण कैलकुलेटर", dataSources: "डेटा स्रोत", newEnterprise: "नया उद्यम", logout: "लॉग आउट", login: "लॉग इन", register: "पंजीकरण", language: "भाषा", yourEnterprises: "आपके उद्यम", activeEnterprise: "सक्रिय उद्यम", createEnterprise: "नया उद्यम बनाएँ और विश्लेषण करें", createAccount: "उद्यमी खाता बनाएँ", signIn: "लॉग इन", backToDashboard: "डैशबोर्ड पर वापस", appraisalLanguage: "क्रेडिट मूल्यांकन भाषा", selectLanguage: "भाषा चुनें" },
  mr: { dashboard: "डॅशबोर्ड", overview: "आढावा आणि सारांश", viability: "एमएल व्यवहार्यता", market: "बाजार आणि मागणी", schemes: "सरकारी योजना", financials: "आर्थिक व रोख प्रवाह", risk: "जोखीम मूल्यांकन", swot: "SWOT विश्लेषण", dpr: "बँक डीपीआर आणि दस्तऐवज", calculator: "कर्ज गणक", dataSources: "डेटा स्रोत", newEnterprise: "नवीन उद्योग", logout: "लॉग आउट", login: "लॉग इन", register: "नोंदणी", language: "भाषा", yourEnterprises: "तुमचे उद्योग", activeEnterprise: "सक्रिय उद्योग", createEnterprise: "नवीन उद्योग तयार करा व विश्लेषण करा", createAccount: "उद्योजक खाते तयार करा", signIn: "लॉग इन", backToDashboard: "डॅशबोर्डवर परत", appraisalLanguage: "पत मूल्यांकन भाषा", selectLanguage: "भाषा निवडा" },
  ta: { dashboard: "டாஷ்போர்டு", overview: "கண்ணோட்டம் மற்றும் சுருக்கம்", viability: "ML செயல்திறன்", market: "சந்தை மற்றும் தேவை", schemes: "அரசுத் திட்டங்கள்", financials: "நிதி மற்றும் பணப்புழக்கம்", risk: "இடர் மதிப்பீடு", swot: "SWOT பகுப்பாய்வு", dpr: "வங்கி DPR ஆவணங்கள்", calculator: "கடன் கணிப்பான்", dataSources: "தரவு ஆதாரங்கள்", newEnterprise: "புதிய நிறுவனம்", logout: "வெளியேறு", login: "உள்நுழை", register: "பதிவு", language: "மொழி", yourEnterprises: "உங்கள் நிறுவனங்கள்", activeEnterprise: "செயலில் உள்ள நிறுவனம்", createEnterprise: "புதிய நிறுவனத்தை உருவாக்கி பகுப்பாய்வு செய்க", createAccount: "தொழில்முனைவோர் கணக்கை உருவாக்கவும்", signIn: "உள்நுழை", backToDashboard: "டாஷ்போர்டுக்குத் திரும்பு", appraisalLanguage: "கடன் மதிப்பீட்டு மொழி", selectLanguage: "மொழியைத் தேர்ந்தெடுக்கவும்" },
  te: { dashboard: "డ్యాష్‌బోర్డ్", overview: "అవలోకనం మరియు సారాంశం", viability: "ML సాధ్యత", market: "మార్కెట్ మరియు డిమాండ్", schemes: "ప్రభుత్వ పథకాలు", financials: "ఆర్థికాలు మరియు నగదు ప్రవాహం", risk: "ప్రమాద అంచనా", swot: "SWOT విశ్లేషణ", dpr: "బ్యాంక్ DPR పత్రాలు", calculator: "రుణ కాలిక్యులేటర్", dataSources: "డేటా మూలాలు", newEnterprise: "కొత్త సంస్థ", logout: "లాగ్ అవుట్", login: "లాగ్ ఇన్", register: "నమోదు", language: "భాష", yourEnterprises: "మీ సంస్థలు", activeEnterprise: "క్రియాశీల సంస్థ", createEnterprise: "కొత్త సంస్థను సృష్టించి విశ్లేషించండి", createAccount: "వ్యవస్థాపక ఖాతాను సృష్టించండి", signIn: "లాగ్ ఇన్", backToDashboard: "డ్యాష్‌బోర్డ్‌కు తిరిగి", appraisalLanguage: "క్రెడిట్ మదింపు భాష", selectLanguage: "భాషను ఎంచుకోండి" },
  kn: { dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", overview: "ಅವಲೋಕನ ಮತ್ತು ಸಾರಾಂಶ", viability: "ML ಕಾರ್ಯಸಾಧ್ಯತೆ", market: "ಮಾರುಕಟ್ಟೆ ಮತ್ತು ಬೇಡಿಕೆ", schemes: "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು", financials: "ಹಣಕಾಸು ಮತ್ತು ನಗದು ಹರಿವು", risk: "ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ", swot: "SWOT ವಿಶ್ಲೇಷಣೆ", dpr: "ಬ್ಯಾಂಕ್ DPR ದಾಖಲೆಗಳು", calculator: "ಸಾಲದ ಕ್ಯಾಲ್ಕುಲೇಟರ್", dataSources: "ಡೇಟಾ ಮೂಲಗಳು", newEnterprise: "ಹೊಸ ಉದ್ಯಮ", logout: "ಲಾಗ್ ಔಟ್", login: "ಲಾಗ್ ಇನ್", register: "ನೋಂದಣಿ", language: "ಭಾಷೆ", yourEnterprises: "ನಿಮ್ಮ ಉದ್ಯಮಗಳು", activeEnterprise: "ಸಕ್ರಿಯ ಉದ್ಯಮ", createEnterprise: "ಹೊಸ ಉದ್ಯಮವನ್ನು ರಚಿಸಿ ಮತ್ತು ವಿಶ್ಲೇಷಿಸಿ", createAccount: "ಉದ್ಯಮಿ ಖಾತೆ ರಚಿಸಿ", signIn: "ಲಾಗ್ ಇನ್", backToDashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂತಿರುಗಿ", appraisalLanguage: "ಸಾಲ ಮೌಲ್ಯಮಾಪನ ಭಾಷೆ", selectLanguage: "ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ" },
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => localStorage.getItem(LANGUAGE_STORAGE_KEY) || "en");

  const setLanguage = useCallback((nextLanguage) => {
    const valid = LANGUAGES.some(({ code }) => code === nextLanguage) ? nextLanguage : "en";
    localStorage.setItem(LANGUAGE_STORAGE_KEY, valid);
    setLanguageState(valid);
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const value = useMemo(() => ({
    language,
    setLanguage,
    languages: LANGUAGES,
    t: (key) => messages[language]?.[key] || messages.en[key] || key,
  }), [language, setLanguage]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used within LanguageProvider");
  return context;
}
