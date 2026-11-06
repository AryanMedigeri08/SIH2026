// Short narration for routine introductions whose evidence is shown in the cards.
// Preserve actual follow-up answers and all financial/risk decisions verbatim.
const prompts = {
  en: { recommendations: 'Choose a business below. Tap to see details, or ask me for other ideas.', regional: 'This idea has some local challenges. See the reasons below. Would you like other ideas, or continue with these risks?' },
  hi: { recommendations: 'नीचे कोई व्यवसाय चुनिए। जानकारी देखने के लिए दबाइए, या मुझसे दूसरे विचार पूछिए।', regional: 'इस विचार के लिए यहाँ कुछ चुनौतियाँ हैं। कारण नीचे दिए हैं। दूसरे विचार देखें या इन जोखिमों के साथ आगे बढ़ें?' },
  mr: { recommendations: 'खालील व्यवसायांपैकी एक निवडा. माहिती पाहण्यासाठी दाबा किंवा इतर कल्पना विचारा.', regional: 'या व्यवसायासाठी येथे काही अडचणी आहेत. कारणे खाली दिली आहेत. इतर कल्पना पाहायच्या की हे धोके समजून पुढे जायचे?' },
  te: { recommendations: 'కింద ఒక వ్యాపారాన్ని ఎంచుకోండి. వివరాలు చూడండి లేదా వేరే ఆలోచనలు అడగండి.', regional: 'ఈ వ్యాపారానికి ఇక్కడ కొన్ని సవాళ్లు ఉన్నాయి. కారణాలు కింద ఉన్నాయి. వేరే ఆలోచనలు చూడాలా లేదా ఈ ప్రమాదాలతో కొనసాగాలా?' },
  ta: { recommendations: 'கீழே ஒரு தொழிலைத் தேர்ந்தெடுங்கள். விவரங்களைப் பாருங்கள் அல்லது வேறு யோசனைகளைக் கேளுங்கள்.', regional: 'இந்தத் தொழிலுக்கு இங்கு சில சவால்கள் உள்ளன. காரணங்கள் கீழே உள்ளன. வேறு யோசனைகளைப் பார்க்கலாமா அல்லது இந்த அபாயங்களுடன் தொடரலாமா?' },
  kn: { recommendations: 'ಕೆಳಗೆ ಒಂದು ವ್ಯಾಪಾರ ಆಯ್ಕೆಮಾಡಿ. ವಿವರಗಳನ್ನು ನೋಡಿ ಅಥವಾ ಬೇರೆ ಆಲೋಚನೆಗಳನ್ನು ಕೇಳಿ.', regional: 'ಈ ವ್ಯಾಪಾರಕ್ಕೆ ಇಲ್ಲಿ ಕೆಲವು ಸವಾಲುಗಳಿವೆ. ಕಾರಣಗಳು ಕೆಳಗಿವೆ. ಬೇರೆ ಆಲೋಚನೆಗಳನ್ನು ನೋಡಬೇಕೇ ಅಥವಾ ಈ ಅಪಾಯಗಳೊಂದಿಗೆ ಮುಂದುವರಿಯಬೇಕೇ?' },
};

export function readableChatPrompt(reply, state, language) {
  if (!reply || !state) return reply;
  const copy = prompts[language] || prompts.en;
  const last = state.history?.at(-1);
  const routine = !last || (last.role === 'assistant' && last.text === state.next?.text);
  if (state.next?.field === 'recommendations' && state.recommendations?.length && routine) return copy.recommendations;
  if (state.next?.field === 'regional_review' && last?.role === 'assistant' && last.text.startsWith('Regional check:')) return copy.regional;
  return reply;
}
