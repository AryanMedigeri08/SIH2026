/**
 * LanguageContext.jsx — Google Cloud Translation & Enterprise Multilingual Localization Agent.
 * Synchronizes navigation labels, reports, wizard inputs, and dynamic text synthesis across 10 Indian languages.
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState, useRef } from "react";
import { useAuth } from "./AuthContext";
import { translationApi } from "../services/api";

const LANGUAGE_STORAGE_KEY = "udyam_saathi_ui_language";
const TRANSLATION_CACHE_KEY = "udyam_saathi_dynamic_translation_cache_v2";

export const LANGUAGES = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
];

export const messages = {
  en: {
    dashboard: "Dashboard",
    overview: "Overview & Synthesis",
    viability: "ML Viability",
    market: "Market & Demand",
    schemes: "Government Schemes",
    financials: "Financials & Cash Flow",
    risk: "Risk Assessment",
    swot: "SWOT Analysis",
    dpr: "Bank DPR & Documents",
    calculator: "Loan Calculator",
    dataSources: "Data Sources",
    newEnterprise: "New Enterprise",
    logout: "Logout",
    login: "Login",
    register: "Register",
    language: "Language",
    yourEnterprises: "Your Enterprises",
    activeEnterprise: "Active Enterprise",
    createEnterprise: "Create & Analyze New Enterprise",
    createAccount: "Create Entrepreneur Account",
    signIn: "Sign In",
    backToDashboard: "Back to Dashboard",
    appraisalLanguage: "Credit Appraisal Language",
    selectLanguage: "Select language",
    projectCost: "Project Cost",
    marginCapital: "Available Margin Capital",
    subsidyAmount: "Applicable Subsidy",
    bankLoan: "Bank Loan Sizing",
    dscrRatio: "Debt Service Coverage Ratio (DSCR)",
    statusViable: "Statutorily & Financially Viable",
    verifiedDataSources: "Verified Ground-Truth Data Sources & Audit Lineage",
    sourcesConnected: "Sources Connected",
    hideLineage: "Hide Lineage",
    showLineage: "Show Lineage",
    totalCapitalOutlay: "Total Capital Outlay",
    capitalSubsidy: "Capital Subsidy",
    bankTermLoan: "Bank Term Loan",
    monthlyNetEmi: "Monthly Net EMI",
    annualTurnover: "Annual Turnover",
    debtCoverageDscr: "Debt Coverage (DSCR)",
    rbiBenchmarkMet: "RBI Benchmark Met",
    viewBankDpr: "View Official 7-Section Bank DPR",
    dedicatedModules: "Dedicated Appraisal Modules",
    exploreSection: "Explore Section",
    tier2Engine: "Tier 2 Supervised XGBoost Viability Engine (10-D)",
    viabilityVerdict: "Viability Verdict:",
    modelConfidence: "Model Confidence",
    classProbDistribution: "Class Probabilities Distribution:",
    primarySolvencyDriver: "Primary Solvency Driver:",
    primaryOperationalRisk: "Primary Operational Risk Factor:",
    executiveSynthesisTitle: "Executive Feasibility & Credit Appraisal Synthesis",
    strategicRecommendations: "Strategic Recommendations & Growth Milestones:",
    bankMemorandum: "Bank Credit Appraisal Memorandum:",
    fiveYearHorizon: "5-Year Financial Horizon & Capacity Ramp Schedule",
    fiveYearAmortization: "5-Year Amortization & Cash Flow",
    lineItem: "Line Item (₹)",
    turnoverGrossSales: "Turnover / Gross Sales",
    operatingExpenses: "Operating Expenses (Opex)",
    netEbitda: "Net EBITDA",
    taxDepreciation: "Tax Depreciation (15% WDV)",
    termLoanInterest: "Term Loan Interest (11%)",
    debtServiceEmi: "Debt Service (P+I EMI)",
    netCashSurplus: "Net Operating Cash Surplus (PAT)",
    dscrSolvencyRatio: "DSCR Solvency Ratio",
    strengths: "Strengths",
    weaknesses: "Weaknesses",
    opportunities: "Opportunities",
    threats: "Threats",
    promoterProfile: "Promoter Profile",
    marginCapitalSizing: "Margin Capital & Sizing",
    supplementaryContext: "Supplementary Context",
  },
  kn: {
    dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    overview: "ಅವಲೋಕನ ಮತ್ತು ಸಾರಾಂಶ",
    viability: "ML ಕಾರ್ಯಸಾಧ್ಯತೆ",
    market: "ಮಾರುಕಟ್ಟೆ ಮತ್ತು ಬೇಡಿಕೆ",
    schemes: "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು",
    financials: "ಹಣಕಾಸು ಮತ್ತು ನಗದು ಹರಿವು",
    risk: "ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ",
    swot: "SWOT ವಿಶ್ಲೇಷಣೆ",
    dpr: "ಬ್ಯಾಂಕ್ DPR ದಾಖಲೆಗಳು",
    calculator: "ಸಾಲದ ಕ್ಯಾಲ್ಕುಲೇಟರ್",
    dataSources: "ಡೇಟಾ ಮೂಲಗಳು",
    newEnterprise: "ಹೊಸ ಉದ್ಯಮ",
    logout: "ಲಾಗ್ ಔಟ್",
    login: "ಲಾಗ್ ಇನ್",
    register: "ನೋಂದಣಿ",
    language: "ಭಾಷೆ",
    yourEnterprises: "ನಿಮ್ಮ ಉದ್ಯಮಗಳು",
    activeEnterprise: "ಸಕ್ರಿಯ ಉದ್ಯಮ",
    createEnterprise: "ಹೊಸ ಉದ್ಯಮವನ್ನು ರಚಿಸಿ ಮತ್ತು ವಿಶ್ಲೇಷಿಸಿ",
    createAccount: "ಉದ್ಯಮಿ ಖಾತೆ ರಚಿಸಿ",
    signIn: "ಲಾಗ್ ಇನ್",
    backToDashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂತಿರುಗಿ",
    appraisalLanguage: "ಸಾಲ ಮೌಲ್ಯಮಾಪನ ಭಾಷೆ",
    selectLanguage: "ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
    projectCost: "ಯೋಜನಾ ವೆಚ್ಚ",
    marginCapital: "ಲಭ್ಯವಿರುವ ಮಾರ್ಜಿನ್ ಬಂಡವಾಳ",
    subsidyAmount: "ಅನ್ವಯವಾಗುವ ಸಬ್ಸಿಡಿ",
    bankLoan: "ಬ್ಯಾಂಕ್ ಸಾಲದ ಗಾತ್ರ",
    dscrRatio: "ಸಾಲ ಸೇವಾ ವ್ಯಾಪ್ತಿ ಅನುಪಾತ (DSCR)",
    statusViable: "ಶಾಸನಬದ್ಧವಾಗಿ ಮತ್ತು ಆರ್ಥಿಕವಾಗಿ ಕಾರ್ಯಸಾಧ್ಯ",
    verifiedDataSources: "ಪರಿಶೀಲಿಸಿದ ವಾಸ್ತವ ಡೇಟಾ ಮೂಲಗಳು ಮತ್ತು ಆಡಿಟ್ ವಿವರಗಳು",
    sourcesConnected: "ಮೂಲಗಳು ಸಂಪರ್ಕಗೊಂಡಿವೆ",
    hideLineage: "ವಿವರ ಮರೆಮಾಡಿ",
    showLineage: "ವಿವರ ತೋರಿಸಿ",
    totalCapitalOutlay: "ಒಟ್ಟು ಬಂಡವಾಳ ವೆಚ್ಚ",
    capitalSubsidy: "ಬಂಡವಾಳ ಸಬ್ಸಿಡಿ",
    bankTermLoan: "ಬ್ಯಾಂಕ್ ಅವಧಿ ಸಾಲ",
    monthlyNetEmi: "ಮಾಸಿಕ ನಿವ್ವಳ ಇಎಂಐ",
    annualTurnover: "ವಾರ್ಷಿಕ ವಹಿವಾಟು",
    debtCoverageDscr: "ಸಾಲ ವ್ಯಾಪ್ತಿ (DSCR)",
    rbiBenchmarkMet: "ಆರ್‌ಬಿಐ ಮಾನದಂಡ ಪೂರೈಸಲಾಗಿದೆ",
    viewBankDpr: "ಅಧಿಕೃತ 7-ವಿಭಾಗದ ಬ್ಯಾಂಕ್ DPR ವೀಕ್ಷಿಸಿ",
    dedicatedModules: "ಮೀಸಲಾದ ಮೌಲ್ಯಮಾಪನ ಮಾಡ್ಯೂಲ್‌ಗಳು",
    exploreSection: "ವಿಭಾಗವನ್ನು ಅನ್ವೇಷಿಸಿ",
    tier2Engine: "ಹಂತ 2 ಮೇಲ್ವಿಚಾರಣೆಯ XGBoost ಕಾರ್ಯಸಾಧ್ಯತಾ ಎಂಜಿನ್ (10-D)",
    viabilityVerdict: "ಕಾರ್ಯಸಾಧ್ಯತೆಯ ತೀರ್ಪು:",
    modelConfidence: "ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ",
    classProbDistribution: "ವರ್ಗ ಸಂಭವನೀಯತೆಗಳ ಹಂಚಿಕೆ:",
    primarySolvencyDriver: "ಮುಖ್ಯ ಸಾಲ ಮರುಪಾವತಿ ಪ್ರೇರಕ:",
    primaryOperationalRisk: "ಮುಖ್ಯ ಕಾರ್ಯಾಚರಣಾ ಅಪಾಯ ಅಂಶ:",
    executiveSynthesisTitle: "ಕಾರ್ಯನಿರ್ವಾಹಕ ಕಾರ್ಯಸಾಧ್ಯತೆ ಮತ್ತು ಕ್ರೆಡಿಟ್ ಮೌಲ್ಯಮಾಪನ ಸಾರಾಂಶ",
    strategicRecommendations: "ಕಾರ್ಯತಂತ್ರದ ಶಿಫಾರಸುಗಳು ಮತ್ತು ಬೆಳವಣಿಗೆಯ ಹಂತಗಳು:",
    bankMemorandum: "ಬ್ಯಾಂಕ್ ಸಾಲ ಮೌಲ್ಯಮಾಪನ ಜ್ಞಾಪಕ ಪತ್ರ:",
    fiveYearHorizon: "5-ವರ್ಷದ ಹಣಕಾಸು ಮುನ್ನೋಟ ಮತ್ತು ಸಾಮರ್ಥ್ಯ ವೇಳಾಪಟ್ಟಿ",
    fiveYearAmortization: "5-ವರ್ಷದ ಸಾಲ ಮರುಪಾವತಿ ಮತ್ತು ನಗದು ಹರಿವು",
    lineItem: "ವಿವರ ಐಟಂ (₹)",
    turnoverGrossSales: "ಒಟ್ಟು ಮಾರಾಟ / ವಹಿವಾಟು",
    operatingExpenses: "ಕಾರ್ಯಾಚರಣಾ ವೆಚ್ಚಗಳು (Opex)",
    netEbitda: "ನಿವ್ವಳ EBITDA",
    taxDepreciation: "ತೆರಿಗೆ ಸವಕಳಿ (15% WDV)",
    termLoanInterest: "ಅವಧಿ ಸಾಲದ ಬಡ್ಡಿ (11%)",
    debtServiceEmi: "ಸಾಲ ಸೇವೆ (P+I EMI)",
    netCashSurplus: "ನಿವ್ವಳ ನಗದು ಉಳಿತಾಯ (PAT)",
    dscrSolvencyRatio: "DSCR ಸಾಲ ಸೇವಾ ಅನುಪಾತ",
    strengths: "ಸಾಮರ್ಥ್ಯಗಳು",
    weaknesses: "ದೌರ್ಬಲ್ಯಗಳು",
    opportunities: "ಅವಕಾಶಗಳು",
    threats: "ಬೆದರಿಕೆಗಳು",
    promoterProfile: "ಪ್ರವರ್ತಕರ ವಿವರ",
    marginCapitalSizing: "ಮಾರ್ಜಿನ್ ಬಂಡವಾಳ ಮತ್ತು ಸಾಲ ಗಾತ್ರ",
    supplementaryContext: "ಪೂರಕ ವ್ಯವಹಾರ ಸಂದರ್ಭ",
  },
  hi: {
    dashboard: "डैशबोर्ड",
    overview: "अवलोकन और सार",
    viability: "एमएल व्यवहार्यता",
    market: "बाज़ार और मांग",
    schemes: "सरकारी योजनाएँ",
    financials: "वित्त और नकदी प्रवाह",
    risk: "जोखिम मूल्यांकन",
    swot: "SWOT विश्लेषण",
    dpr: "बैंक डीपीआर और दस्तावेज़",
    calculator: "ऋण कैलकुलेटर",
    dataSources: "डेटा स्रोत",
    newEnterprise: "नया उद्यम",
    logout: "लॉग आउट",
    login: "लॉग इन",
    register: "पंजीकरण",
    language: "भाषा",
    yourEnterprises: "आपके उद्यम",
    activeEnterprise: "सक्रिय उद्यम",
    createEnterprise: "नया उद्यम बनाएँ और विश्लेषण करें",
    createAccount: "उद्यमी खाता बनाएँ",
    signIn: "लॉग इन",
    backToDashboard: "डैशबोर्ड पर वापस",
    appraisalLanguage: "क्रेडिट मूल्यांकन भाषा",
    selectLanguage: "भाषा चुनें",
    projectCost: "परियोजना लागत",
    marginCapital: "उपलब्ध मार्जिन पूंजी",
    subsidyAmount: "लागू सब्सिडी",
    bankLoan: "बैंक ऋण आकार",
    dscrRatio: "ऋण सेवा कवरेज अनुपात (DSCR)",
    statusViable: "वैधानिक और वित्तीय रूप से व्यवहार्य",
    verifiedDataSources: "सत्यापित डेटा स्रोत और ऑडिट वंशावली",
    sourcesConnected: "स्रोत जुड़े हुए हैं",
    hideLineage: "विवरण छिपाएँ",
    showLineage: "विवरण दिखाएँ",
    totalCapitalOutlay: "कुल परियोजना पूंजी परिव्यय",
    capitalSubsidy: "पूंजीगत सब्सिडी",
    bankTermLoan: "बैंक मियादी ऋण",
    monthlyNetEmi: "मासिक शुद्ध ईएमआई",
    annualTurnover: "वार्षिक कारोबार",
    debtCoverageDscr: "ऋण सेवा कवरेज (DSCR)",
    rbiBenchmarkMet: "आरबीआई मानक पूरा हुआ",
    viewBankDpr: "आधिकारिक 7-खंडीय बैंक डीपीआर देखें",
    dedicatedModules: "समर्पित मूल्यांकन मॉड्यूल",
    exploreSection: "अनुभाग देखें",
    tier2Engine: "टियर 2 सुपरवाइज्ड XGBoost व्यवहार्यता इंजन (10-D)",
    viabilityVerdict: "व्यवहार्यता निर्णय:",
    modelConfidence: "मॉडल विश्वसनीयता",
    classProbDistribution: "वर्ग संभावना वितरण:",
    primarySolvencyDriver: "प्रमुख ऋण शोधन क्षमता कारक:",
    primaryOperationalRisk: "प्रमुख परिचालन जोखिम कारक:",
    executiveSynthesisTitle: "कार्यकारी व्यवहार्यता और क्रेडिट मूल्यांकन सार",
    strategicRecommendations: "रणनीतिक सिफारिशें और विकास मील के पत्थर:",
    bankMemorandum: "बैंक क्रेडिट मूल्यांकन ज्ञापन:",
    fiveYearHorizon: "5-वर्षीय वित्तीय क्षितिज और क्षमता अनुसूची",
    fiveYearAmortization: "5-वर्षीय ऋण परिशोधन और नकदी प्रवाह",
    lineItem: "मद विवरण (₹)",
    turnoverGrossSales: "सकल बिक्री / कारोबार",
    operatingExpenses: "परिचालन व्यय (Opex)",
    netEbitda: "शुद्ध EBITDA",
    taxDepreciation: "कर मूल्यह्रास (15% WDV)",
    termLoanInterest: "मियादी ऋण ब्याज (11%)",
    debtServiceEmi: "ऋण सेवा (P+I EMI)",
    netCashSurplus: "शुद्ध परिचालन नकदी अधिशेष (PAT)",
    dscrSolvencyRatio: "DSCR ऋण शोधन अनुपात",
    strengths: "ताकतें",
    weaknesses: "कमजोरियां",
    opportunities: "अवसर",
    threats: "चुनौतियां",
    promoterProfile: "प्रवर्तक प्रोफ़ाइल",
    marginCapitalSizing: "मार्जिन पूंजी और ऋण निर्धारण",
    supplementaryContext: "पूरक व्यावसायिक संदर्भ",
  },
  ta: {
    dashboard: "டாஷ்போர்டு",
    overview: "கண்ணோட்டம் மற்றும் சுருக்கம்",
    viability: "ML செயல்திறன்",
    market: "சந்தை மற்றும் தேவை",
    schemes: "அரசுத் திட்டங்கள்",
    financials: "நிதி மற்றும் பணப்புழக்கம்",
    risk: "இடர் மதிப்பீடு",
    swot: "SWOT பகுப்பாய்வு",
    dpr: "வங்கி DPR ஆவணங்கள்",
    calculator: "கடன் கணிப்பான்",
    dataSources: "தரவு ஆதாரங்கள்",
    newEnterprise: "புதிய நிறுவனம்",
    logout: "வெளியேறு",
    login: "உள்நுழை",
    register: "பதிவு",
    language: "மொழி",
    yourEnterprises: "உங்கள் நிறுவனங்கள்",
    activeEnterprise: "செயலில் உள்ள நிறுவனம்",
    createEnterprise: "புதிய நிறுவனத்தை உருவாக்கி பகுப்பாய்வு செய்க",
    createAccount: "தொழில்முனைவோர் கணக்கை உருவாக்கவும்",
    signIn: "உள்நுழை",
    backToDashboard: "டாஷ்போர்டுக்குத் திரும்பு",
    appraisalLanguage: "கடன் மதிப்பீட்டு மொழி",
    selectLanguage: "மொழியைத் தேர்ந்தெடுக்கவும்",
    projectCost: "திட்ட செலவு",
    marginCapital: "கிடைக்கக்கூடிய விளிம்பு மூலதனம்",
    subsidyAmount: "பொருந்தும் மானியம்",
    bankLoan: "வங்கி கடன் அளவு",
    dscrRatio: "கடன் சேவை பாதுகாப்பு விகிதம் (DSCR)",
    statusViable: "சட்டபூர்வமாகவும் நிதி ரீதியாகவும் சாத்தியமானது",
    verifiedDataSources: "சரிபார்க்கப்பட்ட தரவு ஆதாரங்கள் மற்றும் தணிக்கை விவரங்கள்",
    sourcesConnected: "ஆதாரங்கள் இணைக்கப்பட்டுள்ளன",
    hideLineage: "விவரங்களை மறை",
    showLineage: "விவரங்களைக் காட்டு",
    totalCapitalOutlay: "மொத்த திட்ட மூலதன செலவு",
    capitalSubsidy: "மூலதன மானியம்",
    bankTermLoan: "வங்கி தவணை கடன்",
    monthlyNetEmi: "மாதாந்திர EMI",
    annualTurnover: "வருடாந்திர வருவாய்",
    debtCoverageDscr: "கடன் சேவை பாதுகாப்பு (DSCR)",
    rbiBenchmarkMet: "ஆர்பிஐ தரம் பூர்த்தியானது",
    viewBankDpr: "அதிகாரப்பூர்வ 7-பிரிவு வங்கி DPR காண்க",
    dedicatedModules: "சிறப்பு மதிப்பீட்டு தொகுதிகள்",
    exploreSection: "பிரிவை ஆராய்க",
    tier2Engine: "நிலை 2 XGBoost சாத்தியக்கூறு இயந்திரம் (10-D)",
    viabilityVerdict: "சாத்தியக்கூறு முடிவு:",
    modelConfidence: "மாதிரி நம்பிக்கை",
    classProbDistribution: "சாத்தியக்கூறு விநியோகம்:",
    primarySolvencyDriver: "முக்கிய கடன் தீர்வு காரணி:",
    primaryOperationalRisk: "முக்கிய செயல்பாட்டு இடர் காரணி:",
    executiveSynthesisTitle: "செயல்முறை சாத்தியக்கூறு மற்றும் கடன் மதிப்பீட்டு சுருக்கம்",
    strategicRecommendations: "மூலோபாய பரிந்துரைகள் மற்றும் வளர்ச்சி மைல்கற்கள்:",
    bankMemorandum: "வங்கி கடன் மதிப்பீட்டுக் குறிப்பு:",
    fiveYearHorizon: "5-ஆண்டு நிதி கண்ணோட்டம் மற்றும் திறன் திட்டம்",
    fiveYearAmortization: "5-ஆண்டு கடன் தவணை மற்றும் பணப்புழக்கம்",
    lineItem: "பொருள் விவரம் (₹)",
    turnoverGrossSales: "மொத்த விற்பனை / வருவாய்",
    operatingExpenses: "செயல்பாட்டு செலவுகள் (Opex)",
    netEbitda: "நிகர EBITDA",
    taxDepreciation: "வரி தேய்மானம் (15% WDV)",
    termLoanInterest: "தவணை கடன் வட்டி (11%)",
    debtServiceEmi: "கடன் சேவை (P+I EMI)",
    netCashSurplus: "நிகர பண உபரி (PAT)",
    dscrSolvencyRatio: "DSCR கடன் பாதுகாப்பு விகிதம்",
    strengths: "பலங்கள்",
    weaknesses: "பலவீனங்கள்",
    opportunities: "வாய்ப்புகள்",
    threats: "அச்சுறுத்தல்கள்",
    promoterProfile: "முனைவோர் சுயவிவரம்",
    marginCapitalSizing: "விளிம்பு மூலதனம் & கடன் அளவு",
    supplementaryContext: "கூடுதல் வணிக சூழல்",
  },
  te: {
    dashboard: "డ్యాష్‌బోర్డ్",
    overview: "అవలోకనం మరియు సారాంశం",
    viability: "ML సాధ్యత",
    market: "మార్కెట్ మరియు డిమాండ్",
    schemes: "ప్రభుత్వ పథకాలు",
    financials: "ఆర్థికాలు మరియు నగదు ప్రవాహం",
    risk: "ప్రమాద అంచనా",
    swot: "SWOT విశ్లేషణ",
    dpr: "బ్యాంక్ DPR పత్రాలు",
    calculator: "రుణ కాలిక్యులేటర్",
    dataSources: "డేటా మూలాలు",
    newEnterprise: "కొత్త సంస్థ",
    logout: "లాగ్ అవుట్",
    login: "లాగ్ ఇన్",
    register: "నమోదు",
    language: "భాష",
    yourEnterprises: "మీ సంస్థలు",
    activeEnterprise: "క్రియాశీల సంస్థ",
    createEnterprise: "కొత్త సంస్థను సృష్టించి విశ్లేషించండి",
    createAccount: "వ్యవస్థాపక ఖాతాను సృష్టించండి",
    signIn: "లాగ్ ఇన్",
    backToDashboard: "డ్యాష్‌బోర్డ్‌కు తిరిగి",
    appraisalLanguage: "క్రెడిట్ మదింపు భాష",
    selectLanguage: "భాషను ఎంచుకోండి",
    projectCost: "ప్రాజెక్ట్ వ్యయం",
    marginCapital: "అందుబాటులో ఉన్న మార్జిన్ మూలధనం",
    subsidyAmount: "వర్తించే రాయితీ",
    bankLoan: "బ్యాంక్ రుణ పరిమాణం",
    dscrRatio: "రుణ సేవా కవరేజ్ నిష్పత్తి (DSCR)",
    statusViable: "చట్టబద్ధంగా మరియు ఆర్థికంగా సాధ్యమైనది",
    verifiedDataSources: "ధృవీకరించబడిన డేటా మూలాలు మరియు ఆడిట్ వివరాలు",
    sourcesConnected: "మూలాలు అనుసంధానించబడ్డాయి",
    hideLineage: "వివరాలు దాచు",
    showLineage: "వివరాలు చూపించు",
    totalCapitalOutlay: "మొత్తం ప్రాజెక్ట్ మూలధన వ్యయం",
    capitalSubsidy: "మూలధన రాయితీ",
    bankTermLoan: "బ్యాంక్ కాలపరిమితి రుణం",
    monthlyNetEmi: "నెలవారీ EMI",
    annualTurnover: "వార్షిక టర్నోవర్",
    debtCoverageDscr: "రుణ సేవా కవరేజ్ (DSCR)",
    rbiBenchmarkMet: "ఆర్బీఐ ప్రమాణాలు నెరవేరాయి",
    viewBankDpr: "అధికారిక 7-విభాగాల బ్యాంక్ DPR చూడండి",
    dedicatedModules: "ప్రత్యేక మదింపు మాడ్యూల్స్",
    exploreSection: "విభాగాన్ని అన్వేషించండి",
    tier2Engine: "టైర్ 2 పర్యవేక్షించబడే XGBoost ఇంజిన్ (10-D)",
    viabilityVerdict: "సాధ్యత నిర్ణయం:",
    modelConfidence: "మోడల్ విశ్వసనీయత",
    classProbDistribution: "సాధ్యత పంపిణీ:",
    primarySolvencyDriver: "ప్రధాన రుణ చెల్లింపు కారకం:",
    primaryOperationalRisk: "ప్రధాన కార్యాచరణ ప్రమాద కారకం:",
    executiveSynthesisTitle: "కార్యనిర్వాహక సాధ్యత మరియు క్రెడిట్ మదింపు సారాంశం",
    strategicRecommendations: "వ్యూహాత్మక సిఫార్సులు మరియు వృద్ధి మైలురాళ్ళు:",
    bankMemorandum: "బ్యాంక్ క్రెడిట్ మదింపు మెమోరాండం:",
    fiveYearHorizon: "5-సంవత్సరాల ఆర్థిక ప్రణాళిక మరియు సామర్థ్య షెడ్యూల్",
    fiveYearAmortization: "5-సంవత్సరాల రుణ చెల్లింపు మరియు నగదు ప్రవాహం",
    lineItem: "వివరాల అంశం (₹)",
    turnoverGrossSales: "స్థూల అమ్మకాలు / టర్నోవర్",
    operatingExpenses: "కార్యాచరణ ఖర్చులు (Opex)",
    netEbitda: "నికర EBITDA",
    taxDepreciation: "పన్ను తరుగుదల (15% WDV)",
    termLoanInterest: "కాలపరిమితి రుణ వడ్డీ (11%)",
    debtServiceEmi: "రుణ సేవ (P+I EMI)",
    netCashSurplus: "నికర నగదు మిగులు (PAT)",
    dscrSolvencyRatio: "DSCR రుణ రక్షణ నిష్పత్తి",
    strengths: "బలాలు",
    weaknesses: "బలహీనతలు",
    opportunities: "అవకాశాలు",
    threats: "ముప్పులు",
    promoterProfile: "వ్యవస్థాపక ప్రొఫైల్",
    marginCapitalSizing: "మార్జిన్ మూలధనం & రుణ పరిమాణం",
    supplementaryContext: "అదనపు వ్యాపార సందర్భం",
  },
  mr: {
    dashboard: "डॅशबोर्ड",
    overview: "आढावा आणि सारांश",
    viability: "एमएल व्यवहार्यता",
    market: "बाजार आणि मागणी",
    schemes: "सरकारी योजना",
    financials: "आर्थिक व रोख प्रवाह",
    risk: "जोखीम मूल्यांकन",
    swot: "SWOT विश्लेषण",
    dpr: "बँक डीपीआर आणि दस्तऐवज",
    calculator: "कर्ज गणक",
    dataSources: "डेटा स्रोत",
    newEnterprise: "नवीन उद्योग",
    logout: "लॉग आउट",
    login: "लॉग इन",
    register: "नोंदणी",
    language: "भाषा",
    yourEnterprises: "तुमचे उद्योग",
    activeEnterprise: "सक्रिय उद्योग",
    createEnterprise: "नवीन उद्योग तयार करा व विश्लेषण करा",
    createAccount: "उद्योजक खाते तयार करा",
    signIn: "लॉग इन",
    backToDashboard: "डॅशबोर्डवर परत",
    appraisalLanguage: "पत मूल्यांकन भाषा",
    selectLanguage: "भाषा निवडा",
    projectCost: "प्रकल्प खर्च",
    marginCapital: "उपलब्ध मार्जिन भांडवल",
    subsidyAmount: "लागू अनुदान",
    bankLoan: "बँक कर्ज आकार",
    dscrRatio: "कर्ज सेवा कव्हरेज प्रमाण (DSCR)",
    statusViable: "वैधानिक व आर्थिकदृष्ट्या व्यवहार्य",
    verifiedDataSources: "सत्यापित डेटा स्रोत आणि ऑडिट वंशावळ",
    sourcesConnected: "स्रोत जोडले आहेत",
    hideLineage: "तपशील लपवा",
    showLineage: "तपशील दाखवा",
    totalCapitalOutlay: "एकूण प्रकल्प भांडवली खर्च",
    capitalSubsidy: "भांडवली अनुदान",
    bankTermLoan: "बँक मुदत कर्ज",
    monthlyNetEmi: "मासिक निव्वळ ईएमआय",
    annualTurnover: "वार्षिक उलाढाल",
    debtCoverageDscr: "कर्ज सेवा कव्हरेज (DSCR)",
    rbiBenchmarkMet: "आरबीआय निकष पूर्ण",
    viewBankDpr: "अधिकृत 7-विभागीय बँक डीपीआर पहा",
    dedicatedModules: "समर्पित मूल्यांकन मॉड्यूल",
    exploreSection: "विभाग एक्सप्लोर करा",
    tier2Engine: "टियर 2 सुपरव्हाइज्ड XGBoost व्यवहार्यता इंजिन (10-D)",
    viabilityVerdict: "व्यवहार्यता निर्णय:",
    modelConfidence: "मॉडेल विश्वासार्हता",
    classProbDistribution: "वर्ग संभाव्यता वितरण:",
    primarySolvencyDriver: "प्रमुख कर्ज परतफेड चालक:",
    primaryOperationalRisk: "प्रमुख ऑपरेशनल जोखीम घटक:",
    executiveSynthesisTitle: "कार्यकारी व्यवहार्यता आणि क्रेडिट मूल्यांकन सारांश",
    strategicRecommendations: "धोरणात्मक शिफारसी आणि वाढीचे टप्पे:",
    bankMemorandum: "बँक क्रेडिट मूल्यांकन ज्ञापन:",
    fiveYearHorizon: "5-वर्षीय आर्थिक क्षितिज आणि क्षमता वेळापत्रक",
    fiveYearAmortization: "5-वर्षीय कर्ज परतफेड आणि रोख प्रवाह",
    lineItem: "तपशील बाब (₹)",
    turnoverGrossSales: "एकूण विक्री / उलाढाल",
    operatingExpenses: "ऑपरेटिंग खर्च (Opex)",
    netEbitda: "निव्वळ EBITDA",
    taxDepreciation: "कर घसारा (15% WDV)",
    termLoanInterest: "मुदत कर्ज व्याज (11%)",
    debtServiceEmi: "कर्ज सेवा (P+I EMI)",
    netCashSurplus: "निव्वळ रोख नफा (PAT)",
    dscrSolvencyRatio: "DSCR कर्ज कव्हरेज प्रमाण",
    strengths: "सामर्थ्य",
    weaknesses: "कमकुवतपणा",
    opportunities: "संधी",
    threats: "धोके",
    promoterProfile: "उद्योजक प्रोफाइल",
    marginCapitalSizing: "मार्जिन भांडवल आणि कर्ज आकार",
    supplementaryContext: "पूरक व्यावसायिक संदर्भ",
  },
  bn: {
    dashboard: "ড্যাশবোর্ড",
    overview: "সংক্ষিপ্ত বিবরণ ও সংশ্লেষণ",
    viability: "এমএল কার্যকারিতা",
    market: "বাজার ও চাহিদা",
    schemes: "সরকারি প্রকল্প",
    financials: "আর্থিক ও নগদ প্রবাহ",
    risk: "ঝুঁকি মূল্যায়ন",
    swot: "SWOT বিশ্লেষণ",
    dpr: "ব্যাঙ্ক ডিপিআর ও নথি",
    calculator: "ঋণ ক্যালকুলেটর",
    dataSources: "তথ্য উৎস",
    newEnterprise: "নতুন উদ্যোগ",
    logout: "লগ আউট",
    login: "লগ ইন",
    register: "নিবন্ধন",
    language: "ভাষা",
    yourEnterprises: "আপনার উদ্যোগসমূহ",
    activeEnterprise: "সক্রিয় উদ্যোগ",
    createEnterprise: "নতুন উদ্যোগ তৈরি ও বিশ্লেষণ করুন",
    createAccount: "উদ্যোক্তা অ্যাকাউন্ট তৈরি করুন",
    signIn: "সাইন ইন",
    backToDashboard: "ড্যাশবোর্ডে ফিরে যান",
    appraisalLanguage: "ক্রেডিট মূল্যায়ন ভাষা",
    selectLanguage: "ভাষা নির্বাচন করুন",
    projectCost: "প্রকল্প ব্যয়",
    marginCapital: "উপলব্ধ মার্জিন মূলধন",
    subsidyAmount: "প্রযোজ্য ভর্তুকি",
    bankLoan: "ব্যাঙ্ক ঋণের আকার",
    dscrRatio: "ঋণ সেবা কভারেজ অনুপাত (DSCR)",
    statusViable: "বিধিবদ্ধ ও আর্থিকভাবে কার্যকর",
    verifiedDataSources: "যাচাইকৃত তথ্য উৎস এবং অডিট বিশদ",
    sourcesConnected: "উৎস সংযুক্ত",
    hideLineage: "বিবরণ লুকান",
    showLineage: "বিবরণ দেখুন",
    totalCapitalOutlay: "মোট প্রকল্প মূলধন ব্যয়",
    capitalSubsidy: "মূলধন ভর্তুকি",
    bankTermLoan: "ব্যাঙ্ক মেয়াদী ঋণ",
    monthlyNetEmi: "মাসিক নিট ইএমআই",
    annualTurnover: "বার্ষিক লেনদেন",
    debtCoverageDscr: "ঋণ কভারেজ (DSCR)",
    rbiBenchmarkMet: "আরবিআই মানদণ্ড পূরণ হয়েছে",
    viewBankDpr: "অফিসিয়াল ৭-বিভাগীয় ব্যাঙ্ক ডিপিআর দেখুন",
    dedicatedModules: "মূল্যায়ন মডিউলসমূহ",
    exploreSection: "বিভাগ দেখুন",
    tier2Engine: "টায়ার ২ তত্ত্বাবধানযুক্ত XGBoost ইঞ্জিন (10-D)",
    viabilityVerdict: "কার্যকারিতা রায়:",
    modelConfidence: "মডেলের নির্ভরযোগ্যতা",
    classProbDistribution: "সম্ভাব্যতার বন্টন:",
    primarySolvencyDriver: "প্রধান ঋণ পরিশোধ চালক:",
    primaryOperationalRisk: "প্রধান অপারেশনাল ঝুঁকি ফ্যাক্টর:",
    executiveSynthesisTitle: "নির্বাহী কার্যকারিতা ও ক্রেডিট মূল্যায়ন সারসংক্ষেপ",
    strategicRecommendations: "কৌশলগত সুপারিশ এবং বৃদ্ধির মাইলফলক:",
    bankMemorandum: "ব্যাঙ্ক ক্রেডিট মূল্যায়ন স্মারকলিপি:",
    fiveYearHorizon: "৫-বছরের আর্থিক সম্ভাবনা এবং ক্ষমতা সময়সূচী",
    fiveYearAmortization: "৫-বছরের ঋণ পরিশোধ এবং নগদ প্রবাহ",
    lineItem: "আইটেম বিবরণ (₹)",
    turnoverGrossSales: "মোট বিক্রয় / টার্নওভার",
    operatingExpenses: "পরিচালন ব্যয় (Opex)",
    netEbitda: "নিট EBITDA",
    taxDepreciation: "কর অবচয় (15% WDV)",
    termLoanInterest: "মেয়াদী ঋণের সুদ (11%)",
    debtServiceEmi: "ঋণ সেবা (P+I EMI)",
    netCashSurplus: "নিট নগদ উদ্বৃত্ত (PAT)",
    dscrSolvencyRatio: "DSCR ঋণ কভারেজ অনুপাত",
    strengths: "শক্তি",
    weaknesses: "দুর্বলতা",
    opportunities: "সুযোগ",
    threats: "হুমকি",
    promoterProfile: "উদ্যোক্তা প্রোফাইল",
    marginCapitalSizing: "মার্জিন মূলধন ও ঋণের আকার",
    supplementaryContext: "সম্পূরক ব্যবসায়িক প্রসঙ্গ",
  },
  gu: {
    dashboard: "ડૅશબોર્ડ",
    overview: "ઝાંખી અને સંશ્લેષણ",
    viability: "ML વ્યવહાર્યતા",
    market: "બજાર અને માંગ",
    schemes: "સરકારી યોજનાઓ",
    financials: "નાણાકીય અને રોકડ પ્રવાહ",
    risk: "જોખમ મૂલ્યાંકન",
    swot: "SWOT વિશ્લેષણ",
    dpr: "બેંક ડીપીઆર અને દસ્તાવેજો",
    calculator: "લોન કેલ્ક્યુલેટર",
    dataSources: "ડેટા સ્ત્રોતો",
    newEnterprise: "નવો વ્યવસાય",
    logout: "લૉગ આઉટ",
    login: "લૉગ ઇન",
    register: "નોંધણી",
    language: "ભાષા",
    yourEnterprises: "તમારા વ્યવસાયો",
    activeEnterprise: "સક્રિય વ્યવસાય",
    createEnterprise: "નવો વ્યવસાય બનાવો અને વિશ્લેષણ કરો",
    createAccount: "ઉદ્યોગસાહસિક ખાતું બનાવો",
    signIn: "સાઇન ઇન",
    backToDashboard: "ડૅશબોર્ડ પર પાછા જાઓ",
    appraisalLanguage: "ક્રેડિટ મૂલ્યાંકન ભાષા",
    selectLanguage: "ભાષા પસંદ કરો",
    projectCost: "પ્રોજેક્ટ ખર્ચ",
    marginCapital: "ઉપલબ્ધ માર્જિન મૂડી",
    subsidyAmount: "લાગુ પડતી સબસિડી",
    bankLoan: "બેંક લોનનું કદ",
    dscrRatio: "ડેટ સર્વિસ કવરેજ રેશિયો (DSCR)",
    statusViable: "વૈધાનિક અને નાણાકીય રીતે વ્યવહારુ",
    verifiedDataSources: "ચકાસાયેલ ડેટા સ્ત્રોતો અને ઓડિટ વિગતો",
    sourcesConnected: "સ્ત્રોતો જોડાયેલા છે",
    hideLineage: "વિગતો છુપાવો",
    showLineage: "વિગતો બતાવો",
    totalCapitalOutlay: "કુલ પ્રોજેક્ટ મૂડી ખર્ચ",
    capitalSubsidy: "મૂડી સબસિડી",
    bankTermLoan: "બેંક મુદતી લોન",
    monthlyNetEmi: "માસિક ચોખ્ખી EMI",
    annualTurnover: "વાર્ષિક ટર્નઓવર",
    debtCoverageDscr: "ડેટ કવરેજ (DSCR)",
    rbiBenchmarkMet: "આરબીઆઈ માપદંડ પૂર્ણ",
    viewBankDpr: "સત્તાવાર 7-વિભાગીય બેંક DPR જુઓ",
    dedicatedModules: "સમર્પિત મૂલ્યાંકન મોડ્યુલ્સ",
    exploreSection: "વિભાગનું અન્વેષણ કરો",
    tier2Engine: "ટાયર 2 સુપરવાઇઝ્ડ XGBoost એન્જિન (10-D)",
    viabilityVerdict: "વ્યવહાર્યતા નિર્ણય:",
    modelConfidence: "મોડલ વિશ્વસનીયતા",
    classProbDistribution: "સંભાવના વિતરણ:",
    primarySolvencyDriver: "મુખ્ય લોન ચૂકવણી પરિબળ:",
    primaryOperationalRisk: "મુખ્ય કાર્યકારી જોખમ પરિબળ:",
    executiveSynthesisTitle: "કાર્યકારી વ્યવહાર્યતા અને ક્રેડિટ મૂલ્યાંકન સારાંશ",
    strategicRecommendations: "વ્યૂહાત્મક ભલામણો અને વૃદ્ધિના લક્ષ્યો:",
    bankMemorandum: "બેંક ક્રેડિટ મૂલ્યાંકન મેમોરેન્ડમ:",
    fiveYearHorizon: "5-વર્ષીય નાણાકીય ક્ષિતિજ અને ક્ષમતા શેડ્યૂલ",
    fiveYearAmortization: "5-વર્ષીય લોન ચુકવણી અને રોકડ પ્રવાહ",
    lineItem: "વિગત આઇટમ (₹)",
    turnoverGrossSales: "કુલ વેચાણ / ટર્નઓવર",
    operatingExpenses: "ઓપરેટિંગ ખર્ચ (Opex)",
    netEbitda: "ચોખ્ખું EBITDA",
    taxDepreciation: "ટેક્સ ઘસારો (15% WDV)",
    termLoanInterest: "મુદતી લોન વ્યાજ (11%)",
    debtServiceEmi: "લોન સેવા (P+I EMI)",
    netCashSurplus: "ચોખ્ખો રોકડ નફો (PAT)",
    dscrSolvencyRatio: "DSCR ડેટ કવરેજ રેશિયો",
    strengths: "શક્તિઓ",
    weaknesses: "નબળાઈઓ",
    opportunities: "તકો",
    threats: "જોખમો",
    promoterProfile: "ઉદ્યોગસાહસિક પ્રોફાઇલ",
    marginCapitalSizing: "માર્જિન મૂડી અને લોન કદ",
    supplementaryContext: "પૂરક વ્યવસાય સંદર્ભ",
  },
  ml: {
    dashboard: "ഡാഷ്‌ബോർഡ്",
    overview: "അവലോകനവും സംഗ്രഹവും",
    viability: "ML പ്രവർത്തനക്ഷമത",
    market: "വിപണിയും ആവശ്യകതയും",
    schemes: "സർക്കാർ പദ്ധതികൾ",
    financials: "സാമ്പത്തികവും പണമൊഴുക്കും",
    risk: "റിസ്ക് വിലയിരുത്തൽ",
    swot: "SWOT വിശകലനം",
    dpr: "ബാങ്ക് ഡിപിആറും രേഖകളും",
    calculator: "ലോൺ കാൽക്കുലേറ്റർ",
    dataSources: "ഡാറ്റ ഉറവിടങ്ങൾ",
    newEnterprise: "പുതിയ സംരംഭം",
    logout: "ലോഗ് ഔട്ട്",
    login: "ലോഗിൻ",
    register: "രജിസ്റ്റർ",
    language: "ഭാഷ",
    yourEnterprises: "നിങ്ങളുടെ സംരംഭങ്ങൾ",
    activeEnterprise: "സജീവ സംരംഭം",
    createEnterprise: "പുതിയ സംരംഭം സൃഷ്ടിച്ച് വിശകലനം ചെയ്യുക",
    createAccount: "സംരംഭക അക്കൗണ്ട് സൃഷ്ടിക്കുക",
    signIn: "സൈൻ ഇൻ",
    backToDashboard: "ഡാഷ്‌ബോർഡിലേക്ക് മടങ്ങുക",
    appraisalLanguage: "ക്രെഡിറ്റ് മൂല്യനിർണ്ണയ ഭാഷ",
    selectLanguage: "ഭാഷ തിരഞ്ഞെടുക്കുക",
    projectCost: "പദ്ധതി ചെലവ്",
    marginCapital: "ലഭ്യമായ മാർജിൻ മൂലധനം",
    subsidyAmount: "ബാധകമായ സബ്സിഡി",
    bankLoan: "ബാങ്ക് വായ്പ തുക",
    dscrRatio: "ഡെബ്റ്റ് സർവീസ് കവറേജ് അനുപാതം (DSCR)",
    statusViable: "നിയമപരമായും സാമ്പത്തികമായും ലാഭകരം",
    verifiedDataSources: "സ്ഥിരീകരിച്ച ഡാറ്റ ഉറവിടങ്ങളും ഓഡിറ്റ് വിശദാംശങ്ങളും",
    sourcesConnected: "ഉറവിടങ്ങൾ ബന്ധിപ്പിച്ചിരിക്കുന്നു",
    hideLineage: "വിശദാംശങ്ങൾ മറയ്ക്കുക",
    showLineage: "വിശദാംശങ്ങൾ കാണിക്കുക",
    totalCapitalOutlay: "മൊത്തം പദ്ധതി മൂലധനച്ചെലവ്",
    capitalSubsidy: "മൂലധന സബ്‌സിഡി",
    bankTermLoan: "ബാങ്ക് കാലാവധി വായ്പ",
    monthlyNetEmi: "പ്രതിമാസ EMI",
    annualTurnover: "വാർഷിക വരുമാനം",
    debtCoverageDscr: "വായ്പാ തിരിച്ചടവ് ശേഷി (DSCR)",
    rbiBenchmarkMet: "ആർബിഐ മാനദണ്ഡം പാലിച്ചു",
    viewBankDpr: "ഔദ്യോഗിക 7-വിഭാഗ ബാങ്ക് ഡിപിആർ കാണുക",
    dedicatedModules: "പ്രത്യേക മൂല്യനിർണ്ണയ മൊഡ്യൂളുകൾ",
    exploreSection: "വിഭാഗം കാണുക",
    tier2Engine: "ടയർ 2 മേൽനോട്ടത്തിലുള്ള XGBoost എഞ്ചിൻ (10-D)",
    viabilityVerdict: "പ്രവർത്തനക്ഷമത വിധി:",
    modelConfidence: "മോഡൽ വിശ്വാസ്യത",
    classProbDistribution: "സാധ്യതകളുടെ വിതരണം:",
    primarySolvencyDriver: "പ്രധാന വായ്പാ തിരിച്ചടവ് ഘടകം:",
    primaryOperationalRisk: "പ്രധാന പ്രവർത്തനപരമായ റിസ്ക് ഘടകം:",
    executiveSynthesisTitle: "എക്സിക്യൂട്ടീവ് പ്രവർത്തനക്ഷമതയും ക്രെഡിറ്റ് മൂല്യനിർണ്ണയ സംഗ്രഹവും",
    strategicRecommendations: "തന്ത്രപരമായ നിർദ്ദേശങ്ങളും വളർച്ചാ നാഴികക്കല്ലുകളും:",
    bankMemorandum: "ബാങ്ക് ക്രെഡിറ്റ് അപ്രൈസൽ മെമ്മോറാണ്ടം:",
    fiveYearHorizon: "5-വർഷത്തെ സാമ്പത്തിക കാഴ്ചപ്പാടും ശേഷി പദ്ധതിയും",
    fiveYearAmortization: "5-വർഷത്തെ വായ്പാ തിരിച്ചടവും പണമൊഴുക്കും",
    lineItem: "ഇനം വിശദാംശം (₹)",
    turnoverGrossSales: "മൊത്തം വിൽപ്പന / വിറ്റുവരവ്",
    operatingExpenses: "പ്രവർത്തനച്ചെലവുകൾ (Opex)",
    netEbitda: "അറ്റ EBITDA",
    taxDepreciation: "നികുതി തേയ്മാനം (15% WDV)",
    termLoanInterest: "കാലാവധി വായ്പാ പലിശ (11%)",
    debtServiceEmi: "വായ്പാ സേവനം (P+I EMI)",
    netCashSurplus: "അറ്റ പണ മിച്ചം (PAT)",
    dscrSolvencyRatio: "DSCR വായ്പാ കവറേജ് അനുപാതം",
    strengths: "കരുത്തുകൾ",
    weaknesses: "ബലഹീനതകൾ",
    opportunities: "അവസരങ്ങൾ",
    threats: "ഭീഷണികൾ",
    promoterProfile: "സംരംഭക പ്രൊഫൈൽ",
    marginCapitalSizing: "മാർജിൻ മൂലധനവും വായ്പാ തുകയും",
    supplementaryContext: "അധിക ബിസിനസ്സ് പശ്ചാത്തലം",
  },
  pa: {
    dashboard: "ਡੈਸ਼ਬੋਰਡ",
    overview: "ਸੰਖੇਪ ਜਾਣਕਾਰੀ ਅਤੇ ਸੰਸਲੇਸ਼ਣ",
    viability: "ML ਵਿਵਹਾਰਕਤਾ",
    market: "ਮਾਰਕੀਟ ਅਤੇ ਮੰਗ",
    schemes: "ਸਰਕਾਰੀ ਸਕੀਮਾਂ",
    financials: "ਵਿੱਤੀ ਅਤੇ ਨਕਦ ਪ੍ਰਵਾਹ",
    risk: "ਜੋਖਮ ਮੁਲਾਂਕਣ",
    swot: "SWOT ਵਿਸ਼ਲੇਸ਼ਣ",
    dpr: "ਬੈਂਕ ਡੀਪੀਆਰ ਅਤੇ ਦਸਤਾਵੇਜ਼",
    calculator: "ਕਰਜ਼ਾ ਕੈਲਕੁਲੇਟਰ",
    dataSources: "ਡਾਟਾ ਸਰੋਤ",
    newEnterprise: "ਨਵਾਂ ਉੱਦਮ",
    logout: "ਲਾਗ ਆਉਟ",
    login: "ਲਾਗ ਇਨ",
    register: "ਰਜਿਸਟਰ",
    language: "ਭਾਸ਼ਾ",
    yourEnterprises: "ਤੁਹਾਡੇ ਉੱਦਮ",
    activeEnterprise: "ਸਰਗਰਮ ਉੱਦਮ",
    createEnterprise: "ਨਵਾਂ ਉੱਦਮ ਬਣਾਓ ਅਤੇ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰੋ",
    createAccount: "ਉੱਦਮੀ ਖਾਤਾ ਬਣਾਓ",
    signIn: "ਸਾਈਨ ਇਨ",
    backToDashboard: "ਡੈਸ਼ਬੋਰਡ ਤੇ ਵਾਪਸ ਜਾਓ",
    appraisalLanguage: "ਕ੍ਰੈਡਿਟ ਮੁਲਾਂਕਣ ਭਾਸ਼ਾ",
    selectLanguage: "ਭਾਸ਼ਾ ਚੁਣੋ",
    projectCost: "ਪ੍ਰੋਜੈਕਟ ਲਾਗਤ",
    marginCapital: "ਉਪਲਬਧ ਮਾਰਜਿਨ ਪੂੰਜੀ",
    subsidyAmount: "ਲਾਗੂ ਸਬਸਿਡੀ",
    bankLoan: "ਬੈਂਕ ਕਰਜ਼ਾ ਆਕਾਰ",
    dscrRatio: "ਕਰਜ਼ਾ ਸੇਵਾ ਕਵਰੇਜ ਅਨੁਪਾਤ (DSCR)",
    statusViable: "ਕਾਨੂੰਨੀ ਅਤੇ ਵਿੱਤੀ ਤੌਰ 'ਤੇ ਵਿਵਹਾਰਕ",
    verifiedDataSources: "ਪ੍ਰਮਾਣਿਤ ਡਾਟਾ ਸਰੋਤ ਅਤੇ ਆਡਿਟ ਵੇਰਵੇ",
    sourcesConnected: "ਸਰੋਤ ਜੁੜੇ ਹੋਏ ਹਨ",
    hideLineage: "ਵੇਰਵੇ ਲੁਕਾਓ",
    showLineage: "ਵੇਰਵੇ ਦਿਖਾਓ",
    totalCapitalOutlay: "ਕੁੱਲ ਪ੍ਰੋਜੈਕਟ ਪੂੰਜੀ ਲਾਗਤ",
    capitalSubsidy: "ਪੂੰਜੀਗਤ ਸਬਸਿਡੀ",
    bankTermLoan: "ਬੈਂਕ ਮਿਆਦੀ ਕਰਜ਼ਾ",
    monthlyNetEmi: "ਮਾਸਿਕ ਸ਼ੁੱਧ EMI",
    annualTurnover: "ਸਾਲਾਨਾ ਟਰਨਓਵਰ",
    debtCoverageDscr: "ਕਰਜ਼ਾ ਕਵਰੇਜ (DSCR)",
    rbiBenchmarkMet: "ਆਰਬੀਆਈ ਮਾਪਦੰਡ ਪੂਰਾ ਹੋਇਆ",
    viewBankDpr: "ਅਧਿਕਾਰਤ 7-ਭਾਗ ਬੈਂਕ ਡੀਪੀਆਰ ਦੇਖੋ",
    dedicatedModules: "ਸਮਰਪਿਤ ਮੁਲਾਂਕਣ ਮੋਡੀਊਲ",
    exploreSection: "ਭਾਗ ਐਕਸਪਲੋਰ ਕਰੋ",
    tier2Engine: "ਟੀਅਰ 2 ਨਿਗਰਾਨੀ ਵਾਲਾ XGBoost ਇੰਜਣ (10-D)",
    viabilityVerdict: "ਵਿਵਹਾਰਕਤਾ ਫੈਸਲਾ:",
    modelConfidence: "ਮਾਡਲ ਭਰੋਸੇਯੋਗਤਾ",
    classProbDistribution: "ਸੰਭਾਵਨਾ ਵੰਡ:",
    primarySolvencyDriver: "ਮੁੱਖ ਕਰਜ਼ਾ ਅਦਾਇਗੀ ਕਾਰਕ:",
    primaryOperationalRisk: "ਮੁੱਖ ਕਾਰਜਸ਼ੀਲ ਜੋਖਮ ਕਾਰਕ:",
    executiveSynthesisTitle: "ਕਾਰਜਕਾਰੀ ਵਿਵਹਾਰਕਤਾ ਅਤੇ ਕ੍ਰੈਡਿਟ ਮੁਲਾਂਕਣ ਸੰਖੇਪ",
    strategicRecommendations: "ਰਣਨੀਤਕ ਸਿਫਾਰਸ਼ਾਂ ਅਤੇ ਵਿਕਾਸ ਮੀਲ ਪੱਥਰ:",
    bankMemorandum: "ਬੈਂਕ ਕ੍ਰੈਡਿਟ ਮੁਲਾਂਕਣ ਮੈਮੋਰੰਡਮ:",
    fiveYearHorizon: "5-ਸਾਲਾ ਵਿੱਤੀ ਦ੍ਰਿਸ਼ਟੀਕੋਣ ਅਤੇ ਸਮਰੱਥਾ ਸਮਾਂ-ਸਾਰਣੀ",
    fiveYearAmortization: "5-ਸਾਲਾ ਕਰਜ਼ਾ ਅਦਾਇਗੀ ਅਤੇ ਨਕਦ ਪ੍ਰਵਾਹ",
    lineItem: "ਵੇਰਵਾ ਆਈਟਮ (₹)",
    turnoverGrossSales: "ਕੁੱਲ ਵਿਕਰੀ / ਟਰਨਓਵਰ",
    operatingExpenses: "ਓਪਰੇਟਿੰਗ ਖਰਚੇ (Opex)",
    netEbitda: "ਸ਼ੁੱਧ EBITDA",
    taxDepreciation: "ਟੈਕਸ ਕਟੌਤੀ (15% WDV)",
    termLoanInterest: "ਮਿਆਦੀ ਕਰਜ਼ਾ ਵਿਆਜ (11%)",
    debtServiceEmi: "ਕਰਜ਼ਾ ਸੇਵਾ (P+I EMI)",
    netCashSurplus: "ਸ਼ੁੱਧ ਨਕਦ ਬੱਚਤ (PAT)",
    dscrSolvencyRatio: "DSCR ਕਰਜ਼ਾ ਕਵਰੇਜ ਅਨੁਪਾਤ",
    strengths: "ਤਾਕਤਾਂ",
    weaknesses: "ਕਮਜ਼ੋਰੀਆਂ",
    opportunities: "ਮੌਕੇ",
    threats: "ਖ਼ਤਰੇ",
    promoterProfile: "ਉੱਦਮੀ ਪ੍ਰੋਫਾਈਲ",
    marginCapitalSizing: "ਮਾਰਜਿਨ ਪੂੰਜੀ ਅਤੇ ਕਰਜ਼ਾ ਆਕਾਰ",
    supplementaryContext: "ਵਾਧੂ ਕਾਰੋਬਾਰੀ ਸੰਦਰਭ",
  },
};

// Fast reverse index matching English strings to translation keys
const PHRASE_KEY_MAP = {};
Object.entries(messages.en).forEach(([k, text]) => {
  if (typeof text === "string") {
    PHRASE_KEY_MAP[text.toLowerCase().trim()] = k;
  }
});

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => localStorage.getItem(LANGUAGE_STORAGE_KEY) || "en");
  const [dynamicCache, setDynamicCache] = useState(() => {
    try {
      const raw = localStorage.getItem(TRANSLATION_CACHE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  });

  const { isAuthenticated, userProfile, updateProfile } = useAuth();
  const cacheRef = useRef(dynamicCache);
  cacheRef.current = dynamicCache;

  const setLanguage = useCallback((nextLanguage) => {
    const valid = LANGUAGES.some(({ code }) => code === nextLanguage) ? nextLanguage : "en";
    localStorage.setItem(LANGUAGE_STORAGE_KEY, valid);
    setLanguageState(valid);
    
    if (isAuthenticated && userProfile?.firebase_uid && valid !== userProfile.preferred_language) {
      updateProfile({ preferred_language: valid }).catch((error) => {
        console.warn("Could not persist preferred language:", error);
      });
    }
  }, [isAuthenticated, updateProfile, userProfile?.firebase_uid, userProfile?.preferred_language]);

  useEffect(() => {
    const preferred = userProfile?.preferred_language;
    if (isAuthenticated && LANGUAGES.some(({ code }) => code === preferred) && preferred !== language) {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, preferred);
      setLanguageState(preferred);
    }
  }, [isAuthenticated, language, userProfile?.preferred_language]);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  /**
   * Fast synchronous static dictionary lookup for zero-latency UI rendering.
   */
  const lookupStatic = useCallback((text, targetLang = language) => {
    if (!text || typeof text !== "string") return null;
    if (targetLang === "en") return text;
    
    // Direct key lookup
    if (messages[targetLang]?.[text]) {
      return messages[targetLang][text];
    }

    // Phrase-to-key lookup
    const normalized = text.toLowerCase().trim();
    const key = PHRASE_KEY_MAP[normalized];
    if (key && messages[targetLang]?.[key]) {
      return messages[targetLang][key];
    }

    return null;
  }, [language]);

  /**
   * On-demand dynamic text translator powered by Google Cloud Translation Engine.
   */
  const translateText = useCallback(async (text, targetLang = language, sourceLang = "en") => {
    if (!text || typeof text !== "string" || !text.trim()) return text;
    if (targetLang === sourceLang) return text;

    // 1. Check static dictionary first
    const staticMatch = lookupStatic(text, targetLang);
    if (staticMatch) return staticMatch;

    // 2. Check local memory cache
    const cacheKey = `${sourceLang}:${targetLang}:${text.trim()}`;
    if (cacheRef.current[cacheKey]) {
      return cacheRef.current[cacheKey];
    }

    // 3. Query Google Cloud Translation API
    try {
      const res = await translationApi.translateText(text, targetLang, sourceLang);
      const translated = res?.translated_text || text;
      
      setDynamicCache((prev) => {
        const next = { ...prev, [cacheKey]: translated };
        try {
          localStorage.setItem(TRANSLATION_CACHE_KEY, JSON.stringify(next));
        } catch (_) {}
        return next;
      });
      return translated;
    } catch (e) {
      return text;
    }
  }, [language, lookupStatic]);

  /**
   * Batch text translator for reports and multi-line structures with local caching.
   */
  const translateBatch = useCallback(async (texts, targetLang = language, sourceLang = "en") => {
    if (!Array.isArray(texts) || texts.length === 0) return texts;
    if (targetLang === sourceLang) return texts;

    const uncachedIndices = [];
    const uncachedTexts = [];
    const results = new Array(texts.length);

    texts.forEach((txt, idx) => {
      if (typeof txt !== "string" || !txt.trim()) {
        results[idx] = txt;
        return;
      }
      
      // Check static dictionary
      const staticMatch = lookupStatic(txt, targetLang);
      if (staticMatch) {
        results[idx] = staticMatch;
        return;
      }

      // Check cache
      const cacheKey = `${sourceLang}:${targetLang}:${txt.trim()}`;
      if (cacheRef.current[cacheKey]) {
        results[idx] = cacheRef.current[cacheKey];
      } else {
        uncachedIndices.push(idx);
        uncachedTexts.push(txt);
      }
    });

    if (uncachedTexts.length === 0) {
      return results;
    }

    try {
      const res = await translationApi.translateBatch(uncachedTexts, targetLang, sourceLang);
      const newCacheEntries = {};

      res.forEach((r, i) => {
        const originalIdx = uncachedIndices[i];
        const translatedStr = r?.translated_text || uncachedTexts[i];
        results[originalIdx] = translatedStr;
        const cacheKey = `${sourceLang}:${targetLang}:${uncachedTexts[i].trim()}`;
        newCacheEntries[cacheKey] = translatedStr;
      });

      setDynamicCache((prev) => {
        const next = { ...prev, ...newCacheEntries };
        try {
          localStorage.setItem(TRANSLATION_CACHE_KEY, JSON.stringify(next));
        } catch (_) {}
        return next;
      });

      return results;
    } catch (e) {
      uncachedIndices.forEach((origIdx, i) => {
        results[origIdx] = uncachedTexts[i];
      });
      return results;
    }
  }, [language, lookupStatic]);

  const value = useMemo(() => ({
    language,
    setLanguage,
    languages: LANGUAGES,
    t: (key, fallback) => messages[language]?.[key] || lookupStatic(key, language) || messages.en[key] || fallback || key,
    lookupStatic,
    translateText,
    translateBatch,
  }), [language, setLanguage, lookupStatic, translateText, translateBatch]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used within LanguageProvider");
  return context;
}
